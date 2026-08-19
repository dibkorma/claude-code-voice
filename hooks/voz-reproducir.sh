#!/bin/bash
# Reproduce en voz alta el texto de un archivo. Lo lanza voz_comun.decir().
#
# Voz neuronal con edge-tts (gratis, sin cuenta ni llave). Si edge-tts no esta
# o no hay red, cae al TTS del sistema — nunca se queda sin hablar.
#
# Se configura por entorno, sin tocar codigo:
#   CC_VOZ            voz de edge-tts        (por defecto es-MX-DaliaNeural)
#   CC_VOZ_VEL        velocidad de edge-tts  (formato +20%, -10%, +0%)
#   CC_EDGE_TTS       ruta al binario edge-tts, si no esta en el PATH
#   CC_REPRODUCTOR    reproductor de mp3     (por defecto: el que encuentre)
#   CLAUDE_VOZ_SAY    voz del `say` de macOS (respaldo)
#   CLAUDE_VOZ_VEL    velocidad del `say`    (palabras por minuto)
set -u
TXT="${1:?falta el archivo de texto}"

# --- Configuracion: ~/.claude/voz.conf ---------------------------------------
# Lo escribe el instalador con la voz del idioma que elegiste, y se puede editar
# a mano. NO se hace `source`: se leen solo las claves conocidas, para que un
# archivo de configuracion no pueda ejecutar nada. El entorno pisa al archivo.
CONF="${CC_VOZ_CONF:-$HOME/.claude/voz.conf}"
if [ -f "$CONF" ]; then
  while IFS='=' read -r _k _v || [ -n "$_k" ]; do
    case "$_k" in \#*|"") continue ;; esac
    _v="${_v%\"}"; _v="${_v#\"}"          # comillas opcionales
    case "$_k" in
      CC_VOZ|CC_VOZ_VEL|CC_EDGE_TTS|CC_REPRODUCTOR|CLAUDE_VOZ_SAY|CLAUDE_VOZ_VEL)
        eval "_actual=\${$_k:-}"
        [ -z "$_actual" ] && export "$_k=$_v"
        ;;
    esac
  done < "$CONF"
fi

VOZ_EDGE="${CC_VOZ:-es-MX-DaliaNeural}"
VEL_EDGE="${CC_VOZ_VEL:-+20%}"
VOZ_SAY="${CLAUDE_VOZ_SAY:-Paulina}"
VEL_SAY="${CLAUDE_VOZ_VEL:-215}"

# Se limpia SIEMPRE, tambien si nos matan (callar.sh manda SIGTERM al grupo):
# sin INT/TERM/HUP el mp3 a medias se quedaba en el temporal.
limpiar() { rm -f "$TXT" "${MP3:-}" "${SEMILLA:-}" 2>/dev/null; }
trap limpiar EXIT INT TERM HUP

# Barrido de huerfanos viejos. Durante meses cada frase dejo un archivo tirado
# aqui (ver SEMILLA mas abajo); una hora de gracia para no tocar el de una voz
# que este sonando en otra ventana.
find "${TMPDIR:-/tmp}" -maxdepth 1 -name 'voz.*' -type f -mmin +60 -delete 2>/dev/null

# --- Donde esta edge-tts -----------------------------------------------------
# En orden: el que digas tu, el del PATH, el venv que crea el instalador, y por
# ultimo cualquier venv de ~/.config (asi reusa uno que ya tengas por ahi).
buscar_edge() {
  [ -n "${CC_EDGE_TTS:-}" ] && [ -x "$CC_EDGE_TTS" ] && { echo "$CC_EDGE_TTS"; return; }
  local p
  p="$(command -v edge-tts 2>/dev/null)" && [ -n "$p" ] && { echo "$p"; return; }
  [ -x "$HOME/.claude/hooks/.venv/bin/edge-tts" ] && { echo "$HOME/.claude/hooks/.venv/bin/edge-tts"; return; }
  for d in "$HOME"/.config/*/.venv/bin/edge-tts; do
    [ -x "$d" ] && { echo "$d"; return; }
  done
}

# --- Con que se reproduce un mp3 --------------------------------------------
reproducir_mp3() {
  local mp3="$1"
  if [ -n "${CC_REPRODUCTOR:-}" ]; then
    # En segundo plano + wait: en primer plano bash no atiende el SIGTERM hasta
    # que el reproductor termine solo, y la limpieza no corre.
    $CC_REPRODUCTOR "$mp3" & wait $!; return $?
  fi
  if command -v afplay >/dev/null 2>&1; then         # macOS
    afplay "$mp3" & wait $!; return $?
  fi
  if command -v ffplay >/dev/null 2>&1; then         # ffmpeg
    ffplay -nodisp -autoexit -loglevel quiet "$mp3" & wait $!; return $?
  fi
  if command -v mpv >/dev/null 2>&1; then
    mpv --no-video --really-quiet "$mp3" & wait $!; return $?
  fi
  return 1
}

# --- TTS del sistema, cuando no hay edge-tts --------------------------------
tts_del_sistema() {
  if command -v say >/dev/null 2>&1; then            # macOS
    say -v "$VOZ_SAY" -r "$VEL_SAY" -f "$TXT" & wait $!; return $?
  fi
  if command -v espeak-ng >/dev/null 2>&1; then      # Linux
    espeak-ng -f "$TXT" & wait $!; return $?
  fi
  if command -v espeak >/dev/null 2>&1; then
    espeak -f "$TXT" & wait $!; return $?
  fi
  return 1
}

EDGE="$(buscar_edge)"

if [ -n "$EDGE" ]; then
  # OJO: `mktemp -t voz` CREA el archivo y devuelve su ruta; al pegarle .mp3 se
  # trabaja sobre otro nombre y el original quedaba huerfano. Se guarda aparte
  # para borrarlo — habia 30 tirados cuando el usuario lo noto (ago-19-2026).
  SEMILLA="$(mktemp -t voz)"
  MP3="$SEMILLA.mp3"
  if "$EDGE" --voice "$VOZ_EDGE" --rate="$VEL_EDGE" --file "$TXT" --write-media "$MP3" >/dev/null 2>&1 \
     && [ -s "$MP3" ]; then
    reproducir_mp3 "$MP3" && exit 0
  fi
fi

# respaldo: sin edge-tts, sin red, mp3 vacio o sin reproductor de mp3
tts_del_sistema
