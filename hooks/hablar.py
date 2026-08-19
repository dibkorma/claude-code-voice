"""Hook Stop: dice en voz alta el titular de la ultima respuesta de Claude.

Solo habla si ESTA sesion tiene la voz prendida (con /hablar). Es a proposito:
el usuario corre muchas ventanas a la vez y pidio elegir cual le habla — "no que
todas me esten hablando porque se convierte en un problema" (ago-2026).
"""
import datetime, json, os, sys, traceback

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "hooks"))
import voz_comun as voz

MAX  = int(os.environ.get("CLAUDE_VOZ_MAX", "900"))
# 900 caracteres son unos 47 segundos hablados (medido, no a ojo: 350 dan 19s
# y 1600 dan 1m23s). Empezo en 350 —solo el titular— y el usuario pregunto si
# podia leerle un parrafo entero: puede, el limite era una decision, no una
# restriccion. Con CLAUDE_VOZ_MAX=0 lee TODO, sin recortar.
HOME = os.path.expanduser("~")
YA_DIJO = os.path.join(HOME, ".claude", ".voz-ya-dijo")
LOG     = os.path.join(HOME, ".claude", "voz-debug.log")

_raw = sys.stdin.read()


def _log(msg):
    try:
        # el hook corre en CADA respuesta: el log no puede crecer sin fin
        if os.path.exists(LOG) and os.path.getsize(LOG) > 200_000:
            with open(LOG) as f:
                cola = f.read()[-40_000:]
            cola = cola.split("\n", 1)[-1]
            with open(LOG, "w") as f:
                f.write(cola)
        with open(LOG, "a") as f:
            f.write(f"[{datetime.datetime.now():%H:%M:%S}] {msg}\n")
    except Exception:
        pass


_log(f"llamado ({len(_raw)}B, job={os.environ.get('CLAUDE_JOB_DIR') or '-'})")

# 1. De que sesion es esta respuesta.
try:
    payload = json.loads(_raw)
except Exception as e:
    _log(f"  SALIDA: stdin no es JSON valido -> {e}")
    sys.exit(0)

sid = (payload.get("session_id") or "").strip() or voz.sesion_actual()

# 2. Interruptor DE ESTA SESION. Antes era uno solo para toda la maquina, mas
#    un filtro de "la ultima ventana donde escribio"; eso hacia hablar a
#    cualquier ventana en la que tocara algo. Ahora habla la que el prendio.
if not voz.habla_esta_sesion(sid):
    prendidas = voz.sesiones_con_voz()
    _log(f"  SALIDA: esta sesion ({sid[:8]}) no tiene voz. Con voz: {prendidas or 'ninguna'}")
    sys.exit(0)

# 3. Ya hablo el comando /donde-estamos en este turno -> no repetir.
#    La marca caduca a los 2 min para que una huerfana no deje mudo a Claude.
# todo el bloque va en try: la marca puede desaparecer entre el exists() y el
# getmtime() (otra sesion, /aldia en paralelo). Si el hook revienta sale != 0,
# y este hook JAMAS debe fallar.
try:
    import time
    edad = time.time() - os.path.getmtime(YA_DIJO)
    try:
        os.remove(YA_DIJO)
    except Exception:
        pass
    if edad < 120:
        _log(f"  SALIDA: /aldia ya hablo hace {edad:.0f}s")
        sys.exit(0)
    _log("  marca de /aldia caducada, sigo normal")
except SystemExit:
    raise
except Exception:
    pass   # sin marca utilizable -> seguimos normal

# 4. El texto: la doc oficial dice usar `last_assistant_message`, NO el
#    transcript, que "puede ir retrasado" y haria hablar la respuesta ANTERIOR.
last = payload.get("last_assistant_message")

if not last or not str(last).strip():
    _log("  sin last_assistant_message, caigo al transcript")
    tp = payload.get("transcript_path") or ""
    last = None
    if tp and os.path.exists(tp):
        try:
            with open(tp, errors="ignore") as f:
                for line in f:
                    try:
                        o = json.loads(line)
                    except Exception:
                        continue
                    if o.get("type") != "assistant":
                        continue
                    c = o.get("message", {}).get("content", [])
                    if not isinstance(c, list):
                        continue
                    txt = "".join(b.get("text", "") for b in c
                                  if isinstance(b, dict) and b.get("type") == "text")
                    if txt.strip():
                        last = txt
        except Exception as e:
            _log(f"  SALIDA: no pude leer el transcript -> {e}")
            sys.exit(0)

if not last:
    _log("  SALIDA: no encontre mensaje de assistant")
    sys.exit(0)

# 5. Si hay MAS DE UNA ventana hablando, la frase arranca diciendo de cual es.
#    el usuario esta oyendo, no viendo: sin esto no sabe quien le esta hablando
#    ("no se de cual me estabas hablando, porque no puedo ver", ago-19-2026).
#    Con una sola ventana prendida se calla el nombre, que ahi sobra.
if len(voz.sesiones_con_voz()) > 1:
    last = f"{voz.etiqueta_de(sid)}. {last}"

# 6. Hablar. Va con la sesion pegada: asi, cuando el usuario escriba AQUI, se corta
#    esto y no lo que le esta contando otra ventana.
try:
    pid, dicho = voz.decir(last, MAX, sid=sid)
    if pid:
        _log(f"  HABLO ({sid[:8]}): PID={pid} texto={dicho[:120]!r}")
    else:
        _log("  SALIDA: no quedo nada que decir tras limpiar")
except Exception as e:
    _log(f"  SALIDA: fallo al hablar -> {e}\n{traceback.format_exc()}")
