"""Piezas compartidas de la voz de Claude: limpiar texto, encolarlo y decirlo.

Dos reglas que el usuario pidio expresamente (ago-2026) y que este archivo hace
cumplir:

  1. Lo que ya empezo a sonar NUNCA se corta. decir() encola; el que reproduce
     es voz-runner.py, uno por uno. Cortar es cosa de callar().
  2. La voz se prende POR SESION, no para toda la maquina. Cada ventana decide
     si habla o no (ver hablar.py y voz-toggle.sh). "no que todas me esten
     hablando porque se convierte en un problema".

Lo usan:
  - hablar.py  (hook Stop)        -> tope corto, solo el titular de la respuesta
  - decir.py   (/donde-estamos)   -> tope largo, el resumen entero
  - callar.sh  (UserPromptSubmit) -> corta lo de SU sesion cuando el escribe
"""
import os, re, signal, subprocess, sys, time

HOME = os.path.expanduser("~")
PIDF = os.path.join(HOME, ".claude", ".voz.pid")
REPRODUCIR = os.environ.get(
    "CLAUDE_VOZ_REPRODUCTOR",
    os.path.join(HOME, ".claude", "hooks", "voz-reproducir.sh"))
RUNNER = os.path.join(HOME, ".claude", "hooks", "voz-runner.py")
COLA = os.path.join(HOME, ".claude", ".voz-cola")
TMPDIR = COLA          # nombre viejo, misma carpeta

# Carpeta de interruptores: un archivo por sesion que quiere oir voz.
VOZ_ON_D = os.path.join(HOME, ".claude", "voz-on.d")

# Cuantos textos pueden ESPERAR turno. Lo que suena no cuenta. Si se pasa, se
# botan los mas viejos: la idea es no cortar la frase en curso, no leerle un
# monologo de avisos rancios.
COLA_MAX = int(os.environ.get("CLAUDE_VOZ_COLA_MAX", "3"))

VOZ_POR_DEFECTO = os.environ.get("CLAUDE_VOZ", "Paulina")
VEL_POR_DEFECTO = os.environ.get("CLAUDE_VOZ_VEL", "190")


def sesion_actual():
    """El id de la sesion donde corre esto. Lo pone Claude Code en el entorno;
    de respaldo, la ultima donde el usuario escribio (la anota callar.sh)."""
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID", "").strip()
    if sid:
        return sid
    try:
        with open(os.path.join(HOME, ".claude", ".voz-sesion-activa")) as f:
            return f.read().strip()
    except Exception:
        return ""


def marca_de(sid):
    """Trozo de id que va en el nombre de los archivos de la cola, para saber
    de que sesion es cada frase sin abrir nada."""
    return (sid or "").replace("/", "")[:8] or "anonima"


def habla_esta_sesion(sid):
    """True si ESA sesion tiene la voz prendida. Sin archivo, sin voz."""
    if not sid:
        return False
    return os.path.exists(os.path.join(VOZ_ON_D, marca_de(sid)))


def etiqueta_de(sid):
    """Como se llama esa ventana, para que el usuario sepa QUIEN le esta hablando.

    Lo escribe /hablar (el nombre que el le puso, o la carpeta de trabajo). Si
    no hay nada, el trozo del id — feo, pero mejor que una voz anonima."""
    try:
        with open(os.path.join(VOZ_ON_D, marca_de(sid))) as f:
            nombre = f.read().strip()
        if nombre:
            return nombre
    except Exception:
        pass
    return marca_de(sid)


def sesiones_con_voz():
    try:
        return sorted(os.listdir(VOZ_ON_D))
    except Exception:
        return []


