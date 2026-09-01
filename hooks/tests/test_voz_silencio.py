"""Prueba del apagón general (/silencio).

el usuario (19-ago-2026): "necesito un comando general que apague todas las voces
en todos lados". Tiene que hacer las cuatro cosas de una: apagar todas las
ventanas, cortar lo que suena, tirar la cola y no dejar reproductores sueltos.

No suena: el reproductor se sustituye por el doble de tests/.

    python3 ~/.claude/hooks/tests/test_voz_silencio.py
"""
import os, pathlib, subprocess, sys, time

HOOKS = pathlib.Path(__file__).resolve().parent.parent
TESTS = HOOKS / "tests"
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, str(TESTS))

TMP = pathlib.Path(os.environ.get("VOZ_TEST_TMP", "/tmp"))
LOG = TMP / "voz-test-silencio.txt"
os.environ["VOZ_TEST_LOG"] = str(LOG)
os.environ["CLAUDE_VOZ_REPRODUCTOR"] = str(TESTS / "voz-reproducir.sh")

import comun
import voz_comun as voz
comun.blindar(voz)

FALSAS = ["ffff0a01-silencio", "ffff0a02-silencio", "ffff0a03-silencio"]


def main():
    # se guarda lo que el usuario tenía prendido, para devolvérselo al final
    guardadas = {n: pathlib.Path(voz.VOZ_ON_D, n).read_text()
                 for n in voz.sesiones_con_voz()}
    LOG.unlink(missing_ok=True)
    pathlib.Path(voz.VOZ_ON_D).mkdir(parents=True, exist_ok=True)

    for s in FALSAS:
        pathlib.Path(voz.VOZ_ON_D, voz.marca_de(s)).write_text("ventana de prueba")

    voz.decir("Frase que se tiene que cortar a la mitad cuando pida silencio.", 300, sid=FALSAS[0])
    voz.decir("Y esta ni debe llegar a sonar.", 300, sid=FALSAS[1])
    time.sleep(1.0)                      # la primera ya suena, la otra espera

    antes = len(voz.sesiones_con_voz())
    salida = subprocess.run(["bash", str(HOOKS / "voz-silencio.sh")],
                            capture_output=True, text=True).stdout.strip()
    time.sleep(1.2)

    dichas = [l.strip() for l in LOG.read_text().splitlines()] if LOG.exists() else []
    quedan = voz.sesiones_con_voz()
    cola = os.listdir(voz.COLA) if os.path.isdir(voz.COLA) else []

    print("salida:", salida)
    print("rastro:", dichas or "(nada sono)")

    fallos = []
    if antes < 3:
        fallos.append("la prueba no logro montar las ventanas; no probo nada")
    if quedan:
        fallos.append(f"NO APAGO TODO: siguen prendidas {quedan}")
    if cola:
        fallos.append(f"no vacio la cola: {cola}")
    if not any(l.startswith("INICIO") for l in dichas):
        fallos.append("nunca empezo a hablar; la prueba no probo el corte")
    if any(l.startswith("FIN") for l in dichas):
        fallos.append("NO CORTO: la frase en curso llego hasta el final")
    if len([l for l in dichas if l.startswith("INICIO")]) > 1:
        fallos.append("la frase en cola sono igual: no se tiro la cola")
    if "SILENCIO" not in salida:
        fallos.append("no reporto el resultado en la linea de salida")

    # devolver al usuario lo que tenía
    for n, contenido in guardadas.items():
        pathlib.Path(voz.VOZ_ON_D, n).write_text(contenido)
    restaurado = sorted(voz.sesiones_con_voz()) == sorted(guardadas)
    if not restaurado:
        fallos.append("la prueba no devolvio las ventanas que estaban prendidas")

    if fallos:
        print("\nFALLA:")
        for f in fallos:
            print("  -", f)
        sys.exit(1)
    print("\nOK: apago todas, corto la frase en curso y vacio la cola.")


main()
