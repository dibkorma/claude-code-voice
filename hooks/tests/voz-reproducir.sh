#!/bin/bash
# DOBLE DE PRUEBA del reproductor. No suena nada: solo deja rastro de cuando
# empezo y cuando termino de "hablar" cada texto, asi una frase cortada a la
# mitad se ve como un INICIO sin su FIN.
#
# Se llama IGUAL que el real a proposito: voz_comun._matar() solo mata procesos
# cuya linea de comando contiene "voz-reproducir.sh". Con otro nombre, el doble
# seria inmortal y la prueba no podria reproducir el corte.
TXT="$1"
LOG="${VOZ_TEST_LOG:?falta VOZ_TEST_LOG}"
# 80 y no 40: el limite corta la frase que los asserts buscan, y una prueba
# que falla por el largo del texto de ejemplo no dice nada util.
CUERPO="$(head -c 80 "$TXT")"
trap 'rm -f "$TXT"' EXIT
echo "INICIO $CUERPO" >> "$LOG"
sleep 2
echo "FIN $CUERPO" >> "$LOG"
