"""Prueba: `--solo-generar` PREPARA, no suena.

el usuario, ago-29-2026: "esta leyendo en voz alta 2 sesiones al mismo tiempo,
imposible entenderle". No eran dos sesiones: voz-runner.py precocina el trozo
siguiente llamando al reproductor con `--solo-generar`, y el reproductor REAL
ignoraba ese argumento — o sea que lo REPRODUCIA encima del que ya sonaba (y de
paso lo borraba de la cola). El doble de tests/voz-reproducir.sh si imitaba el
modo, asi que las cuatro pruebas pasaban con el defecto vivo.

Por eso esta prueba corre el reproductor DE VERDAD: el contrato entre el runner
y el reproductor solo se prueba contra el reproductor de verdad.

    python3 ~/.claude/hooks/tests/test_voz_no_encima.py
"""
import os, pathlib, shutil, subprocess, sys

HOOKS = pathlib.Path(__file__).resolve().parent.parent
TESTS = HOOKS / "tests"
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, str(TESTS))

import comun

TMP = pathlib.Path(os.environ.get("VOZ_TEST_TMP", "/tmp"))
REPRODUCTOR = str(HOOKS / "voz-reproducir.sh")   # el REAL: es lo que se prueba
LOG = TMP / "espia.log"

# El espia se copia a un directorio SIN ESPACIOS. ~/.claude/hooks es un enlace
# al vault ("Obsidian Vault"), y CC_REPRODUCTOR se parte en palabras para que
# pueda llevar banderas: desde la copia viva, la ruta del espia se partia, el
# reproductor fallaba callado y caia al `say` falso. La prueba fallaba por su
# propia ruta, no por el codigo.
ESPIA = TMP / "reproductor-espia.sh"
shutil.copy(TESTS / "bin" / "reproductor-espia.sh", ESPIA)
ESPIA.chmod(0o755)


def correr(txt_path, *args):
    entorno = comun.sin_sonido()
    entorno["CC_REPRODUCTOR"] = str(ESPIA)
    entorno["VOZ_TEST_LOG"] = str(LOG)
    subprocess.run(["bash", REPRODUCTOR, str(txt_path), *args],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                   timeout=120, env=entorno)
    return LOG.read_text().splitlines() if LOG.exists() else []


def main():
    fallos = []
    LOG.unlink(missing_ok=True)

    # 1. preparar: ni suena, ni se lleva el texto que sigue en la cola
    txt = TMP / "trozo-siguiente.txt"
    txt.write_text("Este trozo solo se prepara.")
    sono = correr(txt, "--solo-generar")
    if sono:
        fallos.append(f"`--solo-generar` REPRODUJO (dos voces encimadas): {sono}")
    if not txt.exists():
        fallos.append("`--solo-generar` borro el texto: se pierde de la cola")

    # El mp3 solo aparece si hay edge-tts y red; sin eso no es falla, es que no
    # se precocina nada. Lo de arriba, en cambio, se cumple siempre.
    listo = pathlib.Path(f"{txt}.mp3")
    precocinado = listo.exists() and listo.stat().st_size > 0

    # 2. modo normal: suena UNA vez y, si estaba precocinado, usa ESE mp3
    LOG.unlink(missing_ok=True)
    sono = correr(txt)
    if len(sono) != 1:
        fallos.append(f"el modo normal tenia que sonar una vez, sono {len(sono)}")
    elif precocinado and not sono[0].endswith(f"{txt.name}.mp3"):
        fallos.append(f"no aprovecho el mp3 precocinado, lo rehizo: {sono[0]}")
    if txt.exists():
        fallos.append("el modo normal no borro el texto")
    if listo.exists():
        fallos.append("quedo tirado el mp3 precocinado")

    LOG.unlink(missing_ok=True)
    txt.unlink(missing_ok=True)
    listo.unlink(missing_ok=True)

    if fallos:
        print("FALLA:")
        for f in fallos:
            print("  -", f)
        sys.exit(1)
    print("OK: preparar no suena, y el mp3 precocinado se aprovecha.")


main()
