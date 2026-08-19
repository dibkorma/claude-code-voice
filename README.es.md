# Claude Code, en voz alta

Dos comandos y dos hooks para que **Claude Code te conteste hablando**, ventana
por ventana, y puedas trabajar mirando otra cosa.

*[Read me in English](README.md)*

```
/hablar                 ->  esta ventana empieza a contestarte hablando
/hablar MAGU            ->  ...y se llama "MAGU" cuando hay varias hablando
/donde-estamos          ->  30 segundos de "dónde quedamos"
/hablar                 ->  apagada otra vez
/silencio               ->  todas mudas, desde cualquier ventana
```

Nació de una forma concreta de trabajar: muchas ventanas de Claude Code abiertas
a la vez, trabajos largos corriendo, y alguien que prefiere **oír** lo que salió
antes que leer cuatro terminales. Que la voz se prenda en *una* ventana y no en
todas es justamente el punto.

---

## Son dos mitades — y solo una es este repo

La gente las confunde todo el tiempo, y eso cuesta horas. Son sistemas
separados:

| | Tú le hablas a Claude | Claude te habla a ti |
|---|---|---|
| **Qué es** | Dictado: tu voz se vuelve texto del prompt | Respuestas habladas |
| **Quién lo hizo** | **Claude Code, viene incluido.** No se instala nada | **Este repo.** Si no, no existe |
| **Cómo** | `/voice`, y sostienes o tocas `Espacio` | `/hablar` |
| **Costo** | Gratis, no gasta tokens | Gratis (edge-tts) |
| **Dónde se hace el audio** | En los servidores de Anthropic | En tu máquina |

