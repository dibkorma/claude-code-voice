#!/bin/bash
# Dice un texto en voz alta, completo. Texto por stdin o como argumento.
exec python3 "$HOME/.claude/hooks/decir.py" "$@"
