---
description: I tell you out loud where we left off in this session and what's next
allowed-tools: Bash(bash ~/.claude/hooks/decir.sh:*)
---

The user just reopened this session and wants to pick it back up **without
reading**. Bring them up to speed.

**Pull it from this conversation**, from what you already have in context. Don't
read files or transcripts unless the conversation is empty.

Do both things, in this order:

**1. Speak the summary.** Run this command, passing the text on stdin:

```
bash ~/.claude/hooks/decir.sh <<'VOZ'
<the spoken text goes here>
VOZ
```

The spoken text:
- **About 90 words**, ~30 seconds. Not one more.
- Three parts, in flowing sentences: **what we were doing**, **what got done**,
  **what the next step is**.
- Written **for the ear**: short sentences, no code, paths, URLs, file names or
  bullets. Say "the config file", not the path.
- If something is waiting on a decision from them, say it last and be concrete.
- Same language you normally talk to them in. Direct, no preamble — lead with
  what matters.

**2. Leave the bullets on screen.** After the command, write 4-5 short bullets
with the same content — there you CAN put file names, links and details, so they
read them only if they care. Close with a **Next step** line.

Don't explain that you're summarizing. Start straight in.
