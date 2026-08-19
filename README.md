# Claude Code, out loud

Two slash commands and two hooks that make **Claude Code answer you in a
voice**, per session, so you can work while looking somewhere else.

*[Léeme en español](README.es.md)*

```
/speak                  ->  this window starts answering out loud
/speak MAGU             ->  ...and calls itself "MAGU" when several talk at once
/catch-me-up            ->  30 seconds of "here's where we left off"
/speak                  ->  off again
/silence                ->  every window quiet, from any window
```

It exists because of a specific way of working: many Claude Code windows open at
once, long jobs running, and a human who would rather **listen** to what came out
than read four terminals. Turning the voice on in *one* window, not all of them,
is the whole point.

---

## The two halves — only one of them is this repo

People conflate these constantly, and it costs hours. They are separate systems:

| | You talk to Claude | Claude talks to you |
|---|---|---|
| **What** | Voice dictation: your speech becomes prompt text | Spoken replies |
| **Who built it** | **Claude Code, built in.** Nothing to install | **This repo.** Doesn't exist otherwise |
| **How** | `/voice`, then hold or tap `Space` | `/speak` |
| **Cost** | Free, doesn't consume tokens | Free (edge-tts) |
| **Where the audio is made** | Anthropic's servers | Your machine |

If all you want is to *talk* to Claude, you don't need this repo — skip to
[Talking to Claude](#the-other-half-talking-to-claude-space-bar) and run `/voice`.

---

## What you get

- **Per-session voice.** `/speak` turns on the window you ran it in. Every other
  window stays silent. Ten background jobs finishing at once don't talk over each
  other.
- **The whole reply, by default.** No cap: it reads the answer out, however long
  it is. Set `CLAUDE_VOZ_MAX` to a number of characters for a shorter version —
  measured, 350 is about 19 seconds, 900 about 47. Any cut lands at the end of a
  sentence, never mid-word. (Code, paths, links and tables are stripped either
  way, so a reply full of them speaks much shorter than it looks.)
- **Written for the ear.** Code blocks, file paths, URLs, tables, markdown and
  emoji are stripped before speaking. Nobody wants `~/.config/foo/bar.py` read
  out loud, character by character.
- **It never cuts itself off.** Sentences queue and play one at a time. A
  notification from another window waits its turn instead of eating the status
  you were listening to.
- **Typing shuts it up.** The moment you send a new prompt, the voice for *that*
  session stops — which also kills the microphone echo if you dictated it.
- **Names, when it matters.** With more than one window speaking, each sentence
  starts with that window's name. You're listening; you can't see which one it was.
- **A free neural voice.** [edge-tts](https://github.com/rany2/edge-tts) —
  Microsoft Edge's voices, no account, no API key, no bill. Falls back to the OS
  voice if it isn't there or you're offline.
- **No stray audio files.** Every temp file is cleaned up, including when the
  player is killed mid-sentence.

---

## Requirements

- **Claude Code** and **python3** (both almost certainly already there)
- **macOS** — that's where it is built and tested. Linux *should* work: the
  player looks for `ffplay`/`mpv` and falls back to `espeak-ng`. Untested.
- Optional but recommended: network access the first time, to install `edge-tts`

No API keys. No accounts. Nothing paid.

---

## Install

```bash
git clone https://github.com/dibkorma/claude-code-voice.git
cd claude-code-voice
./install.sh
```

It asks one question — which language you want the slash commands in
(`en` -> `/speak`, `/catch-me-up`; `es` -> `/hablar`, `/donde-estamos`) — and
then:

1. copies the engine into `~/.claude/hooks/`
2. installs the slash commands into `~/.claude/commands/`
3. installs `edge-tts` in its own venv (skipped if you already have it anywhere)
4. writes `~/.claude/voz.conf` with a voice matching your language
5. adds its two hooks to `~/.claude/settings.json` — **additive**: it backs the
   file up first, keeps every other hook and setting, and running it twice
   changes nothing
6. runs the test suite to prove it works (nothing makes a sound)

Flags: `--lang en|es`, `--no-edge-tts`, `--voice-tap`, `--dry-run`.

Then open Claude Code — hooks are read at startup — and type `/speak`.

---

## Using it

| Command | Does |
|---|---|
| `/speak` | Toggle the voice **in this window** |
| `/speak MAGU` | Turn it on and name the window `MAGU` |
| `/catch-me-up` | Speak ~90 words of where we left off, and leave bullets on screen |
| `/silence` | Kill switch: every session off, cut what's playing, drop the queue |

Naming windows only matters when several are speaking: with two or more on, every
sentence starts with the name, so you know who is talking without looking.

`/catch-me-up` speaks **even when the voice is off** — asking for it out loud
outranks a background setting. It summarizes from the conversation it already has
in context, not by reading files, so it is fast and it is about *your* session.

`/silence` is the panic button — it works from any window, including one whose
own voice is off, and it also sweeps up any orphaned player process. Turning a
window back on is `/speak` again.

Under the hood the commands are thin wrappers over the scripts, so they work
from a plain shell too:

```bash
bash ~/.claude/hooks/voz-silencio.sh          # everything quiet
bash ~/.claude/hooks/voz-toggle.sh --estado   # is this one on? how many others?
```

---

## The other half: talking to Claude (space bar)

This is **built into Claude Code** — no install, and this repo is not involved.

```
/voice tap      then tap Space, talk, tap Space again — it sends by itself
/voice hold     hold Space while you talk, release to stop (this is the default)
/voice off      off
```

To make it stick across sessions, in `~/.claude/settings.json`:

```json
{
  "voice": { "enabled": true, "mode": "tap" },
  "language": "spanish"
}
```

Worth knowing, because each of these has cost someone an afternoon:

- **`language` drives both** the dictation language *and* the language Claude
  answers in. Leave it empty and dictation assumes English — dictate Spanish into
  it and you get mush.
- **In tap mode the first tap only records if the input line is empty**, so you
  can still type spaces normally. The second tap stops regardless.
- **Tap auto-submits at three words or more.** A stray tap won't send a word.
- Recording **stops on its own after 15 seconds of silence, or 2 minutes** total.
- The `hold space to speak` hint **does not appear if you have a custom status
  line**. The feature still works; it just doesn't advertise itself.
- It needs a **Claude.ai login** (not an API key, not Bedrock/Vertex/Foundry) and
  a **local microphone** — no SSH, no Claude Code on the web.
- Transcription **does not consume tokens** and doesn't count toward `/usage`.
- Your audio **is streamed to Anthropic's servers** for transcription. It is not
  processed locally. (The other half — Claude's voice — *is* local: edge-tts only
  fetches synthesized audio.)
- The key is rebindable: it's the `voice:pushToTalk` action, `Space` by default,
  changed in `~/.claude/keybindings.json`.

Full reference: [Voice dictation](https://code.claude.com/docs/en/voice-dictation).

**The two halves fit together on purpose:** you tap space and talk, Claude
answers out loud, and the moment you send the next prompt its voice stops so it
isn't talking into your microphone.

---

## Configuration

`~/.claude/voz.conf` (written by the installer, edit freely — read on every
sentence; an environment variable of the same name wins over the file):

```bash
CC_VOZ=en-US-AvaNeural     # edge-tts voice — list them: edge-tts --list-voices
CC_VOZ_VEL=+10%            # edge-tts rate: +20%, -10%, +0%
CLAUDE_VOZ_SAY=Samantha    # fallback macOS 'say' voice — list them: say -v '?'
CLAUDE_VOZ_VEL=215         # fallback rate, words per minute
```

Environment variables, for the rest:

| Variable | Default | What |
|---|---|---|
| `CC_EDGE_TTS` | auto | Path to `edge-tts` if it isn't on your `PATH` |
| `CC_REPRODUCTOR` | auto | Command that plays an mp3 (`afplay`, `ffplay`, `mpv`) |
| `CLAUDE_VOZ_MAX` | `0` | Characters spoken per reply. `0` = no limit, read it all |
| `CLAUDE_VOZ_MAX_RESUMEN` | `0` | Characters for `/catch-me-up`. `0` = the whole thing |
| `CLAUDE_VOZ_COLA_MAX` | `3` | How many sentences may wait their turn |
| `CLAUDE_VOZ_CADUCIDAD` | `300` | Seconds before a queued sentence is too stale to say |

Voices are picked **by ear, not by name**: generate the same sentence in a few
and listen. `en-US-AvaNeural`, `en-US-AndrewNeural`, `es-MX-DaliaNeural` and
`es-ES-ElviraNeural` are good starting points.

---

## How it works

```
                    you send a prompt              Claude finishes a reply
                            |                                |
                   UserPromptSubmit hook               Stop hook
                            |                                |
                        callar.sh                        hablar.sh
                            |                                |
              marks this session "active"              hablar.py
              kills the voice OF THIS SESSION       is this session on?  --no--> silence
                                                     (~/.claude/voz-on.d/<sid8>)
                                                             | yes
                                                    strip code/paths/markdown
                                                     strip, cut only if capped
                                                    prefix window name if >1 on
                                                             |
                                                     voz_comun.decir()
                                                        queues a file
                                                             |
                                                      voz-runner.py
                                              one flock, plays strictly in order
                                                             |
                                                   voz-reproducir.sh
                                            edge-tts -> mp3 -> afplay   (or: say)
```

Every file is short and commented with *why* it is the way it is:

| File | Job |
|---|---|
| `hooks/hablar.py` | Stop hook. Decides whether to speak, and what |
| `hooks/callar.sh` | UserPromptSubmit hook. Marks the active session, cuts its voice |
| `hooks/voz_comun.py` | Cleaning, trimming, the queue, `callar()`. The core |
| `hooks/voz-runner.py` | Plays the queue one at a time, holding a lock |
| `hooks/voz-reproducir.sh` | edge-tts -> mp3 -> player, with fallbacks and cleanup |
| `hooks/voz-toggle.sh` | `/speak`: the per-session on/off switch |
| `hooks/voz-silencio.sh` | `/silence`: the kill switch, from any window |
| `hooks/decir.py` | `/catch-me-up`: says a whole summary, even when off |
| `hooks/tests/` | 4 tests. None of them make a sound |
| `bin/sync-from-local.sh` | Pulls the engine back out of `~/.claude` into the repo |

---

## Design decisions worth stealing

Every one of these came from something breaking in real use:

- **Per session, not per machine.** A global flag meant every window the user
  touched started talking. The switch is a file per session in
  `~/.claude/voz-on.d/`, named after the session id, containing the window's name.
- **Don't filter by "kind" of session.** Filtering on environment variables like
  `CLAUDE_CODE_CHILD_SESSION` or `CLAUDE_JOB_DIR` looks reasonable and leaves you
  mute: those are set in the interactive window too. Print the variable in both
  real situations and compare before you filter on it.
- **What started playing always finishes.** `decir()` queues; only `callar()`
  interrupts, and only when the human types. Before that, every new sentence
  killed the previous one and notifications ate the status mid-word.
- **Take the text from `last_assistant_message`, not the transcript.** The
  transcript can lag, and you end up speaking the *previous* reply.
- **A hook that does `python3 - <<'EOF'` eats the stdin the hook JSON arrives on.**
  Logic goes in a `.py`; the `.sh` only `exec`s it.
- **Speak the name of the window when more than one is on.** Someone listening
  can't see which terminal a voice came from.
- **Deleting inline code leaves sentences crippled.** `say` and `/voice` should
  be read aloud; a command or a path shouldn't. Short word-like spans survive.
- **`mktemp -t voz` creates the file.** Appending `.mp3` to its name means you
  work on a *different* file and orphan the original — one per sentence, for
  months, before anyone noticed.
- **Play in the background and `wait`.** In the foreground, bash won't handle
  SIGTERM until the player exits on its own, so the cleanup trap never runs.
- **Check the process's whole command line before killing a PID.** PIDs get
  recycled; the child is `python3 …` or `bash …`, and there are hundreds of those.
- **Before naming a command, check it doesn't collide.** This one shipped as
  `/resumen` first — autocomplete swallowed it into Claude Code's own `/resume`
  and served a picker of 49 sessions instead.
- **Log every call with a reason.** `~/.claude/voz-debug.log` gets one line per
  reply saying why it stayed quiet. Every silent-voice bug is a one-minute
  diagnosis with it, and a guessing game without it.

---

## Troubleshooting

**It doesn't talk.** In order:

```bash
tail -20 ~/.claude/voz-debug.log            # one line per reply, with the reason
bash ~/.claude/hooks/voz-toggle.sh --estado # is this window even on?
bash ~/.claude/hooks/tests/correr-todas.sh  # the whole engine, silently
```

The log answers most of it: `esta sesion no tiene voz` (you didn't `/speak`
here), `no encontre mensaje de assistant`, `no quedo nada que decir tras limpiar`
(the reply was all code and paths).

**It sounds robotic** — edge-tts wasn't found, so it fell back to the OS voice:

```bash
bash -x ~/.claude/hooks/voz-reproducir.sh <(echo "test") 2>&1 | grep -i edge
```

**Hooks changed but nothing happened.** `settings.json` hooks are read at
startup. Restart Claude Code.

**It talks over itself / from the wrong window.** `voz-toggle.sh --estado` prints
`otras=N`, how many other windows are on. `--todas-no` turns all of them off.

---

## Uninstall

```bash
./uninstall.sh
```

Removes the engine, the commands, the state and its two hooks — backing up
`settings.json` first and leaving every other hook and setting, including your
native `/voice`, exactly as they were.

---

## Notes

The engine's files and comments are in Spanish (`hablar.py`, `voz_comun.py`,
`decir.py`) because that's the language it was written in. The comments are the
real documentation: each one says why that line exists, usually because something
broke. The slash commands ship in both languages.

The engine is developed live in `~/.claude/hooks`, because that is where it runs
and where it gets fixed. `./bin/sync-from-local.sh` copies it back into the repo
and re-applies what the repo does differently; `--check` just reports the diff.

Tested on macOS 14 (Apple Silicon), bash 3.2, python3 3.9, Claude Code 2.x.

MIT. Built with Claude Code, which is a strange thing to say about the thing that
gives Claude Code a voice.
