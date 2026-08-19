"""Dice un texto en voz alta, completo. Lo usa el comando /resumen.

Se diferencia del hook Stop en dos cosas:
  - tope largo (~1200 caracteres): un resumen sale entero, no solo el titular
  - habla AUNQUE la voz este apagada con /hablar: el usuario lo pidio expreso

Texto por stdin, o como argumento (una ruta de archivo tambien vale).
"""
import os, sys

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "hooks"))
import voz_comun as voz

MAX = int(os.environ.get("CLAUDE_VOZ_MAX_RESUMEN", "0"))
# Sin tope tambien aqui: si el pide el resumen hablado, lo quiere entero.
YA_DIJO = os.path.join(os.path.expanduser("~"), ".claude", ".voz-ya-dijo")

if len(sys.argv) > 1 and sys.argv[1].strip():
    arg = sys.argv[1]
    if os.path.isfile(arg):
        try:
            with open(arg, errors="ignore") as f:
                texto = f.read()
        except Exception as e:
            print(f"[voz] no pude leer el archivo: {e}")
            sys.exit(1)
    else:
        texto = arg          # el argumento ES el texto
else:
    texto = sys.stdin.read()

pid, dicho = voz.decir(texto, MAX)

if pid:
    # Marca para que el hook Stop no repita el resumen al terminar el turno.
    with open(YA_DIJO, "w") as f:
        f.write(str(pid))
    seg = round(len(dicho.split()) / 190 * 60)
    print(f"[voz] hablando {len(dicho)} caracteres (~{seg}s)")
else:
    print("[voz] no quedo nada que decir despues de limpiar el texto")
