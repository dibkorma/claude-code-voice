#!/bin/bash
# Corre todas las pruebas de la voz. Ninguna suena ni deja archivos de audio.
#   bash ~/.claude/hooks/tests/correr-todas.sh
cd "$(dirname "$0")" || exit 1
export VOZ_TEST_TMP="${VOZ_TEST_TMP:-$(mktemp -d)}"
fallos=0
for t in test_*.py; do
  if python3 "$t" >/tmp/voz-test-salida 2>&1; then
    echo "PASA   $t"
  else
    echo "FALLA  $t"
    sed 's/^/       /' /tmp/voz-test-salida
    fallos=$((fallos+1))
  fi
done
rm -f /tmp/voz-test-salida
[ "$fallos" = 0 ] && echo "todas OK" || echo "$fallos con falla"
exit "$fallos"