def limpiar(texto):
    """Deja solo lo que vale la pena oir: nada de codigo, rutas, URLs,
    tablas, markdown ni emojis. Leer una ruta en voz alta es tortura."""
    t = texto
    t = re.sub(r"```.*?```", " ", t, flags=re.S)          # bloques de codigo
    t = re.sub(r"~~~.*?~~~", " ", t, flags=re.S)

    # codigo inline: si es una palabra corta (say, /voice, tap) se lee;
    # si es un comando o una ruta se bota, para no dejar la frase coja.
    def _inline(m):
        x = m.group(1).strip()
        return " " + x + " " if (len(x) <= 20 and re.fullmatch(r"[/@]?[\w.\-]+", x)) else " "
    t = re.sub(r"`([^`]*)`", _inline, t)

    t = re.sub(r"^\s*\|.*$", " ", t, flags=re.M)          # filas de tabla
    t = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", t)      # links -> solo el texto
    t = re.sub(r"https?://\S+", " ", t)                   # URLs sueltas
    t = re.sub(r"(?<![\w])[~./][\w.\-]*/[\w./\-]+", " ", t)  # rutas de archivo
    t = re.sub(r"^\s{0,3}#{1,6}\s+", "", t, flags=re.M)   # titulos
    t = re.sub(r"^\s*[-*+]\s+", "", t, flags=re.M)        # vinetas
    t = re.sub(r"^\s*\d+\.\s+", "", t, flags=re.M)        # listas numeradas
    t = re.sub(r"^\s*>+\s*", "", t, flags=re.M)           # citas
    t = re.sub(r"^\s*[-–—_*]{3,}\s*$", " ", t, flags=re.M)  # separadores
    t = re.sub(r"[*_]{1,3}", "", t)                       # negritas / cursivas
    # fuera emojis y simbolos; se conserva el latino acentuado y la puntuacion
    t = "".join(ch for ch in t if ch in "\n\t" or (ch.isprintable() and ord(ch) < 0x2190))
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\s+([.,;:!?…])", r"\1", t)               # sin espacio antes del punto
    t = re.sub(r"\n{2,}", "\n", t)
    return t.strip()


def recortar(t, maximo):
    """Corta en el final de una oracion, nunca a mitad de palabra."""
    if len(t) <= maximo:
        return t
    cut = t[:maximo]
    idx = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "),
              cut.rfind(".\n"), cut.rfind("\n"))
    if idx > 80:
        cut = cut[:idx + 1]
    return cut.rstrip()


def _matar(pid):
    """Mata el reproductor y todo lo que colgo de el (edge-tts, afplay, say).

    Se verifica por la LINEA DE COMANDO completa, no por el nombre del proceso:
    el hijo directo es `python3 voz-runner.py` o `bash voz-reproducir.sh`, y hay
    mil de esos en la Mac. Los PID se reciclan, asi que sin esta comprobacion se
    podria matar cualquier cosa."""
    try:
        cmd = subprocess.run(["ps", "-p", str(pid), "-o", "command="],
                             capture_output=True, text=True, timeout=3).stdout.strip()
    except Exception:
        return
    if not cmd:
        return
    es_nuestro = ("voz-reproducir.sh" in cmd or "voz-runner.py" in cmd
                  or cmd.startswith("say ") or "/say " in cmd)
    if not es_nuestro:
        return
    try:
        # se lanzo con start_new_session -> el pid ES el lider del grupo, asi
        # que esto se lleva tambien al edge-tts o al afplay que tenga adentro
        os.killpg(pid, signal.SIGTERM)
    except Exception:
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass


def _archivos_cola():
    try:
        return sorted(os.listdir(COLA))
    except Exception:
        return []


def _es_de(nombre, marca):
    return f"-{marca}-" in nombre


def callar(sid=None):
    """Corta la voz y tira lo que quedaba por decir.

    Con `sid`, solo toca lo de ESA sesion: si el usuario escribe en una ventana, no
    tiene por que callarse la ventana de al lado que le esta contando otra cosa.
    Sin `sid` (o sea, a mano), se calla todo.

    Es lo UNICO que interrumpe una frase: decir() ya no corta a nadie, encola.
    """
    marca = marca_de(sid) if sid else None
    archivos = _archivos_cola()

    # Mirar QUE esta sonando antes de borrar nada, o se pierde de quien era.
    sonando = [n for n in archivos if n.endswith(".sonando")]
    hay_que_matar = marca is None or any(_es_de(n, marca) for n in sonando)

    for n in archivos:
        if marca and not _es_de(n, marca):
            continue          # de otra sesion: ni se toca
        try:
            os.remove(os.path.join(COLA, n))
        except OSError:
            pass

    if not hay_que_matar:
        return

    try:
        with open(PIDF) as f:
            _matar(int(f.read().strip()))
    except Exception:
        pass

    # Al matar al runner se quedo sin quien atienda lo que era de OTRAS
    # sesiones. Se relanza para que esas frases no queden colgadas.
    if any(n.endswith(".txt") for n in _archivos_cola()):
        _lanzar_runner(dict(os.environ))


