"""Prueba: una respuesta larga arranca rapido y se dice ENTERA y en orden.

el usuario pidio la voz sin tope (19-ago-2026). Sin trocear, edge-tts genera el mp3
completo antes de la primera palabra: 3.640 caracteres tardaban 15 segundos en
arrancar. Ahora el texto se parte en pedazos que terminan en punto, y mientras
suena uno se va preparando el siguiente (medido: arranca en ~2s y los trozos
encadenan sin huecos).

Lo que vigila esta prueba:
  - el texto largo se parte y NO se pierde nada
  - los trozos suenan en orden, uno tras otro, sin encimarse
  - el siguiente se prepara MIENTRAS suena el actual (si no, vuelve la espera)

    python3 ~/.claude/hooks/tests/test_voz_largo.py
"""
import os, pathlib, sys, time

HOOKS = pathlib.Path(__file__).resolve().parent.parent
TESTS = HOOKS / "tests"
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, str(TESTS))

TMP = pathlib.Path(os.environ.get("VOZ_TEST_TMP", "/tmp"))
LOG = TMP / "voz-test-largo.txt"
os.environ["VOZ_TEST_LOG"] = str(LOG)

import comun
import voz_comun as voz
voz.REPRODUCIR = str(TESTS / "voz-reproducir.sh")
comun.blindar(voz)

TEXTO = ("Primer punto del reporte con su explicacion completa. "
         "Segundo punto que sigue al anterior sin cortarse. ") * 14   # ~1500


def main():
    voz.callar(); time.sleep(0.3)
    LOG.unlink(missing_ok=True)

    trozos = voz.trocear(TEXTO)
    fallos = []
    if len(trozos) < 2:
        fallos.append("no partio el texto largo")
    # nada se pierde: las palabras de los trozos son las del original
    if " ".join(trozos).split() != TEXTO.split():
        fallos.append("EL TROCEADO PIERDE O CAMBIA TEXTO")
    if not all(t.rstrip().endswith((".", "!", "?")) for t in trozos[:-1]):
        fallos.append("algun trozo no termina en final de oracion")

    voz.decir(TEXTO, 0, sid="largo-de-prueba")

    # mientras suena el primero, el segundo tiene que estar ya preparado
    preparado_a_tiempo = False
    fin = time.time() + 25
    while time.time() < fin:
        arch = os.listdir(voz.COLA)
        if any(a.endswith(".sonando") for a in arch) and any(a.endswith(".txt.mp3") for a in arch):
            preparado_a_tiempo = True
        if not arch:
            break
        time.sleep(0.2)
    if not preparado_a_tiempo:
        fallos.append("no fue preparando el siguiente: vuelve la espera larga")

    lineas = [l.strip() for l in LOG.read_text().splitlines()] if LOG.exists() else []
    inicios = [l for l in lineas if l.startswith("INICIO")]
    fines = [l for l in lineas if l.startswith("FIN")]
    print(f"trozos: {len(trozos)}   sonaron: {len(inicios)}   completos: {len(fines)}")

    if len(inicios) != len(trozos):
        fallos.append(f"sonaron {len(inicios)} trozos de {len(trozos)}")
    if len(fines) != len(inicios):
        fallos.append("algun trozo quedo a medias")
    abiertas = 0
    for l in lineas:
        abiertas += 1 if l.startswith("INICIO") else -1
        if abiertas > 1:
            fallos.append("dos trozos sonaron encimados")
            break

    voz.callar()
    if fallos:
        print("\nFALLA:")
        for f in fallos:
            print("  -", f)
        sys.exit(1)
    print("\nOK: se partio bien, sono entero, en orden y preparando el siguiente.")


main()
