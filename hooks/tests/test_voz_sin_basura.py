"""Prueba: hablar no deja NI UN archivo de audio tirado.

el usuario, ago-19-2026: "que no vaya a quedar ningun tipo de voice note, que feo".
Y no era paranoia: `mktemp -t voz` crea el archivo y el script le pegaba ".mp3"
al nombre, asi que cada frase dejaba un huerfano. Habia 30 cuando se encontro.

Aqui corre el reproductor DE VERDAD (edge-tts incluido) pero con afplay y say
falsos, para probar la limpieza sin que suene nada.

    python3 ~/.claude/hooks/tests/test_voz_sin_basura.py
"""
import os, pathlib, subprocess, sys, time

HOOKS = pathlib.Path(__file__).resolve().parent.parent
TESTS = HOOKS / "tests"
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, str(TESTS))

import comun
import voz_comun as voz

TMP = pathlib.Path(os.environ.get("VOZ_TEST_TMP", "/tmp"))
REPRODUCTOR = str(HOOKS / "voz-reproducir.sh")   # el REAL: es lo que se prueba


def hablar_de_verdad(texto, matar_a_los=None):
    """Corre el reproductor real (sin sonido) y devuelve si sobrevivio entero."""
    ruta = TMP / "frase-de-prueba.txt"
    ruta.write_text(texto)
    p = subprocess.Popen(["bash", REPRODUCTOR, str(ruta)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True, env=comun.sin_sonido())
    if matar_a_los:
        time.sleep(matar_a_los)
        try:
            os.killpg(p.pid, 15)      # asi corta callar() de verdad
        except OSError:
            pass
    p.wait(timeout=120)
    time.sleep(0.5)
    return ruta.exists()


def main():
    fallos = []
    previos = comun.restos_de_audio()
    if previos:
        print(f"aviso: ya habia {len(previos)} restos de antes; se ignoran")

    # 1. camino normal
    quedo_txt = hablar_de_verdad("Prueba de limpieza.")
    nuevos = [n for n in comun.restos_de_audio() if n not in previos]
    if nuevos:
        fallos.append(f"hablando normal quedaron restos: {nuevos}")
    if quedo_txt:
        fallos.append("el texto de la frase no se borro")

    # 2. cortado a la mitad, que es cuando se escapaba
    quedo_txt = hablar_de_verdad("Frase larga. " * 30, matar_a_los=2.5)
    nuevos = [n for n in comun.restos_de_audio() if n not in previos]
    if nuevos:
        fallos.append(f"al cortarlo a la mitad quedaron restos: {nuevos}")
    if quedo_txt:
        fallos.append("al cortarlo, el texto de la frase quedo tirado")

    # 3. la cola tampoco acumula
    if [n for n in os.listdir(voz.COLA)] if os.path.isdir(voz.COLA) else []:
        fallos.append("quedaron archivos en la cola de voz")

    if fallos:
        print("FALLA:")
        for f in fallos:
            print("  -", f)
        sys.exit(1)
    print("OK: ni un archivo de audio tirado, ni hablando entero ni cortado.")


main()
