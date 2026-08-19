#!/bin/bash
# Pulls the engine back OUT of ~/.claude and into this repo.
#
# The engine is developed live in ~/.claude/hooks — that's where it runs and
# where it gets fixed. This copies it back here and re-applies the two things
# the repo does differently, so a fix made at 2am doesn't quietly stay local.
#
#   ./bin/sync-from-local.sh            copy, then show what changed
#   ./bin/sync-from-local.sh --check    change nothing, just say what differs
set -euo pipefail
AQUI="$(cd "$(dirname "$0")/.." && pwd)"
H="$HOME/.claude"
SOLO_MIRAR=0
[ "${1:-}" = "--check" ] && SOLO_MIRAR=1

# Files that diverge ON PURPOSE and must NOT be blindly overwritten:
#   hooks/voz-reproducir.sh   repo version is portable + reads voz.conf
#   hooks/tests/voz-reproducir.sh   repo version logs 80 chars, not 40
#   commands/es/donde-estamos.md    repo version isn't pinned to one dialect
#   commands/es/hablar.md           repo version points at /silencio
A_MANO="hooks/voz-reproducir.sh hooks/tests/voz-reproducir.sh commands/es/donde-estamos.md commands/es/hablar.md"

generalizar() {   # takes the personal names out of the comments
  perl -pi -e 's/\bde Mangan\b/del usuario/g; s/\ba Mangan\b/al usuario/g; s/\bMangan\b/el usuario/g;' "$1"
}

copiar() {        # copiar <src-in-.claude> <dst-in-repo>
  local src="$H/$1" dst="$AQUI/$2"
  [ -f "$src" ] || { echo "  falta en ~/.claude: $1"; return; }
  if [ "$SOLO_MIRAR" = 1 ]; then
    diff -q <(perl -pe 's/\bde Mangan\b/del usuario/g; s/\ba Mangan\b/al usuario/g; s/\bMangan\b/el usuario/g;' "$src") "$dst" >/dev/null 2>&1 \
      || echo "  DIFIERE: $2"
    return
  fi
  cp "$src" "$dst"
  generalizar "$dst"
}

echo "Engine:"
for f in hablar.sh hablar.py callar.sh decir.sh decir.py voz-toggle.sh \
         voz-silencio.sh voz-runner.py voz_comun.py; do
  copiar "hooks/$f" "hooks/$f"
done

echo "Tests:"
for f in comun.py correr-todas.sh test_voz_callar.py test_voz_no_corta.py \
         test_voz_por_sesion.py test_voz_sin_basura.py; do
  copiar "hooks/tests/$f" "hooks/tests/$f"
done

echo "Spanish commands:"
for f in silencio.md; do
  copiar "commands/$f" "commands/es/$f"
done

if [ "$SOLO_MIRAR" = 0 ]; then
  # callar.sh in the repo must not depend on jq — re-apply that every time.
  if grep -q "jq -r" "$AQUI/hooks/callar.sh"; then
    python3 "$AQUI/bin/parche-callar.py" "$AQUI/hooks/callar.sh"
  fi
  chmod +x "$AQUI/hooks/"*.sh "$AQUI/hooks/tests/"*.sh 2>/dev/null || true
fi

echo
echo "By hand — these diverge on purpose, check them if you touched the originals:"
for f in $A_MANO; do echo "  $f"; done
echo
echo "English commands (commands/en/) are translations: update them yourself"
echo "when the Spanish ones change."
echo
if [ "$SOLO_MIRAR" = 0 ] && command -v git >/dev/null 2>&1; then
  cd "$AQUI" && git status --short
fi
