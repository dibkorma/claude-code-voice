#!/bin/bash
# Reproductor FALSO que deja rastro: anota QUE mp3 le pidieron sonar.
# Sirve para probar que `--solo-generar` no suena, y que el modo normal
# aprovecha el mp3 ya precocinado en vez de rehacerlo.
echo "SONO $1" >> "${VOZ_TEST_LOG:?falta VOZ_TEST_LOG}"
sleep 0.2
