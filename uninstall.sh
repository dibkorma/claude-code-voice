#!/bin/bash
# Takes the voice engine back out of ~/.claude/. Leaves your settings.json
# otherwise intact — only the two hooks this project added come out.
#
#   ./uninstall.sh            asks before doing anything
#   ./uninstall.sh --yes      no questions
#   ./uninstall.sh --dry-run  show what it would remove, remove nothing
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
DESTINO="$HOME/.claude"
SECO=0; SI=0
for a in "$@"; do
  case "$a" in
    --dry-run) SECO=1 ;;
    --yes|-y)  SI=1 ;;
    -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
  esac
done
decir() { printf '%s\n' "$*"; }
corre() { if [ "$SECO" = 1 ]; then decir "  would remove: $*"; else rm -rf "$@"; fi; }

decir "This removes:"
decir "  - the 9 engine files in $DESTINO/hooks/"
decir "  - the tests in $DESTINO/hooks/tests/"
decir "  - the slash commands (hablar/donde-estamos, speak/catch-me-up)"
decir "  - the runtime state (voz-on.d, the queue, the debug log)"
decir "  - the two hooks in settings.json (a backup is made first)"
decir ""
decir "It does NOT touch: your native /voice setting, any other hook, or anything"
decir "else in settings.json."
decir ""
if [ "$SI" = 0 ] && [ "$SECO" = 0 ]; then
  printf "Go ahead? [y/N] "
  read -r r < /dev/tty || r="n"
  case "$r" in y|Y|yes) ;; *) decir "Nothing done."; exit 0 ;; esac
fi

for f in hablar.sh hablar.py callar.sh decir.sh decir.py voz-toggle.sh voz-silencio.sh \
         voz-reproducir.sh voz-runner.py voz_comun.py; do
  [ -e "$DESTINO/hooks/$f" ] && corre "$DESTINO/hooks/$f"
done
[ -d "$DESTINO/hooks/tests" ] && corre "$DESTINO/hooks/tests"
[ -d "$DESTINO/hooks/.venv" ] && corre "$DESTINO/hooks/.venv"
for c in hablar donde-estamos silencio speak catch-me-up silence; do
  [ -e "$DESTINO/commands/$c.md" ] && corre "$DESTINO/commands/$c.md"
done
for e in voz.conf voz-on.d .voz-cola .voz.pid .voz-runner.lock .voz-ya-dijo \
         .voz-sesion-activa voz-debug.log; do
  [ -e "$DESTINO/$e" ] && corre "$DESTINO/$e"
done

decir ""
decir "settings.json:"
if [ "$SECO" = 1 ]; then
  python3 "$AQUI/install/merge-settings.py" --remove --dry-run | head -5
else
  python3 "$AQUI/install/merge-settings.py" --remove
fi
decir ""
decir "Done. Claude goes quiet on the next reply."
