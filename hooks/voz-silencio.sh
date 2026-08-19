#!/bin/bash
# EL APAGÓN GENERAL de la voz. Lo usa el comando /silencio.
#
# el usuario (19-ago-2026): "necesito un comando general que apague todas las voces
# en todos lados". El toggle por sesión sirve para elegir quién habla; esto es
# lo contrario — un botón de pánico que se corre desde CUALQUIER ventana y deja
# la casa en silencio, sin ir ventana por ventana.
#
# Hace cuatro cosas, y las cuatro hacen falta:
#   1. apaga el interruptor de TODAS las sesiones
#   2. corta la frase que esté sonando ahora mismo
#   3. tira lo que quedaba en cola
#   4. barre cualquier reproductor huérfano que se haya soltado
set -u
D="$HOME/.claude/voz-on.d"
ANTES=$(ls "$D" 2>/dev/null | wc -l | tr -d ' ')

# 1 y 2 y 3 — el apagado y el corte. callar() sin sesión corta TODO.
rm -f "$D"/* 2>/dev/null
python3 -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.claude/hooks'))
import voz_comun
voz_comun.callar()
" 2>/dev/null

# 4 — huérfanos. Se matan SOLO los que están reproduciendo un audio nuestro
# (la ruta lleva /voz. y sale del temporal): un afplay con la música del usuario
# no se toca ni por error.
SUELTOS=0
for pid in $(pgrep -f 'afplay .*/voz\.' 2>/dev/null) \
           $(pgrep -f 'edge-tts .*--write-media' 2>/dev/null) \
           $(pgrep -f 'voz-reproducir\.sh' 2>/dev/null) \
           $(pgrep -f 'voz-runner\.py' 2>/dev/null); do
  kill -TERM "$pid" 2>/dev/null && SUELTOS=$((SUELTOS+1))
done

QUEDAN=$(ls "$D" 2>/dev/null | wc -l | tr -d ' ')
COLA=$(ls "$HOME/.claude/.voz-cola" 2>/dev/null | wc -l | tr -d ' ')
echo "SILENCIO apagadas=$ANTES quedan=$QUEDAN sueltos=$SUELTOS cola=$COLA"
