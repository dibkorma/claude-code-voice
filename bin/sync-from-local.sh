#!/bin/bash
# Pulls the engine back OUT of ~/.claude and into this repo.
#
# The engine is developed live in ~/.claude/hooks — that's where it runs and
# where it gets fixed. This copies it back here and re-applies the two things
# the repo does differently, so a fix made at 2am doesn't quietly stay local.
#
#   ./bin/sync-from-local.sh            copy, then show what changed
#   ./bin/sync-from-local.sh --check    change nothing, just say what differs
#
# WHAT IT SYNCS, AND WHY IT ISN'T A LIST ANY MORE
# The file list used to be hardcoded here. A hardcoded list can only carry the
# files someone remembered to add to it: two regression tests written in ago-2026
# would never have reached ~/.claude, and nothing written live would have reached
# the repo. Worse, silently — a list that misses a file looks exactly like a file
# that didn't change. So now the files IN THIS REPO are the list, and anything
# that exists on only one side gets REPORTED instead of being skipped in silence.
set -euo pipefail
AQUI="$(cd "$(dirname "$0")/.." && pwd)"
H="$HOME/.claude"
SOLO_MIRAR=0
[ "${1:-}" = "--check" ] && SOLO_MIRAR=1

# Files that diverge ON PURPOSE and must NOT be blindly overwritten:
#   hooks/voz-reproducir.sh   repo version is portable + reads voz.conf
#   commands/es/donde-estamos.md    repo version isn't pinned to one dialect
#   commands/es/hablar.md           repo version points at /silencio
#
# The test double is NOT in that list on purpose: it evolves with the engine
# (it has to imitate every mode the real player grows), and excluding it once
# already shipped a broken test suite. It gets synced and re-patched instead.
#
# CAREFUL: "by hand" is how the overlapping-voices bug of ago-29-2026 happened.
# The live player learned `--solo-generar` and this copy never did, because
# nobody re-read the diff. That's why they now print their diff, every run.
A_MANO="hooks/voz-reproducir.sh commands/es/donde-estamos.md commands/es/hablar.md"

es_a_mano() {
  case " $A_MANO " in *" $1 "*) return 0 ;; *) return 1 ;; esac
}

generalizar() {   # takes the personal names out of the comments
  perl -pi -e 's/\bde Mangan\b/del usuario/g; s/\ba Mangan\b/al usuario/g; s/\bMangan\b/el usuario/g;' "$1"
}

despersonalizado() {   # prints <file> as it would land in the repo
  perl -pe 's/\bde Mangan\b/del usuario/g; s/\ba Mangan\b/al usuario/g; s/\bMangan\b/el usuario/g;' "$1"
}

copiar() {        # copiar <src-in-.claude> <dst-in-repo>
  local src="$H/$1" dst="$AQUI/$2"
  [ -f "$src" ] || { echo "  falta en ~/.claude: $1"; return; }
  if [ "$SOLO_MIRAR" = 1 ]; then
    diff -q <(despersonalizado "$src") "$dst" >/dev/null 2>&1 \
      || echo "  DIFIERE: $2"
    return
  fi
  cp "$src" "$dst"
  generalizar "$dst"
}

# sincronizar <repo-dir> <local-dir> <glob...>
# Everything matching in THIS REPO is what gets pulled from ~/.claude. Files
# that live on only one side are collected and reported at the end.
SOLO_AQUI=""      # in the repo, missing from ~/.claude
SOLO_ALLA=""      # in ~/.claude, missing from the repo
sincronizar() {
  local rdir="$1" ldir="$2"; shift 2
  local f nombre
  for f in "$AQUI/$rdir"/*; do
    [ -f "$f" ] || continue
    nombre="$(basename "$f")"
    case "$nombre" in *.bak*|.*) continue ;; esac
    if [ ! -f "$H/$ldir/$nombre" ]; then
      SOLO_AQUI="$SOLO_AQUI $rdir/$nombre"
      continue
    fi
    es_a_mano "$rdir/$nombre" && continue
    copiar "$ldir/$nombre" "$rdir/$nombre"
  done
  # the other direction: written live, never brought over
  for f in "$H/$ldir"/*; do
    [ -f "$f" ] || continue
    nombre="$(basename "$f")"
    case "$nombre" in *.bak*|.*) continue ;; esac
    local coincide=0 patron
    for patron in "$@"; do
      case "$nombre" in $patron) coincide=1 ;; esac
    done
    [ "$coincide" = 1 ] || continue
    [ -f "$AQUI/$rdir/$nombre" ] || SOLO_ALLA="$SOLO_ALLA $ldir/$nombre"
  done
}

echo "Engine:"
sincronizar "hooks" "hooks" 'voz*' 'hablar*' 'decir*' 'callar*'

echo "Tests:"
sincronizar "hooks/tests" "hooks/tests" 'test_*.py' 'comun.py' 'correr-todas.sh' 'voz-reproducir.sh'
sincronizar "hooks/tests/bin" "hooks/tests/bin" '*'

echo "Spanish commands:"
for f in silencio.md; do
  copiar "commands/$f" "commands/es/$f"
done

if [ "$SOLO_MIRAR" = 0 ]; then
  # callar.sh in the repo must not depend on jq — re-apply that every time.
  if grep -q "jq -r" "$AQUI/hooks/callar.sh"; then
    python3 "$AQUI/bin/parche-callar.py" "$AQUI/hooks/callar.sh"
  fi
  python3 "$AQUI/bin/parche-doble-pruebas.py" "$AQUI/hooks/tests/voz-reproducir.sh"
  chmod +x "$AQUI/hooks/"*.sh "$AQUI/hooks/tests/"*.sh "$AQUI/hooks/tests/bin/"* 2>/dev/null || true
fi

# --- What the copy could not carry -------------------------------------------
if [ -n "$SOLO_AQUI" ]; then
  echo
  echo "Only in this repo — the live engine does NOT have these, so they never run"
  echo "for real and nothing local can keep them honest. Copy them to ~/.claude:"
  for f in $SOLO_AQUI; do echo "  $f"; done
fi
if [ -n "$SOLO_ALLA" ]; then
  echo
  echo "Only in ~/.claude — written live and never brought over. Add them here:"
  for f in $SOLO_ALLA; do echo "  $f"; done
fi

echo
echo "By hand — these diverge on purpose. Their diff, so a fix can't stay local:"
for f in $A_MANO; do
  local_f="$H/$f"
  case "$f" in commands/es/*) local_f="$H/commands/$(basename "$f")" ;; esac
  echo "  $f"
  if [ -f "$local_f" ]; then
    if diff -q <(despersonalizado "$local_f") "$AQUI/$f" >/dev/null 2>&1; then
      echo "      identical to ~/.claude"
    else
      diff <(despersonalizado "$local_f") "$AQUI/$f" | sed 's/^/      /' | head -40
    fi
  else
    echo "      not in ~/.claude"
  fi
done
echo
echo "English commands (commands/en/) are translations: update them yourself"
echo "when the Spanish ones change."
echo
if [ "$SOLO_MIRAR" = 0 ] && command -v git >/dev/null 2>&1; then
  cd "$AQUI" && git status --short
fi
