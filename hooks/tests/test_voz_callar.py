"""Prueba: cuando el usuario escribe, la voz SI se corta y la cola se tira.

Es la otra mitad de test_voz_no_corta.py. Ahora que decir() ya no interrumpe a
nadie, callar() quedo como el UNICO que puede cortar una frase — si esto se
rompe, Claude le sigue hablando encima mientras el escribe.

    python3 ~/.claude/hooks/tests/test_voz_callar.py
"""
import os, pathlib, sys, time

HOOKS = pathlib.Path(__file__).resolve().parent.parent
TESTS = HOOKS / "tests"
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, str(TESTS))

TMP = pathlib.Path(os.environ.get("VOZ_TEST_TMP", "/tmp"))
LOG = TMP / "voz-test-callar.txt"
os.environ["VOZ_TEST_LOG"] = str(LOG)

import voz_comun as voz
voz.REPRODUCIR = str(TESTS / "voz-reproducir.sh")
import comun; comun.blindar(voz)


def main():
    LOG.unlink(missing_ok=True)
    voz.callar()                      # partir de limpio
    time.sleep(0.3)
    LOG.unlink(missing_ok=True)

    voz.decir("Frase larga que el usuario va a interrumpir escribiendo.", 400)
    voz.decir("Y esta otra ni deberia llegar a sonar.", 400)
    time.sleep(0.9)                   # la primera ya suena, la segunda espera

    voz.callar()                      # <- el usuario escribe
    time.sleep(3)                     # tiempo de sobra para que sonaran ambas

    lineas = [l.strip() for l in LOG.read_text().splitlines() if l.strip()] \
        if LOG.exists() else []
    quedan = sorted(os.listdir(voz.COLA)) if os.path.isdir(voz.COLA) else []

    print("--- rastro ---")
    for l in lineas:
        print("   ", l)
    print("--- cola despues de callar:", quedan or "vacia")

    fallos = []
    if not any(l.startswith("INICIO") for l in lineas):
        fallos.append("nunca empezo a hablar; la prueba no probo nada")
    if any(l.startswith("FIN") for l in lineas):
        fallos.append("NO SE CORTO: la frase llego hasta el final pese al callar()")
    if len([l for l in lineas if l.startswith("INICIO")]) > 1:
        fallos.append("la segunda frase sono igual: la cola no se tiro")
    if quedan:
        fallos.append(f"quedaron archivos en la cola: {quedan}")

    if fallos:
        print("\nFALLA:")
        for f in fallos:
            print("  -", f)
        sys.exit(1)
    print("\nOK: callar() corto la frase en curso y vacio la cola.")


main()
