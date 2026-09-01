"""Prueba: al pedir silencio MIENTRAS se genera el mp3, no se habla igual.

callar.sh manda SIGTERM al grupo de procesos. Un `trap` que solo LIMPIA deja a
bash seguir el guion: si la senal llega mientras edge-tts esta generando, el
script sigue de largo, da el mp3 por fallido y cae al TTS del sistema — o sea
que Claude habla JUSTO DESPUES de que el usuario pidio silencio. La leccion es
de ago-19-2026 y vive en ~/.claude, pero esta copia portable nunca la recibio
porque el sync excluye voz-reproducir.sh a mano.

Corre el reproductor DE VERDAD: es lo unico que puede tener el defecto. El
doble de tests/voz-reproducir.sh no sirve para probar esto, igual que no servia
para probar `--solo-generar` (ver test_voz_no_encima.py).

    python3 ~/.claude/hooks/tests/test_voz_no_habla_tras_callar.py
"""
import os, pathlib, signal, subprocess, sys, time

HOOKS = pathlib.Path(__file__).resolve().parent.parent
REPRODUCTOR = str(HOOKS / "voz-reproducir.sh")   # el REAL: es lo que se prueba
TMP = pathlib.Path(os.environ.get("VOZ_TEST_TMP", "/tmp"))

# Falsos propios, en un directorio SIN ESPACIOS (~/.claude/hooks puede ser un
# enlace a un vault y la ruta resuelta traer espacios). Estos dejan rastro; los
# de tests/bin callan, y aqui hace falta saber si alguien hablo.
CAJA = TMP / "callar-bin"
CAJA.mkdir(parents=True, exist_ok=True)
LOG = TMP / "hablo.log"


def falso(nombre, cuerpo):
    f = CAJA / nombre
    f.write_text(cuerpo)
    f.chmod(0o755)
    return f


falso("say",    f'#!/bin/bash\necho "HABLO say $*" >> "{LOG}"\nsleep 1\n')
falso("afplay", f'#!/bin/bash\necho "HABLO afplay $*" >> "{LOG}"\nsleep 1\n')
# edge-tts falso y LENTO: asi la senal cae seguro durante la generacion, que es
# el unico momento en que aparece el defecto.
LENTO = falso("edge-lento", '#!/bin/bash\nsleep 5\n')


def main():
    LOG.unlink(missing_ok=True)
    txt = TMP / "texto-que-se-calla.txt"
    txt.write_text("Esta frase la interrumpe el usuario mientras se genera.")

    entorno = dict(os.environ)
    entorno["PATH"] = f"{CAJA}:{entorno.get('PATH', '')}"
    entorno["CC_EDGE_TTS"] = str(LENTO)
    entorno["CC_VOZ_CONF"] = str(TMP / "conf-que-no-existe")  # aislar del usuario
    entorno.pop("CC_REPRODUCTOR", None)

    p = subprocess.Popen(["bash", REPRODUCTOR, str(txt)], env=entorno,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)                       # ya esta generando
    p.send_signal(signal.SIGTERM)         # <- el usuario escribe: callar.sh
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
        print("FALLA: no murio con SIGTERM")
        sys.exit(1)
    time.sleep(2)                         # tiempo de sobra para que hablara

    fallos = []
    hablo = LOG.read_text().splitlines() if LOG.exists() else []
    if hablo:
        fallos.append(f"hablo despues de que le pidieron silencio: {hablo}")
    if txt.exists():
        fallos.append("no limpio el texto al morir: se reproduciria despues")

    LOG.unlink(missing_ok=True)
    txt.unlink(missing_ok=True)

    if fallos:
        print("FALLA:")
        for f in fallos:
            print("  -", f)
        sys.exit(1)
    print("OK: al pedir silencio durante la generacion, se calla y limpia.")


main()
