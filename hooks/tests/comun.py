"""Guardas compartidas de las pruebas de voz.

Regla: una prueba JAMAS debe sonarle al usuario ni dejarle archivos de audio.
"""
import os, pathlib, sys

TESTS = pathlib.Path(__file__).resolve().parent


def blindar(voz):
    """Aborta si la prueba fuera a usar el reproductor de verdad."""
    if not str(voz.REPRODUCIR).startswith(str(TESTS)):
        sys.exit(f"ABORTO: la prueba iba a usar el reproductor REAL "
                 f"({voz.REPRODUCIR}) y le sonaria al usuario")


def sin_sonido(entorno=None):
    """Entorno con afplay y say falsos delante en el PATH: sirve para probar el
    reproductor DE VERDAD (y su limpieza de temporales) sin que suene."""
    e = dict(entorno or os.environ)
    e["PATH"] = f"{TESTS / 'bin'}:{e.get('PATH', '')}"
    return e


def restos_de_audio():
    """Archivos de voz tirados en el temporal del sistema."""
    tmp = pathlib.Path(os.environ.get("TMPDIR", "/tmp"))
    try:
        return sorted(p.name for p in tmp.glob("voz.*"))
    except Exception:
        return []


def aislar_sesiones(voz):
    """Aparta las ventanas que el usuario tenga prendidas y devuelve como restaurarlas.

    Sin esto, una prueba que cuenta ventanas con voz da resultados distintos
    segun si el esta oyendo alguna: paso justo eso el 19-ago-2026, cuando la
    prueba de "no digas el nombre habiendo una sola" fallo porque su propia
    ventana era la segunda.
    """
    import pathlib as _p
    d = _p.Path(voz.VOZ_ON_D)
    d.mkdir(parents=True, exist_ok=True)
    guardadas = {f.name: f.read_text() for f in d.iterdir() if f.is_file()}
    for f in d.iterdir():
        if f.is_file():
            f.unlink()

    def restaurar():
        for f in d.iterdir():
            if f.is_file():
                f.unlink()
        for n, txt in guardadas.items():
            (d / n).write_text(txt)
    return restaurar
