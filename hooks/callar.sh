#!/bin/bash
# Hook UserPromptSubmit. Hace dos cosas:
#   1. Marca ESTA sesion como "la activa" — es donde el usuario acaba de escribir,
#      y por tanto la unica que debe hablar. Sin esto, sus 5 trabajos de fondo
#      hablarian todos encima.
#   2. Corta la voz que este sonando (tambien mata el eco del microfono).
# Lectura ACOTADA del payload. Un `cat` pelado se cuelga para siempre si quien
# nos llamo dejo la entrada abierta sin escribir — y este hook corre en CADA
# mensaje suyo, asi que colgarse aqui le congela la sesion. Como hook real el
# JSON llega y cierra al instante, y el limite no se nota.
RAW=""
if [ ! -t 0 ]; then
  # el `|| [ -n "$_linea" ]` es obligatorio: el payload llega SIN salto de linea
  # final, y ahi `read` devuelve fallo aunque si leyo el contenido. Sin eso se
  # descarta el JSON entero y la sesion activa nunca se anota (= Claude mudo).
  while IFS= read -r -t 1 _linea || [ -n "$_linea" ]; do
    RAW="$RAW$_linea"
    _linea=""
  done
fi

# Se saca con python3 y no con jq: python3 ya hace falta para el resto del
# motor, y jq no viene en todas las Macs. Una dependencia menos que explicar.
SID=$(printf '%s' "$RAW" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('session_id') or '')
except Exception:
    print('')
" 2>/dev/null)
if [ -n "$SID" ]; then
  printf '%s' "$SID" > "$HOME/.claude/.voz-sesion-activa"
fi

# Cortar la voz: se DELEGA en voz_comun.callar(), que es la unica
# implementacion. Antes habia una copia en bash que buscaba un proceso `say`;
# al pasar la voz a edge-tts el proceso paso a ser `bash voz-reproducir.sh` y
# la copia de bash dejo de matar nada, en silencio. Una sola fuente de verdad.
#
# Se corta SOLO lo de esta sesion: si el escribe aqui, no hay por que callar la
# ventana de al lado que le esta contando otra cosa.
SID_ARG="${SID:-$CLAUDE_CODE_SESSION_ID}"
SID="$SID_ARG" python3 -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.claude/hooks'))
import voz_comun
voz_comun.callar(os.environ.get('SID') or None)
" 2>/dev/null

exit 0