Si lo único que quieres es *hablarle* a Claude, no necesitas este repo: brinca a
[Hablarle tú a Claude](#la-otra-mitad-hablarle-t%C3%BA-a-claude-la-barra-de-espacio)
y corre `/voice`.

---

## Qué hace

- **Voz por sesión.** `/hablar` prende la ventana donde lo corriste. Las demás
  siguen mudas. Diez trabajos de fondo terminando juntos no te hablan encima.
- **Lo que quieras oír.** El hook Stop dice los primeros ~900 caracteres — unos
  47 segundos — siempre cortando al final de una oración, nunca a media palabra.
  Con `CLAUDE_VOZ_MAX=350` te da solo el titular; con `0` te lee todo.
- **Escrito para el oído.** Antes de hablar quita bloques de código, rutas, URLs,
  tablas, markdown y emojis. Nadie quiere oír `~/.config/foo/bar.py` deletreado.
- **Nunca se corta a sí mismo.** Las frases hacen cola y suenan una por una. El
  aviso de otra ventana espera su turno en vez de comerse el status que estabas
  oyendo.
- **Escribir lo calla.** En cuanto mandas un mensaje nuevo, la voz *de esa
  sesión* se detiene — lo que además mata el eco del micrófono si dictaste.
- **Nombres, cuando hacen falta.** Con más de una ventana hablando, cada frase
  arranca con el nombre de la suya. Estás oyendo: no puedes ver de cuál salió.
- **Voz neuronal gratis.** [edge-tts](https://github.com/rany2/edge-tts) — las
  voces de Microsoft Edge, sin cuenta, sin llave, sin factura. Si no está o no
  hay red, cae a la voz del sistema.
- **No deja archivos de audio tirados.** Todo temporal se limpia, también si
  matan al reproductor a media frase.

---

## Qué hace falta

- **Claude Code** y **python3** (los dos ya los tienes, casi seguro)
- **macOS** — es donde está hecho y probado. En Linux *debería* correr: el
  reproductor busca `ffplay`/`mpv` y cae a `espeak-ng`. Sin probar.
- Opcional pero recomendado: internet la primera vez, para instalar `edge-tts`

Sin llaves de API. Sin cuentas. Nada pago.

---

## Instalación

```bash
git clone https://github.com/dibkorma/claude-code-voice.git
cd claude-code-voice
./install.sh
```

Te hace una sola pregunta — en qué idioma quieres los comandos (`es` ->
`/hablar`, `/donde-estamos`; `en` -> `/speak`, `/catch-me-up`) — y después:

1. copia el motor a `~/.claude/hooks/`
2. instala los comandos en `~/.claude/commands/`
3. instala `edge-tts` en su propio venv (se lo salta si ya lo tienes en algún lado)
4. escribe `~/.claude/voz.conf` con una voz acorde a tu idioma
5. agrega sus dos hooks a `~/.claude/settings.json` — **sin pisar nada**: hace
   respaldo antes, respeta todos tus otros hooks y ajustes, y correrlo dos veces
   no cambia nada
6. corre las pruebas para demostrar que funciona (no suena nada)

Banderas: `--lang es|en`, `--no-edge-tts`, `--voice-tap`, `--dry-run`.

Después abre Claude Code — los hooks se leen al arrancar — y escribe `/hablar`.

---

## Cómo se usa

| Comando | Qué hace |
|---|---|
| `/hablar` | Prende o apaga la voz **en esta ventana** |
| `/hablar MAGU` | La prende y le pone `MAGU` de nombre a la ventana |
| `/donde-estamos` | Te habla ~90 palabras de dónde quedaste y deja viñetas en pantalla |
| `/silencio` | Apagón general: todas las sesiones, corta lo que suena y tira la cola |

Ponerle nombre a la ventana solo importa cuando hay varias hablando: con dos o
más prendidas, cada frase arranca diciendo el nombre, para que sepas quién te
habla sin mirar.

`/donde-estamos` habla **aunque la voz esté apagada** — pedirlo expreso pesa más
que el ajuste de fondo. Resume de la conversación que ya tiene en contexto, no
leyendo archivos: por eso es rápido y va de *tu* sesión.

`/silencio` es el botón de pánico: sirve desde cualquier ventana, incluso una
que tenga su propia voz apagada, y además barre cualquier reproductor que se
haya quedado suelto. Para volver a prender una ventana, `/hablar`.

Por dentro los comandos son envoltorios finitos de los scripts, así que también
sirven desde una terminal normal:

```bash
bash ~/.claude/hooks/voz-silencio.sh          # todo en silencio
bash ~/.claude/hooks/voz-toggle.sh --estado   # ¿esta está prendida? ¿cuántas otras?
```

---

## La otra mitad: hablarle tú a Claude (la barra de espacio)

Esto **viene con Claude Code**. No se instala nada y este repo no participa.

```
/voice tap      tocas Espacio, hablas, tocas Espacio otra vez — se manda solo
/voice hold     sostienes Espacio mientras hablas, sueltas y para (es el default)
/voice off      apagado
```

Para que quede prendido entre sesiones, en `~/.claude/settings.json`:

```json
{
  "voice": { "enabled": true, "mode": "tap" },
  "language": "spanish"
}
```

Vale la pena saber esto, porque cada punto le ha costado una tarde a alguien:

- **`language` manda las dos cosas**: el idioma del dictado *y* el idioma en que
  Claude te contesta. Si la dejas vacía, el dictado asume inglés — le hablas en
  español y te devuelve puré.
- **En modo tap el primer toque solo graba si la línea está vacía**, para que
  puedas seguir escribiendo espacios normal. El segundo toque para siempre.
- **Tap manda solo a partir de tres palabras.** Un toque accidental no envía nada.
- La grabación **se corta sola a los 15 segundos de silencio, o a los 2 minutos**.
- El aviso `hold space to speak` **no aparece si tienes tu propia statusLine**.
  La función igual sirve; simplemente no se anuncia.
- Necesita **cuenta de Claude.ai** (no llave de API, ni Bedrock/Vertex/Foundry) y
  **micrófono local** — no sirve por SSH ni en Claude Code web.
- La transcripción **no gasta tokens** ni cuenta contra `/usage`.
- Tu audio **se manda a los servidores de Anthropic** para transcribirlo; no se
  procesa local. (La otra mitad — la voz de Claude — sí es local: edge-tts solo
  baja el audio ya sintetizado.)
- La tecla se puede cambiar: la acción es `voice:pushToTalk`, `Espacio` por
  defecto, y se reasigna en `~/.claude/keybindings.json`.

Referencia completa: [Voice dictation](https://code.claude.com/docs/en/voice-dictation).

**Las dos mitades encajan a propósito:** tocas espacio y hablas, Claude te
contesta en voz alta, y en cuanto mandas el siguiente mensaje su voz se calla
para no estar hablándole a tu micrófono.

---

## Configuración

`~/.claude/voz.conf` (lo escribe el instalador; edítalo sin miedo, se lee en
cada frase — una variable de entorno con el mismo nombre le gana al archivo):

```bash
CC_VOZ=es-MX-DaliaNeural   # voz de edge-tts — lista: edge-tts --list-voices
CC_VOZ_VEL=+20%            # velocidad de edge-tts: +20%, -10%, +0%
CLAUDE_VOZ_SAY=Paulina     # voz de respaldo del `say` de macOS — lista: say -v '?'
CLAUDE_VOZ_VEL=215         # velocidad del respaldo, palabras por minuto
```

Variables de entorno, para el resto:

| Variable | Default | Qué |
|---|---|---|
| `CC_EDGE_TTS` | auto | Ruta a `edge-tts` si no está en el `PATH` |
| `CC_REPRODUCTOR` | auto | Comando que reproduce un mp3 (`afplay`, `ffplay`, `mpv`) |
| `CLAUDE_VOZ_MAX` | `900` | Caracteres por respuesta (~47s). `0` = sin límite |
| `CLAUDE_VOZ_MAX_RESUMEN` | `1200` | Caracteres para `/donde-estamos` |
| `CLAUDE_VOZ_COLA_MAX` | `3` | Cuántas frases pueden esperar turno |
| `CLAUDE_VOZ_CADUCIDAD` | `300` | Segundos antes de que una frase en cola quede rancia |

Las voces se eligen **oyendo, no leyendo**: genera la misma frase en varias y
escúchalas. `es-MX-DaliaNeural`, `es-ES-ElviraNeural`, `en-US-AvaNeural` y
`en-US-AndrewNeural` son buenos puntos de partida.

---

## Cómo funciona

```
                  mandas un mensaje                Claude termina de responder
                          |                                    |
                 hook UserPromptSubmit                     hook Stop
                          |                                    |
                      callar.sh                            hablar.sh
                          |                                    |
           marca esta sesión como "activa"                 hablar.py
           corta la voz DE ESTA SESIÓN            ¿esta sesión está prendida? --no--> silencio
                                                   (~/.claude/voz-on.d/<sid8>)
                                                           | sí
                                                  quita código, rutas, markdown
                                                  corta en 900, al fin de oración
                                                  antepone el nombre si hay >1
                                                           |
                                                   voz_comun.decir()
                                                     encola un archivo
                                                           |
                                                    voz-runner.py
                                            un flock, reproduce en orden estricto
                                                           |
                                                 voz-reproducir.sh
                                          edge-tts -> mp3 -> afplay   (o: say)
```

Cada archivo es corto y está comentado con el *porqué*:

| Archivo | Trabajo |
|---|---|
| `hooks/hablar.py` | Hook Stop. Decide si habla, y qué |
| `hooks/callar.sh` | Hook UserPromptSubmit. Marca la sesión activa y corta su voz |
| `hooks/voz_comun.py` | Limpieza, recorte, la cola, `callar()`. El corazón |
| `hooks/voz-runner.py` | Reproduce la cola uno por uno, con un lock |
| `hooks/voz-reproducir.sh` | edge-tts -> mp3 -> reproductor, con respaldos y limpieza |
| `hooks/voz-toggle.sh` | `/hablar`: el interruptor por sesión |
| `hooks/voz-silencio.sh` | `/silencio`: el apagón general, desde cualquier ventana |
| `hooks/decir.py` | `/donde-estamos`: dice un resumen entero, aunque esté apagada |
| `hooks/tests/` | 4 pruebas. Ninguna suena |
| `bin/sync-from-local.sh` | Trae el motor de vuelta de `~/.claude` al repo |

---

## Decisiones que vale la pena copiarse

Cada una salió de algo que se rompió usándolo de verdad:

- **Por sesión, no por máquina.** Con una bandera global, cualquier ventana que
  tocaras empezaba a hablar. El interruptor es un archivo por sesión en
  `~/.claude/voz-on.d/`, nombrado con el id de la sesión y con el nombre adentro.
- **No filtres por "tipo" de sesión.** Filtrar por variables de entorno como
  `CLAUDE_CODE_CHILD_SESSION` o `CLAUDE_JOB_DIR` suena razonable y te deja mudo:
  también están puestas en la ventana interactiva. Imprime la variable en las dos
  situaciones reales y compáralas antes de filtrar por ella.
- **Lo que empezó a sonar siempre termina.** `decir()` encola; lo único que
  interrumpe es `callar()`, y solo cuando el humano escribe. Antes, cada frase
  nueva mataba a la anterior y los avisos se comían el status a media palabra.
- **El texto sale de `last_assistant_message`, no del transcript.** El transcript
  puede ir retrasado y terminas hablando la respuesta *anterior*.
- **Un hook que hace `python3 - <<'EOF'` se come el stdin por donde llega el JSON
  del hook.** La lógica va en un `.py`; el `.sh` solo hace `exec`.
- **Di el nombre de la ventana cuando hay más de una.** Quien está oyendo no
  puede ver de qué terminal salió la voz.
- **Borrar el código inline deja la frase coja.** `say` y `/voice` hay que
  leerlos; un comando o una ruta, no. Sobreviven los tramos cortos que parecen
  palabra.
- **`mktemp -t voz` CREA el archivo.** Pegarle `.mp3` al nombre significa que
  trabajas sobre otro y dejas el original huérfano — uno por frase, durante
  meses, hasta que alguien lo notó.
- **Reproduce en segundo plano y haz `wait`.** En primer plano bash no atiende el
  SIGTERM hasta que el reproductor termine solo, y la limpieza nunca corre.
- **Revisa la línea de comando completa antes de matar un PID.** Los PID se
  reciclan; el hijo es `python3 …` o `bash …`, y de esos hay cientos.
- **Antes de bautizar un comando, verifica que no choque.** Este salió primero
  como `/resumen`: el autocompletado se lo comió con el `/resume` propio de
  Claude Code y servía un selector de 49 sesiones.
- **Registra cada llamada con su razón.** `~/.claude/voz-debug.log` recibe una
  línea por respuesta diciendo por qué se calló. Con eso, cualquier bug de "no
  habla" se diagnostica en un minuto; sin eso, es adivinanza.

---

## Cuando algo falla

**No habla.** En este orden:

```bash
tail -20 ~/.claude/voz-debug.log            # una línea por respuesta, con la razón
bash ~/.claude/hooks/voz-toggle.sh --estado # ¿esta ventana está prendida?
bash ~/.claude/hooks/tests/correr-todas.sh  # el motor completo, en silencio
```

El log responde casi todo: `esta sesion no tiene voz` (no corriste `/hablar`
aquí), `no encontre mensaje de assistant`, `no quedo nada que decir tras limpiar`
(la respuesta era pura ruta y código).

**Suena robótico** — no encontró edge-tts y cayó a la voz del sistema:

```bash
bash -x ~/.claude/hooks/voz-reproducir.sh <(echo "prueba") 2>&1 | grep -i edge
```

**Cambiaste los hooks y no pasó nada.** Los hooks del `settings.json` se leen al
arrancar. Reinicia Claude Code.

**Habla encima o desde la ventana equivocada.** `voz-toggle.sh --estado` imprime
`otras=N`, cuántas otras ventanas están prendidas. `--todas-no` las apaga todas.

---

## Desinstalar

```bash
./uninstall.sh
```

Saca el motor, los comandos, el estado y sus dos hooks — con respaldo del
`settings.json` primero, y dejando todos tus otros hooks y ajustes (incluido tu
`/voice` nativo) exactamente como estaban.

---

## Notas

Los archivos y comentarios del motor están en español (`hablar.py`,
`voz_comun.py`, `decir.py`) porque en ese idioma se escribió. Los comentarios son
la documentación de verdad: cada uno dice por qué existe esa línea, casi siempre
porque algo se rompió. Los comandos vienen en los dos idiomas.

El motor se desarrolla en vivo en `~/.claude/hooks`, que es donde corre y donde
se arregla. `./bin/sync-from-local.sh` lo trae de vuelta al repo y re-aplica lo
que el repo hace distinto; con `--check` solo te dice qué difiere.

Probado en macOS 14 (Apple Silicon), bash 3.2, python3 3.9, Claude Code 2.x.

MIT. Hecho con Claude Code, que es una cosa rara que decir de lo que le da voz a
Claude Code.
