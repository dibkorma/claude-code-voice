---
description: Prende o apaga que Claude te conteste hablando en ESTA sesión
allowed-tools: Bash(bash ~/.claude/hooks/voz-toggle.sh:*)
---

Argumento opcional: el nombre de esta ventana. `$ARGUMENTS`

Corre exactamente este comando (con el nombre si lo dio, sin nada si no):

```
bash ~/.claude/hooks/voz-toggle.sh $ARGUMENTS
```

La voz es POR SESION: prende solo la ventana donde corriste esto, las demas
siguen mudas. Sin nombre usa la carpeta de trabajo. El nombre sirve para
cuando hay varias ventanas hablando: Claude lo dice antes de cada frase, porque
el usuario está OYENDO y no puede ver de cual salio la voz.

El comando imprime `otras=N`: las OTRAS ventanas que tambien tienen voz.

Responde en UNA linea, sin explicar nada mas:
- `PRENDIDA nombre=X otras=0` -> "Voz prendida aqui como X — las demas mudas."
- `PRENDIDA nombre=X otras=N` -> "Voz prendida aqui como X. Hay N ventana(s) mas hablando, asi que digo el nombre antes de cada frase."
- `APAGADA otras=0`  -> "Voz apagada aqui — ninguna sesion te habla."
- `APAGADA otras=N`  -> "Voz apagada aqui. Siguen hablando N ventana(s)."

Si te pide apagar TODAS, eso es `/silencio` — corre
`bash ~/.claude/hooks/voz-silencio.sh` y responde "Voz apagada en todas las
sesiones."
