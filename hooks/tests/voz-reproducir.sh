#!/bin/bash
# DOBLE DE PRUEBA del reproductor. No suena nada: solo deja rastro de cuando
# empezo y cuando termino de "hablar" cada texto, asi una frase cortada a la
# mitad se ve como un INICIO sin su FIN.
#
# Se llama IGUAL que el real a proposito: voz_comun._matar() solo mata procesos
# cuya linea de comando contiene "voz-reproducir.sh". Con otro nombre, el doble
# seria inmortal y la prueba no podria reproducir el corte.
#
# Imita los DOS modos del real, incluido `--solo-generar` (preparar el mp3 del
# trozo siguiente sin reproducirlo). Cuando el doble no lo imitaba, la prueba
# "sonaba" el trozo que solo debia prepararse y el orden salia al reves — que
# es exactamente el defecto que la prueba tiene que cazar si vuelve.
TXT="$1"
MODO="${2:-}"
LOG="${VOZ_TEST_LOG:?falta VOZ_TEST_LOG}"

if [ "$MODO" = "--solo-generar" ]; then
  : > "$TXT.mp3"          # queda listo al lado, sin sonar ni anotar nada
  exit 0
fi

# 80 y no 40: 40 corta la frase que los asserts buscan, y una prueba que
# falla por el largo de su propio ejemplo no dice nada util.
CUERPO="$(head -c 80 "$TXT")"
limpiar() { rm -f "$TXT" "$TXT.mp3" 2>/dev/null; }
trap limpiar EXIT
# `exit` en el trap y `sleep & wait`: igual que el real. Sin las dos cosas, al
# matarlo bash termina el sleep, sigue el guion y anota el FIN — o sea, una
# frase cortada se veia como una frase completa y la prueba mentia.
trap 'limpiar; exit 143' INT TERM HUP
echo "INICIO $CUERPO" >> "$LOG"
sleep 2 & wait $!
echo "FIN $CUERPO" >> "$LOG"
