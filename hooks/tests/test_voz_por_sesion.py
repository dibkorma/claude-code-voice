"""Prueba: solo habla la sesion que el usuario prendio; las demas se quedan mudas.

el usuario, ago-19-2026: "que solamente se activen las sesiones que yo quiera y que
no sea una activacion global para todos... yo pudiese estar escuchando una
sesion en especifico si quiero, pero no que todas me esten hablando".

Se corre el hook Stop DE VERDAD (hablar.sh) con dos payloads de sesiones
distintas: una prendida y otra no. Nada suena: el reproductor se sustituye por
el doble de tests/ via CLAUDE_VOZ_REPRODUCTOR.

    python3 ~/.claude/hooks/tests/test_voz_por_sesion.py
"""
import json, os, pathlib, subprocess, sys, time

HOOKS = pathlib.Path(__file__).resolve().parent.parent
TESTS = HOOKS / "tests"
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, str(TESTS))

TMP = pathlib.Path(os.environ.get("VOZ_TEST_TMP", "/tmp"))
LOG = TMP / "voz-test-sesion.txt"
os.environ["VOZ_TEST_LOG"] = str(LOG)
os.environ["CLAUDE_VOZ_REPRODUCTOR"] = str(TESTS / "voz-reproducir.sh")

import voz_comun as voz
import comun; comun.blindar(voz)

# sesiones de mentira, para no pisar las de verdad
A = "ffff0001-prendida-de-prueba"      # esta SI habla
B = "ffff0002-apagada-de-prueba"       # esta NO


def correr_hook(sid, texto):
    payload = json.dumps({"session_id": sid, "last_assistant_message": texto})
    return subprocess.run(["bash", str(HOOKS / "hablar.sh")],
                          input=payload, text=True, capture_output=True,
                          env={**os.environ, "CLAUDE_CODE_SESSION_ID": sid})


def limpiar():
    voz.callar()
    for s in (A, B):
        pathlib.Path(voz.VOZ_ON_D, voz.marca_de(s)).unlink(missing_ok=True)
    LOG.unlink(missing_ok=True)


def main():
    # las ventanas que el usuario tenga prendidas se apartan: si no, ES una de las
    # ventanas de la prueba y el conteo sale mal
    restaurar = comun.aislar_sesiones(voz)
    prendidas_antes = voz.sesiones_con_voz()
    limpiar()

    pathlib.Path(voz.VOZ_ON_D).mkdir(parents=True, exist_ok=True)
    pathlib.Path(voz.VOZ_ON_D, voz.marca_de(A)).touch()   # /hablar solo en A

    correr_hook(B, "Soy la ventana que el usuario NO quiere oir.")
    correr_hook(A, "Soy la ventana que el usuario si quiere oir.")
    time.sleep(3)

    dichas = [l.strip() for l in LOG.read_text().splitlines()] if LOG.exists() else []
    print("--- lo que sono ---")
    for l in dichas:
        print("   ", l)

    fallos = []
    if not any("si quiere oir" in l for l in dichas):
        fallos.append("la sesion PRENDIDA no hablo")
    if any("NO quiere" in l for l in dichas):
        fallos.append("HABLO UNA SESION APAGADA: la voz sigue siendo global")
    # con UNA sola ventana el nombre sobra: no debe decirlo
    if any(l.startswith("INICIO") and not l.startswith("INICIO Soy la ventana")
           for l in dichas):
        fallos.append("dijo el nombre de la ventana habiendo una sola prendida")

    # con DOS ventanas hablando SI tiene que decir de cual es: el usuario esta
    # oyendo y no puede ver de donde sale la voz
    limpiar()
    pathlib.Path(voz.VOZ_ON_D, voz.marca_de(A)).write_text("MAGU")
    pathlib.Path(voz.VOZ_ON_D, voz.marca_de(B)).write_text("The Tower")
    correr_hook(A, "Ya subi los mockups a la consola.")
    time.sleep(2.5)
    con_dos = [l.strip() for l in LOG.read_text().splitlines()] if LOG.exists() else []
    print("--- con dos ventanas prendidas ---")
    for l in con_dos:
        print("   ", l)
    if not any(l.startswith("INICIO MAGU") for l in con_dos):
        fallos.append("con dos ventanas hablando no dijo de cual era la voz")

    # y el aislamiento al reves: callar en B no puede tocar lo de A
    limpiar()
    pathlib.Path(voz.VOZ_ON_D, voz.marca_de(A)).touch()
    voz.decir("Frase larga de la ventana A que no debe cortarse.", 300, sid=A)
    time.sleep(0.6)
    voz.callar(B)                       # el usuario escribe en la OTRA ventana
    time.sleep(0.4)
    sigue = [n for n in os.listdir(voz.COLA) if n.endswith(".sonando")]
    if not sigue:
        fallos.append("callar() en otra sesion corto la frase de A")

    limpiar()
    if sorted(voz.sesiones_con_voz()) != sorted(prendidas_antes):
        fallos.append("la prueba dejo sucia la lista de sesiones con voz")
    restaurar()          # devolverle sus ventanas tal como estaban

    if fallos:
        print("\nFALLA:")
        for f in fallos:
            print("  -", f)
        sys.exit(1)
    print("\nOK: solo hablo la sesion prendida, y callar en otra no la corto.")


main()
