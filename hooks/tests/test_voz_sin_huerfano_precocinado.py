"""Prueba: si falla el reproductor, el mp3 precocinado tampoco queda tirado.

El modo normal aprovecha "$TXT.mp3" si el runner ya lo dejo listo. Cuando ese
mp3 no se puede sonar (reproductor roto, archivo corrupto, salida ocupada) el
guion sigue de largo al respaldo — y el precocinado se quedaba en el temporal
para siempre, porque limpiar() solo conocia el mp3 que genera EL MISMO. Es la
misma fuga que dejo 30 archivos tirados en ago-19-2026, por otra puerta.

    python3 ~/.claude/hooks/tests/test_voz_sin_huerfano_precocinado.py
"""
import os, pathlib, subprocess, sys

HOOKS = pathlib.Path(__file__).resolve().parent.parent
REPRODUCTOR = str(HOOKS / "voz-reproducir.sh")   # el REAL: es lo que se prueba
TMP = pathlib.Path(os.environ.get("VOZ_TEST_TMP", "/tmp"))

CAJA = TMP / "huerfano-bin"            # sin espacios: CC_REPRODUCTOR se parte
CAJA.mkdir(parents=True, exist_ok=True)


def falso(nombre, cuerpo):
    f = CAJA / nombre
    f.write_text(cuerpo); f.chmod(0o755)
    return f


ROTO = falso("rep-roto", "#!/bin/bash\nexit 1\n")     # no puede sonar nada
falso("say", "#!/bin/bash\nsleep 0.2\n")              # respaldo mudo
VACIO = falso("edge-vacio", '#!/bin/bash\n: > "${!#}" 2>/dev/null\n')


def main():
    txt = TMP / "con-precocinado.txt"
    listo = pathlib.Path(f"{txt}.mp3")
    txt.write_text("Ya venia preparado.")
    listo.write_text("mp3 que el runner dejo listo")

    entorno = dict(os.environ)
    entorno["PATH"] = f"{CAJA}:{entorno.get('PATH', '')}"
    entorno["CC_REPRODUCTOR"] = str(ROTO)
    entorno["CC_EDGE_TTS"] = str(VACIO)
    entorno["CC_VOZ_CONF"] = str(TMP / "conf-que-no-existe")
    subprocess.run(["bash", REPRODUCTOR, str(txt)], env=entorno, timeout=60,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    fallos = []
    if listo.exists():
        fallos.append(f"quedo tirado el mp3 precocinado: {listo}")
    if txt.exists():
        fallos.append("quedo tirado el texto")

    listo.unlink(missing_ok=True); txt.unlink(missing_ok=True)
    if fallos:
        print("FALLA:")
        for f in fallos:
            print("  -", f)
        sys.exit(1)
    print("OK: no queda huerfano aunque el reproductor falle.")


main()
