#!/bin/bash
# Installs the voice engine into ~/.claude/. Safe to run twice.
#
#   ./install.sh                 interactive: asks for command language
#   ./install.sh --lang en       English commands  (/speak, /catch-me-up)
#   ./install.sh --lang es       Spanish commands  (/hablar, /donde-estamos)
#   ./install.sh --no-edge-tts   skip the neural voice, use the OS voice
#   ./install.sh --voice-tap     also turn ON native dictation in tap mode
#   ./install.sh --dry-run       show what it would do, write nothing
set -euo pipefail
AQUI="$(cd "$(dirname "$0")" && pwd)"
DESTINO="$HOME/.claude"
LANG_CMD=""
EDGE=1
SECO=0
VOICE_TAP=0

while [ $# -gt 0 ]; do
  case "$1" in
    --lang) LANG_CMD="${2:-}"; shift 2 ;;
    --lang=*) LANG_CMD="${1#*=}"; shift ;;
    --no-edge-tts) EDGE=0; shift ;;
    --voice-tap) VOICE_TAP=1; shift ;;
    --dry-run) SECO=1; shift ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown option: $1"; exit 1 ;;
  esac
done

decir() { printf '%s\n' "$*"; }
paso()  { printf '\n\033[1m%s\033[0m\n' "$*"; }
corre() { if [ "$SECO" = 1 ]; then decir "  would run: $*"; else "$@"; fi; }

# --- 0. requirements ---------------------------------------------------------
paso "0. Checking requirements"
command -v python3 >/dev/null 2>&1 || { decir "  MISSING: python3 — install it and run this again"; exit 1; }
decir "  python3: $(python3 --version 2>&1)"
if command -v claude >/dev/null 2>&1; then
  decir "  claude:  $(claude --version 2>&1 | head -1)"
else
  decir "  NOTE: 'claude' is not on your PATH. The engine installs fine, but you"
  decir "        need Claude Code for it to do anything."
fi
case "$(uname -s)" in
  Darwin) decir "  os:      macOS (tested)" ;;
  Linux)  decir "  os:      Linux (should work: needs edge-tts + ffplay/mpv, or espeak-ng)" ;;
  *)      decir "  os:      $(uname -s) — untested, expect to tweak hooks/voz-reproducir.sh" ;;
esac

# --- 1. which language for the slash commands --------------------------------
if [ -z "$LANG_CMD" ]; then
  paso "1. Command language"
  decir "  en -> /speak and /catch-me-up"
  decir "  es -> /hablar and /donde-estamos"
  printf "  which one? [en/es] "
  read -r LANG_CMD < /dev/tty || LANG_CMD="en"
  LANG_CMD="${LANG_CMD:-en}"
fi
case "$LANG_CMD" in
  en|es) ;;
  *) decir "  --lang must be 'en' or 'es' (got: $LANG_CMD)"; exit 1 ;;
esac

# --- 2. the engine -----------------------------------------------------------
paso "2. Installing the engine into $DESTINO/hooks/"
corre mkdir -p "$DESTINO/hooks/tests/bin" "$DESTINO/commands"
for f in hablar.sh hablar.py callar.sh decir.sh decir.py voz-toggle.sh voz-silencio.sh \
         voz-reproducir.sh voz-runner.py voz_comun.py; do
  if [ -e "$DESTINO/hooks/$f" ] && ! cmp -s "$AQUI/hooks/$f" "$DESTINO/hooks/$f"; then
    SELLO="$(date +%Y%m%d-%H%M%S)"
    decir "  ! $f already exists and differs — keeping yours as $f.bak-$SELLO"
    corre cp "$DESTINO/hooks/$f" "$DESTINO/hooks/$f.bak-$SELLO"
  fi
  corre cp "$AQUI/hooks/$f" "$DESTINO/hooks/$f"
  decir "  hooks/$f"
done
corre chmod +x "$DESTINO/hooks/hablar.sh" "$DESTINO/hooks/callar.sh" \
                "$DESTINO/hooks/decir.sh" "$DESTINO/hooks/voz-toggle.sh" \
                "$DESTINO/hooks/voz-reproducir.sh" \
                "$DESTINO/hooks/voz-silencio.sh" 2>/dev/null || true

paso "3. Installing the tests into $DESTINO/hooks/tests/"
for f in comun.py correr-todas.sh voz-reproducir.sh test_voz_callar.py \
         test_voz_no_corta.py test_voz_por_sesion.py test_voz_sin_basura.py; do
  corre cp "$AQUI/hooks/tests/$f" "$DESTINO/hooks/tests/$f"
done
corre cp "$AQUI/hooks/tests/bin/afplay" "$AQUI/hooks/tests/bin/say" "$DESTINO/hooks/tests/bin/"
corre chmod +x "$DESTINO/hooks/tests/bin/afplay" "$DESTINO/hooks/tests/bin/say" \
                "$DESTINO/hooks/tests/voz-reproducir.sh" 2>/dev/null || true
decir "  7 test files + 2 fakes"

