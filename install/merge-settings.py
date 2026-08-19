"""Adds this project's two hooks to ~/.claude/settings.json without touching
anything else that lives in there.

Run by install.sh. It is deliberately additive: your settings file is yours, and
a config file with a hand-written model, permissions and plugins in it is not
something an installer gets to overwrite. Every write makes a timestamped backup
first, and running it twice changes nothing the second time.

  python3 merge-settings.py [--voice-tap] [--dry-run]
  python3 merge-settings.py --remove [--dry-run]
"""
import datetime, json, os, shutil, sys

HOME = os.path.expanduser("~")
SETTINGS = os.path.join(HOME, ".claude", "settings.json")

HOOKS = [
    ("Stop", "bash ~/.claude/hooks/hablar.sh", 10),
    ("UserPromptSubmit", "bash ~/.claude/hooks/callar.sh", 3),
]

seco = "--dry-run" in sys.argv
voice_tap = "--voice-tap" in sys.argv
quitar = "--remove" in sys.argv


def cargar():
    if not os.path.exists(SETTINGS):
        return {}
    with open(SETTINGS) as f:
        texto = f.read().strip()
    if not texto:
        return {}
    return json.loads(texto)          # si esta roto, mejor reventar que pisarlo


def ya_esta(evento, cfg, aguja):
    """True si ese comando ya esta enganchado a ese evento, sea como sea que lo
    hayas escrito (ruta absoluta, ~, con o sin bash delante)."""
    for grupo in cfg.get("hooks", {}).get(evento, []):
        for h in grupo.get("hooks", []):
            if aguja in str(h.get("command", "")):
                return True
    return False


def main():
    try:
        cfg = cargar()
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: {SETTINGS} is not valid JSON ({e}). Fix it first — "
                 f"I will not overwrite a broken settings file.")

    cambios = []
    cfg.setdefault("hooks", {})

    if quitar:
        for evento, comando, _ in HOOKS:
            aguja = comando.split("/")[-1]
            grupos = cfg["hooks"].get(evento, [])
            quedan = []
            for grupo in grupos:
                hs = [h for h in grupo.get("hooks", [])
                      if aguja not in str(h.get("command", ""))]
                if len(hs) != len(grupo.get("hooks", [])):
                    cambios.append(f"{evento} -> {aguja}")
                    print(f"  - {evento}: {aguja} unhooked")
                # un grupo que se quedo sin hooks se va; otro con hooks ajenos se queda
                if hs:
                    quedan.append({**grupo, "hooks": hs})
            if quedan:
                cfg["hooks"][evento] = quedan
            elif evento in cfg["hooks"]:
                del cfg["hooks"][evento]
        # la clave `voice` NO se toca: es del dictado nativo de Claude Code y
        # puede haber estado ahi mucho antes que esto.
        escribir(cfg, cambios)
        return

    for evento, comando, timeout in HOOKS:
        aguja = comando.split("/")[-1]          # hablar.sh / callar.sh
        if ya_esta(evento, cfg, aguja):
            print(f"  = {evento}: {aguja} already hooked up, leaving it alone")
            continue
        cfg["hooks"].setdefault(evento, []).append(
            {"hooks": [{"type": "command", "command": comando, "timeout": timeout}]})
        cambios.append(f"{evento} -> {aguja}")
        print(f"  + {evento}: {aguja}")

    if voice_tap:
        voz = cfg.get("voice") or {}
        if voz.get("enabled") is True and voz.get("mode") == "tap":
            print("  = voice: already on in tap mode")
        else:
            cfg["voice"] = {**voz, "enabled": True, "mode": "tap"}
            cambios.append("voice: tap")
            print("  + voice: enabled, mode=tap  (native /voice — tap space to talk)")

    escribir(cfg, cambios)


def escribir(cfg, cambios):
    if not cambios:
        print("  nothing to change — settings.json is already how it should be")
        return

    if seco:
        print("\n--dry-run: nothing was written. This is what it would look like:\n")
        print(json.dumps(cfg, indent=2, ensure_ascii=False))
        return

    if os.path.exists(SETTINGS):
        sello = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        copia = f"{SETTINGS}.bak-{sello}"
        shutil.copy2(SETTINGS, copia)
        print(f"  backup: {copia}")

    os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
    with open(SETTINGS, "w") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  written: {SETTINGS}")


main()
