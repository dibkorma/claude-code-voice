"""Prueba: una frase que ya empezo a sonar NUNCA se corta a la mitad.

el usuario, ago-2026: "si comienzas a decirme algo, siempre tienes que terminar lo
que me estabas diciendo". Antes, decir() mataba la voz en curso para arrancar la
nueva, asi que el aviso de otra sesion se comia la frase que el estaba oyendo.

No suena audio: el reproductor se sustituye por el doble de tests/, que anota
INICIO y FIN. Una frase cortada se ve como un INICIO sin su FIN; dos frases
encimadas se ven como dos INICIO seguidos.

    python3 ~/.claude/hooks/tests/test_voz_no_corta.py
"""
import os, pathlib, sys, time

HOOKS = pathlib.Path(__file__).resolve().parent.parent
TESTS = HOOKS / "tests"
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, str(TESTS))

TMP = pathlib.Path(os.environ.get("VOZ_TEST_TMP", "/tmp"))
LOG = TMP / "voz-test-log.txt"
os.environ["VOZ_TEST_LOG"] = str(LOG)

import voz_comun as voz
voz.REPRODUCIR = str(TESTS / "voz-reproducir.sh")   # el doble, no el real
import comun; comun.blindar(voz)

A = "Primera frase: el status que el usuario esta oyendo ahora mismo."
B = "Segunda frase: el aviso de la otra sesion que acaba de terminar."


def limpiar_estado():
    LOG.unlink(missing_ok=True)
    pathlib.Path(voz.PIDF).unlink(missing_ok=True)
    for atributo in ("COLA",):
        d = getattr(voz, atributo, None)
        if d:
            for f in pathlib.Path(d).glob("*"):
                f.unlink()


def rastro():
    try:
        return [l.strip() for l in LOG.read_text().splitlines() if l.strip()]
    except FileNotFoundError:
        return []


def etiqueta(linea):
    """'INICIO Primera frase: ...' -> 'Primera frase: ...'"""
    return linea.split(" ", 1)[1] if " " in linea else ""


def revisar(lineas):
    fallos = []
    inicios = [l for l in lineas if l.startswith("INICIO")]
    fines = [l for l in lineas if l.startswith("FIN")]

    if len(inicios) != 2:
        fallos.append(f"esperaba que hablara 2 veces, hablo {len(inicios)}")
    if len(fines) != len(inicios):
        fallos.append(f"FRASE CORTADA: empezaron {len(inicios)} y solo terminaron {len(fines)}")

    # el corazon de la prueba: nunca dos INICIO sin un FIN en medio
    abiertas = 0
    for l in lineas:
        abiertas += 1 if l.startswith("INICIO") else -1
        if abiertas > 1:
            fallos.append("SE ENCIMARON: empezo una frase sin que terminara la anterior")
            break

    # y ademas en orden: primero la que ya estaba sonando
    if len(lineas) >= 2 and etiqueta(lineas[0]) != etiqueta(lineas[1]):
        fallos.append("la primera frase no fue la primera en terminar")
    return fallos


def main():
    limpiar_estado()

    voz.decir(A, 400)          # 1. arranca el status que el usuario esta oyendo
    time.sleep(0.8)            #    ya suena
    voz.decir(B, 400)          # 2. otra sesion quiere hablar encima
    time.sleep(7)              # 3. dejar que todo termine

    lineas = rastro()
    print("--- rastro ---")
    for l in lineas:
        print("   ", l)

    fallos = revisar(lineas)
    if fallos:
        print("\nFALLA:")
        for f in fallos:
            print("  -", f)
        sys.exit(1)
    print("\nOK: las dos frases sonaron completas, en orden y sin encimarse.")


main()
