---
description: Te cuento hablando dónde quedamos en esta sesión y qué sigue
allowed-tools: Bash(bash ~/.claude/hooks/decir.sh:*)
---

El usuario acaba de reabrir esta sesión y quiere retomar **sin leer**. Ponlo al día.

**Sácalo de esta conversación**, de lo que ya tienes en contexto. No leas
archivos ni transcripts salvo que la conversación esté vacía.

Haz las dos cosas, en este orden:

**1. Habla el resumen.** Corre este comando pasándole el texto por stdin:

```
bash ~/.claude/hooks/decir.sh <<'VOZ'
<aquí el texto hablado>
VOZ
```

El texto hablado va así:
- **Unas 90 palabras**, ~30 segundos. Ni una más.
- Tres partes, en frases corridas: **en qué estábamos**, **qué quedó hecho**,
  **cuál es el próximo paso**.
- Escrito **para el oído**: frases cortas, nada de código, rutas, URLs, nombres
  de archivo ni viñetas. Di "el archivo de configuración", no la ruta.
- Si algo está esperando por una decisión suya, dilo al final y sé concreto.
- Habla en el mismo idioma en que conversas con él normalmente. Directo, sin
  preámbulo: arranca por lo que importa.

**2. Deja las viñetas en pantalla.** Después del comando, escribe 4-5 viñetas
cortas con el mismo contenido — ahí SÍ puedes poner nombres de archivo, links y
detalles, para que los lea solo si le interesan. Cierra con una línea de
**Próximo paso**.

No expliques que estás resumiendo. Arranca directo.
