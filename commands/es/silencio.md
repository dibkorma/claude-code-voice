---
description: Apaga la voz en TODAS las sesiones y corta lo que esté sonando
allowed-tools: Bash(bash ~/.claude/hooks/voz-silencio.sh)
---

Corre exactamente este comando:

```
bash ~/.claude/hooks/voz-silencio.sh
```

Es el apagón general: sirve desde cualquier ventana, apaga el interruptor de
todas las sesiones, corta la frase que esté sonando y tira la cola. Para volver
a prender una ventana en particular se usa `/hablar`.

Imprime `SILENCIO apagadas=N quedan=N sueltos=N cola=N`.

Responde en UNA linea, sin explicar nada mas:
- `apagadas=0` -> "Ya estaba todo en silencio."
- `apagadas=1` -> "Listo, silencio — apagué la única ventana que hablaba."
- `apagadas=N` (N>1) -> "Listo, silencio — apagué N ventanas."

Si `quedan` no es 0, avisa: "Ojo: quedaron N sin apagar." Nada mas.
