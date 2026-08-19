"""Takes the jq dependency out of callar.sh after a sync.

jq isn't on every Mac and python3 already is — one less thing to explain in the
README. Run by bin/sync-from-local.sh; it is a no-op if the jq line is gone.
"""
import sys

p = sys.argv[1]
s = open(p).read()
viejo = """SID=$(printf '%s' "$RAW" | jq -r '.session_id // empty' 2>/dev/null)"""
nuevo = """# Se saca con python3 y no con jq: python3 ya hace falta para el resto del
# motor, y jq no viene en todas las Macs. Una dependencia menos que explicar.
SID=$(printf '%s' "$RAW" | python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('session_id') or '')
except Exception:
    print('')
" 2>/dev/null)"""
if viejo not in s:
    print("  callar.sh: ya estaba sin jq")
    sys.exit(0)
open(p, "w").write(s.replace(viejo, nuevo))
print("  callar.sh: jq -> python3")
