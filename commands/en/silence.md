---
description: Turn the voice off in EVERY session and cut whatever is playing
allowed-tools: Bash(bash ~/.claude/hooks/voz-silencio.sh)
---

Run exactly this command:

```
bash ~/.claude/hooks/voz-silencio.sh
```

This is the kill switch: it works from any window, turns the switch off for
every session, cuts the sentence that is playing and drops the queue. To turn a
particular window back on, use `/speak`.

It prints `SILENCIO apagadas=N quedan=N sueltos=N cola=N`.

Answer in ONE line, nothing else:
- `apagadas=0` -> "Everything was already quiet."
- `apagadas=1` -> "Silence — turned off the one window that was talking."
- `apagadas=N` (N>1) -> "Silence — turned off N windows."

If `quedan` is not 0, add: "Heads up: N were left on." Nothing more.
