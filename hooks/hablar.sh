#!/bin/bash
# Hook Stop: dice en voz alta la ultima respuesta de Claude.
# La logica vive en hablar.py; este wrapper solo le pasa el stdin del hook tal cual.
# Voz y velocidad:  CLAUDE_VOZ=Monica CLAUDE_VOZ_VEL=170 CLAUDE_VOZ_MAX=350
exec python3 "$HOME/.claude/hooks/hablar.py"
