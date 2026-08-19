"""Atiende la cola de voz: reproduce los textos UNO POR UNO, en orden, y nunca
corta al que ya empezo a sonar.

Existe por una peticion del usuario (ago-2026): "si comienzas a decirme algo,
siempre tienes que terminar lo que me estabas diciendo". Antes, cada voz nueva
mataba a la anterior, asi que el aviso de otra sesion se comia el status que el
estaba oyendo a la mitad.

Lo lanza voz_comun.decir() despues de encolar. Si ya hay un runner atendiendo la
cola, el nuevo se muere de una: el que manda es el lock, no el ultimo que llego.
"""
import fcntl, os, pathlib, subprocess, sys, time

HOME = pathlib.Path.home()
COLA = HOME / ".claude" / ".voz-cola"
LOCK = HOME / ".claude" / ".voz-runner.lock"
PIDF = HOME / ".claude" / ".voz.pid"
REPRODUCIR = os.environ.get(
    "CLAUDE_VOZ_REPRODUCTOR", str(HOME / ".claude" / "hooks" / "voz-reproducir.sh"))

# Un texto que lleva mas de esto esperando ya no vale la pena: el usuario seguiria
# oyendo el status de hace media hora. Se descarta callado.
CADUCIDAD = int(os.environ.get("CLAUDE_VOZ_CADUCIDAD", "300"))


def pendientes():
    """Lo que espera turno. El que SUENA no esta aqui: se renombra a .sonando
    justo antes de reproducirlo, para que el tope de la cola no lo toque."""
    return sorted(COLA.glob("*.txt"))


def entorno_de(txt):
    """Cada texto puede traer su propia voz/velocidad en un archivo hermano."""
    entorno = dict(os.environ)
    extra = txt.with_suffix(".voz")
    try:
        for linea in extra.read_text().splitlines():
            if "=" in linea:
                k, v = linea.split("=", 1)
                entorno[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return entorno, extra


def preparar(txt, entorno):
    """Deja el mp3 del SIGUIENTE trozo listo mientras suena el actual.

    Es lo que hace usable el modo sin tope: edge-tts tarda ~15s en un texto
    largo, y esa espera se la come el trozo que ya esta sonando."""
    if txt is None or txt.with_suffix(".txt.mp3").exists():
        return
    try:
        subprocess.Popen(["bash", REPRODUCIR, str(txt), "--solo-generar"],
                         stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         env=entorno)
    except Exception:
        pass


def reproducir(txt, siguiente=None):
    entorno, extra = entorno_de(txt)
    sonando = txt.with_suffix(".txt.sonando")
    listo = txt.with_suffix(".txt.mp3")
    try:
        txt.rename(sonando)
        # el mp3 preparado viaja con su texto, o el reproductor no lo encuentra
        if listo.exists():
            listo.rename(sonando.with_name(sonando.name + ".mp3"))
    except OSError:
        return                      # se lo llevo un callar(): nada que hacer
    preparar(siguiente, entorno)    # el de despues se va cocinando ya
    try:
        subprocess.run(["bash", REPRODUCIR, str(sonando)],
                       stdin=subprocess.DEVNULL,
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       env=entorno)
    finally:
        # el reproductor ya lo borra en su trap; esto cubre el caso de que
        # muera de una forma que no lo dispare
        for f in (sonando, extra, sonando.with_name(sonando.name + ".mp3")):
            try:
                f.unlink()
            except OSError:
                pass


def main():
    COLA.mkdir(parents=True, exist_ok=True)
    lock = open(LOCK, "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return          # ya hay runner; el tomara lo que acabo de encolar

    PIDF.write_text(str(os.getpid()))

    while True:
        cola = pendientes()
        if not cola:
            # Soltar y re-mirar: alguien pudo encolar justo entre el listado y
            # el break, y su runner se habria muerto contra este mismo lock.
            fcntl.flock(lock, fcntl.LOCK_UN)
            time.sleep(0.15)
            if not pendientes():
                return
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                return  # otro runner agarro el relevo: mejor aun
            continue

        txt = cola[0]
        try:
            viejo = time.time() - txt.stat().st_mtime > CADUCIDAD
        except OSError:
            continue
        if viejo:
            try:
                txt.unlink()
            except OSError:
                pass
            continue
        reproducir(txt, cola[1] if len(cola) > 1 else None)


main()