# --- 4. the slash commands ---------------------------------------------------
paso "4. Installing the /commands ($LANG_CMD)"
for f in "$AQUI/commands/$LANG_CMD"/*.md; do
  corre cp "$f" "$DESTINO/commands/$(basename "$f")"
  decir "  /$(basename "$f" .md)"
done

# --- 5. the neural voice -----------------------------------------------------
paso "5. Voice"
if [ "$EDGE" = 0 ]; then
  decir "  --no-edge-tts: skipping. Falls back to the OS voice (macOS 'say')."
elif command -v edge-tts >/dev/null 2>&1; then
  decir "  edge-tts already on your PATH: $(command -v edge-tts)"
elif ls "$HOME"/.config/*/.venv/bin/edge-tts >/dev/null 2>&1; then
  decir "  edge-tts found in an existing venv: $(ls "$HOME"/.config/*/.venv/bin/edge-tts | head -1)"
else
  decir "  installing edge-tts in its own venv ($DESTINO/hooks/.venv)"
  decir "  (free, no account, no API key — Microsoft Edge's neural voices)"
  if [ "$SECO" = 1 ]; then
    decir "  would run: python3 -m venv $DESTINO/hooks/.venv && pip install edge-tts"
  elif python3 -m venv "$DESTINO/hooks/.venv" >/dev/null 2>&1 \
       && "$DESTINO/hooks/.venv/bin/pip" install -q edge-tts >/dev/null 2>&1; then
    decir "  done: $("$DESTINO/hooks/.venv/bin/edge-tts" --version 2>&1 | head -1)"
  else
    decir "  couldn't install it (no network?). Not fatal: it falls back to the"
    decir "  OS voice, and picks edge-tts up automatically once it's there."
  fi
fi

# --- 5b. the voice that matches your language --------------------------------
CONF="$DESTINO/voz.conf"
if [ -e "$CONF" ]; then
  decir "  $CONF already exists — leaving your voice settings alone"
elif [ "$SECO" = 1 ]; then
  decir "  would write $CONF (voice for '$LANG_CMD')"
else
  if [ "$LANG_CMD" = "es" ]; then
    V_EDGE="es-MX-DaliaNeural"; V_VEL="+20%"; V_SAY="Paulina"
  else
    V_EDGE="en-US-AvaNeural";   V_VEL="+10%"; V_SAY="Samantha"
  fi
  cat > "$CONF" <<CONFEOF
# Which voice Claude answers in. Edit freely — it is read on every sentence.
# Env vars of the same name win over this file.
#
# CC_VOZ         edge-tts voice. Full list:  edge-tts --list-voices
# CC_VOZ_VEL     edge-tts rate: +20%, -10%, +0%
# CLAUDE_VOZ_SAY fallback voice for macOS 'say' (say -v '?' lists them)
# CLAUDE_VOZ_VEL fallback rate for 'say', in words per minute
CC_VOZ=$V_EDGE
CC_VOZ_VEL=$V_VEL
CLAUDE_VOZ_SAY=$V_SAY
CLAUDE_VOZ_VEL=215
CONFEOF
  decir "  $CONF -> $V_EDGE at $V_VEL (fallback: $V_SAY)"
fi

# --- 6. settings.json --------------------------------------------------------
paso "6. Wiring the hooks into settings.json"
# Sin array: en bash 3.2 (el que trae macOS) un array vacio con `set -u`
# aborta el script — "${A[@]}" con A vacio cuenta como variable sin definir.
ARGS_MERGE=""
[ "$SECO" = 1 ] && ARGS_MERGE="$ARGS_MERGE --dry-run"
[ "$VOICE_TAP" = 1 ] && ARGS_MERGE="$ARGS_MERGE --voice-tap"
# shellcheck disable=SC2086
python3 "$AQUI/install/merge-settings.py" $ARGS_MERGE
if [ "$VOICE_TAP" = 0 ]; then
  decir "  (native dictation left as it is — turn it on yourself with /voice,"
  decir "   or rerun this with --voice-tap)"
fi

# --- 7. proof ----------------------------------------------------------------
paso "7. Running the tests (nothing will make a sound)"
if [ "$SECO" = 1 ]; then
  decir "  would run: bash $DESTINO/hooks/tests/correr-todas.sh"
else
  bash "$DESTINO/hooks/tests/correr-todas.sh" || {
    decir ""
    decir "  Tests failed. The engine is installed but something is off —"
    decir "  open an issue with the output above."
    exit 1
  }
fi

paso "Done."
if [ "$LANG_CMD" = "es" ]; then
  decir "  Abre Claude Code y escribe  /hablar        -> te contesta hablando"
  decir "  Reabre una sesion y escribe /donde-estamos -> te cuenta donde quedaste"
  decir "  Desde cualquier ventana:    /silencio      -> las apaga todas"
  decir "  Para hablarle TU: escribe /voice tap, y luego toca ESPACIO con la linea"
  decir "  vacia, habla, y toca ESPACIO otra vez. Eso es dictado nativo de Claude"
  decir "  Code, no de este repo."
else
  decir "  Open Claude Code and type  /speak       -> it starts talking back"
  decir "  Reopen a session and type  /catch-me-up -> it tells you where you left off"
  decir "  From any window, type      /silence     -> turns them all off"
  decir "  To talk to IT: run /voice tap, then tap SPACE on an empty line, talk,"
  decir "  and tap SPACE again. That half is Claude Code's built-in dictation,"
  decir "  not this repo."
fi
decir ""
decir "  Voice is per session: /speak only turns on the window you ran it in."
decir "  Log: ~/.claude/voz-debug.log  (one line per reply, says why it stayed quiet)"
