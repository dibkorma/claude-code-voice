"""Re-applies the repo's one change to the test double after a sync.

The double logs the first N characters of each sentence so the asserts can find
it. Upstream it is 40, which is shorter than the example sentences in this repo
(they got longer when the personal name came out of them), so a test would fail
because of the length of its own example — an error message that points at the
logic and lies. 80 fixes that and changes nothing else.

Run by bin/sync-from-local.sh; it is a no-op if the change is already there.
"""
import sys

p = sys.argv[1]
s = open(p).read()
viejo = 'CUERPO="$(head -c 40 "$TXT")"'
nuevo = ('# 80 y no 40: 40 corta la frase que los asserts buscan, y una prueba que\n'
         '# falla por el largo de su propio ejemplo no dice nada util.\n'
         'CUERPO="$(head -c 80 "$TXT")"')
if viejo not in s:
    print("  tests/voz-reproducir.sh: ya estaba en 80" if 'head -c 80' in s
          else "  tests/voz-reproducir.sh: OJO, no encontre la linea del limite")
    sys.exit(0)
open(p, "w").write(s.replace(viejo, nuevo))
print("  tests/voz-reproducir.sh: limite 40 -> 80")