def _lanzar_runner(entorno):
    entorno = dict(entorno)
    entorno["CLAUDE_VOZ_REPRODUCTOR"] = REPRODUCIR
    p = subprocess.Popen([sys.executable or "python3", RUNNER],
                         stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL,
                         start_new_session=True,
                         env=entorno)
    return p.pid


def decir(texto, maximo, voz=None, vel=None, sid=None):
    """Limpia, recorta y PONE EN COLA el texto. Devuelve (pid, texto_dicho)
    o (None, "") si no quedo nada que decir.

    No interrumpe a nadie: si Claude ya esta hablando, esto suena DESPUES.
    Antes aqui habia un callar() que mataba la frase en curso, y por eso el
    aviso de otra sesion se comia a la mitad el status que el usuario estaba
    oyendo (lo reporto en ago-2026)."""
    t = recortar(limpiar(texto), maximo)
    if len(t) < 2:
        return None, ""

    os.makedirs(COLA, exist_ok=True)
    _limpiar_temporales()
    _podar_cola()

    # El texto viaja por ARCHIVO, no por argumento: asi no hay que pelear con
    # comillas, acentos ni saltos de linea. El reproductor lo borra al terminar.
    # El nombre lleva el reloj DELANTE (para atender por orden de llegada) y la
    # sesion en medio (para que callar() sepa que es suyo sin abrir nada).
    marca = marca_de(sid if sid is not None else sesion_actual())
    base = os.path.join(COLA, f"voz-{int(time.time()*1000):013d}-{marca}-{os.getpid()}")

    # La voz/velocidad de ESTE texto viajan aparte: cuando le toque sonar, el
    # runner puede ser otro proceso con otro entorno.
    if voz or vel:
        with open(base + ".voz", "w") as f:
            if voz:
                f.write(f"CLAUDE_VOZ_SAY={voz}\n")
            if vel:
                f.write(f"CLAUDE_VOZ_VEL={vel}\n")

    # Se escribe con otra extension y se renombra: el renombrado es atomico, y
    # asi el runner nunca alcanza a leer un texto a medio escribir.
    with open(base + ".parcial", "w") as f:
        f.write(t)
    os.replace(base + ".parcial", base + ".txt")

    # Si ya hay un runner atendiendo la cola, este se muere solo contra el lock
    # y el que manda recoge el texto al terminar el actual. El PIDF lo escribe
    # el runner que SI agarro el lock, no este de aqui.
    return _lanzar_runner(os.environ), t


def _podar_cola():
    """Deja como mucho COLA_MAX textos esperando; bota los mas viejos.

    Lo que ya esta sonando lleva extension .sonando y no entra en esta cuenta:
    esa frase se termina, que es justo lo que pidio el usuario."""
    try:
        esperando = sorted(n for n in os.listdir(COLA) if n.endswith(".txt"))
        for n in esperando[:max(0, len(esperando) - (COLA_MAX - 1))]:
            for f in (n, n[:-4] + ".voz"):
                try:
                    os.remove(os.path.join(COLA, f))
                except OSError:
                    pass
    except Exception:
        pass


def _limpiar_temporales(edad_max=600):
    """Si se mata el reproductor a media frase su trap no corre y el .txt
    queda huerfano. Se barren los de mas de 10 minutos."""
    try:
        ahora = time.time()
        for n in os.listdir(COLA):
            f = os.path.join(COLA, n)
            if ahora - os.path.getmtime(f) > edad_max:
                os.remove(f)
    except Exception:
        pass
