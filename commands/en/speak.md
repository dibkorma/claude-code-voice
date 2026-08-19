---
description: Turn Claude's spoken replies on or off in THIS session
allowed-tools: Bash(bash ~/.claude/hooks/voz-toggle.sh:*)
---

Optional argument: a name for this window. `$ARGUMENTS`

Run exactly this command (with the name if one was given, bare if not):

```
bash ~/.claude/hooks/voz-toggle.sh $ARGUMENTS
```

Voice is PER SESSION: this turns it on only in the window where it was run;
every other window stays silent. With no name it uses the working directory.
The name matters when several windows are speaking at once — Claude says it
before each sentence, because the user is LISTENING and can't see which window
the voice came from.

The command prints `otras=N`: how many OTHER windows also have voice on.

Answer in ONE line, nothing else:
- `PRENDIDA nombre=X otras=0` -> "Voice on here as X — every other window is silent."
- `PRENDIDA nombre=X otras=N` -> "Voice on here as X. N other window(s) are speaking, so I'll say the name before each sentence."
- `APAGADA otras=0`  -> "Voice off here — no session is talking to you."
- `APAGADA otras=N`  -> "Voice off here. N window(s) are still speaking."

If they ask to turn off ALL of them, that is `/silence` — run
`bash ~/.claude/hooks/voz-silencio.sh` and answer "Voice off in every session."
