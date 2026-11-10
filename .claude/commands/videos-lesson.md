---
description: Produce un video completo por cada tema de UNA lección (guion, narración con ElevenLabs, animación, render). Uso: /videos-lesson X.Y [con la voz Nombre]
argument-hint: X.Y [voz]
---

# Skill: Producir Videos de Lección (un video por tema)

**Argumento recibido:** `$ARGUMENTS` (la lección, p. ej. `1.1`, y opcionalmente una voz, p. ej.
`1.1 con la voz Liz`). Si viene vacío, pide la lección al autor.

## Uso
```
/videos-lesson 1.1
/videos-lesson 1.1 con la voz Liz
```

## Regla principal
Este skill produce un `.mp4` por cada tema de la lección, en orden. No te detienes para pedir
aprobaciones intermedias entre temas: termina cada video completo antes de pasar al siguiente.
Solo te detienes si falta algo que solo el autor puede dar (clave de ElevenLabs, Chrome, etc.).

## Paso 0 — Preparar y verificar el entorno (una sola vez, antes del primer tema)

Usa `python` (o `python3` si `python` no existe).

```bash
python _video_kit/kit.py doctor
```

- Si falta `ffmpeg`/`ffprobe`/`venv`: ejecuta `python _video_kit/kit.py setup` y vuelve a correr `doctor`.
- Si falta Node.js 22+, Python 3.10+ o Google Chrome: detente y dile al autor qué instalar.
- Si dice **`ELEVENLABS_API_KEY: NO encontrada`**: detente y dile al autor:
  1. Si no existe `.env`: copiar `.env.example` a `.env`.
  2. Abrir `.env` y reemplazar `pega_aqui_tu_clave` con la clave de [elevenlabs.io](https://elevenlabs.io).
  3. Volver a ejecutar `/videos-lesson X.Y`.
  Nunca pedir la clave en el chat.
- Si dice "sin temas: corre /init-course": indica al autor que ejecute `/init-course` primero.

**Estilo gráfico del video:** lee `course.config.js → theme`, carga `_tools/themes.json` y localiza el objeto con ese `id`. Extrae la sección `video` del tema: `bg`, `surface`, `text`, `text2`, `accent`, `introBg`, `introGrid`, `introBar`, `fontHeading`, `fontMono`, `fontHeadingFile`, `fontMonoFile`. Aplica estos valores en todas las escenas. Si el archivo de fuente indicado en `fontHeadingFile` no existe en `_video_kit/template/assets/fonts/`, usa `fraunces.woff2` como fallback; ídem para `fontMonoFile`. Si el tema tiene `"noGrid": true`, **omite cualquier `background-image` de cuadrícula** tanto en las escenas de contenido como en las pantallas de intro y cierre — el fondo debe ser liso en todos los casos.

Lee `course.config.js` → encuentra la lección X.Y y la lista de temas. Muestra al autor:
```
Lección X.Y – [Título]
Temas a producir: X.Y.1, X.Y.2, X.Y.3 (N temas)
Voz: [Jorge / Liz / la que eligió el autor]
```

## Pasos 1–5 por cada tema (repite para X.Y.1, X.Y.2, … en orden)

Los pasos son idénticos al skill `/videos` del proyecto CourseFramework. Aplícalos a cada tema:

### Paso 1 — Scaffolding
```bash
python _video_kit/kit.py scaffold X.Y.Z
```
Si la carpeta ya tiene `narration.mp3`: usa `scaffold --keep-narration`.

### Paso 2 — Escribir el guion
Lee `teoria.md` (o el PDF si no hay Word). Escribe `SCRIPT.md`:
- **330–460 palabras** (2–3 min)
- Español neutro; cifras en palabras
- **Sin mencionar el examen, la certificación ni el nombre del proveedor**
- Ejemplos con el escenario de `course.config.js → scenario.name`
- Etiquetas de tono ElevenLabs v3 (`[curious]`, `[warmly]`, etc.): máximo una por párrafo
- Moneda: "dólares"

### Paso 3 — Narrar (gasta créditos)
```bash
python _video_kit/kit.py narrate X.Y.Z --voice [Nombre] --voice-name [Nombre]
```
Revisa `cues.txt`: que no haya leído etiquetas `[..]` y que las cifras sean correctas.
Si la duración queda fuera de 2–3 min, corrige el guion y regenera **una sola vez** con `--force`.

### Paso 4 — Componer las escenas
Crea `_partes/css.txt`, `_partes/scenes.txt`, `_partes/anim.txt`.

Incluye etiqueta visual de objetivo en la escena de gancho (`s1`) o de resumen:
`OBJETIVO {topic.id}` visible ~3–4 s, con entrada y salida suaves. **No se narra.**

Lee `_video_kit/template/DESIGN.md` antes de escribir las escenas.

```bash
python _video_kit/tools/assemble_scenes.py X.Y.Z
```

### Paso 5 — Revisar y renderizar
```bash
python _video_kit/kit.py snap X.Y.Z      # fotogramas
python _video_kit/kit.py render X.Y.Z    # render final
python _video_kit/tools/check_video.py X.Y.Z
```

## Al terminar todos los temas — Entregar resumen

Informa al autor:
```
✅ /videos-lesson X.Y completado

Videos producidos:
  X.Y.1  [Título]  →  Videos/Unidad N/X.Y.1 Título.mp4  ([duración])
  X.Y.2  [Título]  →  Videos/Unidad N/X.Y.2 Título.mp4  ([duración])
  ...

Voz: [nombre]  ·  Créditos totales gastados: ~[N] caracteres
```

Incluye advertencias si algún video tuvo duración fuera de rango o datos ilustrativos.

## Notas
- Si un tema ya tiene `narration.mp3`, no regenera el audio (cuesta créditos).
- Los `.mp4` y `.mp3` no van a git; respáldalos aparte.
- Para un solo tema usa el skill `/videos X.Y.Z` del proyecto CourseFramework.
