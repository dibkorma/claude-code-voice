#!/bin/bash
# Prende o apaga que Claude conteste hablando EN ESTA SESION. Lo usa /hablar.
#
# Es por sesion a proposito: el usuario corre muchas ventanas a la vez y pidio
# elegir cual le habla — "no que todas me esten hablando porque se convierte en
# un problema" (ago-2026). Cada ventana prendida deja su archivito en voz-on.d/.
#
#   voz-toggle.sh            prende/apaga esta sesion
#   voz-toggle.sh MAGU       la prende y le pone ese nombre
#   voz-toggle.sh --estado   dice como esta, sin cambiar nada
#   voz-toggle.sh --todas-no apaga TODAS las sesiones
#
# El nombre importa cuando hay varias ventanas hablando: Claude lo dice antes
# de la frase, porque el usuario esta OYENDO y no puede ver de cual salio la voz.
D="$HOME/.claude/voz-on.d"
mkdir -p "$D"

# Quien soy. Claude Code lo pone en el entorno; de respaldo, la ultima sesion
# donde el usuario escribio (la anota callar.sh justo antes de correr esto).
SID="${CLAUDE_CODE_SESSION_ID:-}"
[ -z "$SID" ] && SID="$(cat "$HOME/.claude/.voz-sesion-activa" 2>/dev/null)"
if [ -z "$SID" ]; then
  echo "ERROR: no pude saber en que sesion estoy"
  exit 1
fi
MARCA="${SID:0:8}"

callar_esta() {
  SID="$SID" python3 -c "
import sys, os
sys.path.insert(0, os.path.expanduser('~/.claude/hooks'))
import voz_comun
voz_comun.callar(os.environ['SID'])
" 2>/dev/null
}

otras() {
  local n
  n=$(ls "$D" 2>/dev/null | grep -vc "^${MARCA}$")
  echo "$n"
}

case "${1:-}" in
  --estado)
    if [ -f "$D/$MARCA" ]; then
      echo "PRENDIDA nombre=$(cat "$D/$MARCA") otras=$(otras)"
    else
      echo "APAGADA otras=$(otras)"
    fi
    ;;
  --todas-no)
    rm -f "$D"/* 2>/dev/null
    callar_esta
    echo "TODAS APAGADAS"
    ;;
  *)
    NOMBRE="${1:-}"
    [ -z "$NOMBRE" ] && NOMBRE="$(basename "$PWD")"
    if [ -f "$D/$MARCA" ] && [ -z "${1:-}" ]; then
      rm -f "$D/$MARCA"
      callar_esta
      echo "APAGADA otras=$(otras)"
    else
      # con nombre explicito siempre prende (asi se puede renombrar sin apagar)
      printf '%s' "$NOMBRE" > "$D/$MARCA"
      echo "PRENDIDA nombre=$NOMBRE otras=$(otras)"
    fi
    ;;
esac
