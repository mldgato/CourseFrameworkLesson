---
description: Produce un video con pausas de evaluación (H5P) y el Word con las preguntas por cada tema de UNA lección. Uso: /videos-eval-lesson X.Y [con la voz Nombre]
argument-hint: X.Y [voz]
---

# Skill: Producir Videos con Pausas de Evaluación (lección completa)

**Argumento recibido:** `$ARGUMENTS` (la lección, p. ej. `1.1`, y opcionalmente una voz, p. ej.
`1.1 con la voz Liz`). Si viene vacío, pide la lección al autor.

## Uso
```
/videos-eval-lesson 1.1
/videos-eval-lesson 1.1 con la voz Liz
```

## Qué produce (por cada tema X.Y.Z de la lección)
1. **`Videos/Unidad N/X.Y.Z Título.mp4`** — video con cues orales de pausa de evaluación a
   mitad del contenido y al final.
2. **`Videos/Unidad N/X.Y.Z Título — Evaluación Interactiva.docx`** — Word con las dos preguntas
   de opción múltiple (una por pausa), listo para configurar H5P Interactive Video.

## Regla principal
Termina un tema completo (MP4 + DOCX) antes de pasar al siguiente. No te detengas para pedir
aprobaciones intermedias entre temas. Solo te detienes si falta algo que solo el autor puede dar.

---

## Paso 0 — Preparar entorno (una sola vez)

```bash
python _video_kit/kit.py doctor
```

Aplica exactamente las mismas reglas de `/videos` para manejar dependencias faltantes,
`ELEVENLABS_API_KEY` ausente y temas inexistentes en `course.config.js`.

Lee `course.config.js` → encuentra la lección X.Y y la lista de temas. Muestra al autor:
```
Lección X.Y – [Título]
Temas a producir: X.Y.1, X.Y.2, X.Y.3 (N temas)
Voz: [Jorge / Liz / la que eligió el autor]
Modo: Video con pausas de evaluación (H5P)
```

**Estilo gráfico:** lee `course.config.js → theme`, carga `_tools/themes.json` y localiza el
objeto con ese `id`. Extrae la sección `video`. Si `noGrid: true`, omite cuadrículas en todo.
Si el archivo de fuente no existe en `_video_kit/template/assets/fonts/`, usa el fallback.

---

## Pasos 1–6 por cada tema (repite para X.Y.1, X.Y.2, … en orden)

Los pasos son idénticos al skill `/videos-eval X.Y.Z` del proyecto CourseFramework.
Aplícalos a cada tema de la lección:

### Paso 1 — Scaffolding
```bash
python _video_kit/kit.py scaffold X.Y.Z
```
Si ya hay `narration.mp3`: usa `--keep-narration`.

### Paso 2 — Escribir el guion con pausas de evaluación
Lee `teoria.md` (o el PDF si no hay Word). Escribe `SCRIPT.md`:
- **350–480 palabras**
- Español neutro; cifras en palabras
- **Sin mencionar el examen, la certificación ni el nombre del proveedor**
- Ejemplos con el escenario de `course.config.js → scenario.name`
- Etiquetas ElevenLabs v3 (máximo una por párrafo)

**Estructura con pausas:**
1. **Bloque A** (~40–50%) — 1–2 conceptos clave
2. **Cue de pausa 1** (en quiebre narrativo natural):
   > "Hagamos una pausa aquí para evaluar lo que hemos visto hasta este punto."
   Marcador: `<!-- PAUSA-1 -->`
3. **Bloque B** (~40–50%) — conceptos siguientes + cierre
4. **Cue de pausa 2** (antes de la última oración):
   > "Antes de terminar, una última pregunta para consolidar lo aprendido."
   Marcador: `<!-- PAUSA-2 -->`
5. **Cierre final:** una sola oración de remate

### Paso 3 — Narrar (gasta créditos)
```bash
python _video_kit/kit.py narrate X.Y.Z --voice [Nombre] --voice-name [Nombre]
```
Revisa `cues.txt`: verifica que las frases de las cues de pausa aparecen con sus tiempos.
Anota **t_pausa1** y **t_pausa2** — los usarás en los Pasos 4 y 6.
Si la duración queda fuera de 2–3 min, corrige el guion y regenera **una sola vez** con
`--force`.

### Paso 4 — Componer las escenas
Crea `_partes/css.txt`, `_partes/scenes.txt`, `_partes/anim.txt`.

Incluye etiqueta visual de objetivo: `OBJETIVO {topic.id}` en la escena de gancho o de resumen,
visible ~3–4 s, con entrada y salida suaves. **No se narra.**

En cada punto de pausa, puedes incluir una escena breve (~2 s) con fondo `{video.surface}` y
texto `⏸ PAUSA DE EVALUACIÓN` en `{video.accent}` para facilitar al autor encontrar el
timestamp exacto en el video. Si complica el ensamblaje, omítela.

Lee `_video_kit/template/DESIGN.md` antes de escribir las escenas.

```bash
python _video_kit/tools/assemble_scenes.py X.Y.Z
```

### Paso 5 — Revisar y renderizar
```bash
python _video_kit/kit.py snap X.Y.Z
python _video_kit/kit.py render X.Y.Z
python _video_kit/tools/check_video.py X.Y.Z
```

### Paso 6 — Generar el Word de preguntas de evaluación

Con **t_pausa1** y **t_pausa2** conocidos, genera `X.Y.Z Título — Evaluación Interactiva.docx`
en `Videos/Unidad N/` usando `python-docx`.

**Estructura del documento:**
- Cabecera: `Preguntas de Evaluación — Video Interactivo`, tema y curso
- Recuadro de trazabilidad: `Objetivo {certification} · {topic.id} {topic.title}
  (Objetivo {lesson.id}: {lesson.objective})`
- Instrucciones breves para H5P (timestamps de las dos pausas)

**Pregunta 1 — Pausa a mitad del video**
- Timestamp: `{t_pausa1}`
- Contenido evaluado: breve descripción del Bloque A
- Enunciado + 4 opciones (una correcta) + respuesta correcta + retroalimentación (1 oración)

**Pregunta 2 — Pausa al final del video**
- Timestamp: `{t_pausa2}`
- Contenido evaluado: Bloque B o video completo
- Enunciado + 4 opciones (una correcta) + respuesta correcta + retroalimentación (1 oración)

**Reglas para las preguntas:**
- Siempre opción múltiple, 4 opciones, una sola correcta
- Estilo coherente con la certificación objetivo
- Sin mencionar el examen ni la certificación en el enunciado
- Si existe `certificación/preguntas_por_tema.json` para X.Y.Z, úsalo como referencia de nivel
  de dificultad (no copiar preguntas del banco)
- Marca la respuesta correcta con negrita en el documento

---

## Al terminar todos los temas — Entregar resumen

```
✅ /videos-eval-lesson X.Y completado

Videos con evaluación producidos:
  X.Y.1  [Título]  →  MP4 ([duración])  +  DOCX (Pausa 1: MM:SS · Pausa 2: MM:SS)
  X.Y.2  [Título]  →  MP4 ([duración])  +  DOCX (Pausa 1: MM:SS · Pausa 2: MM:SS)
  ...

Voz: [nombre]  ·  Créditos totales gastados: ~[N] caracteres
```

**Instrucciones H5P para el autor (una sola vez al final):**
> Para activar la evaluación interactiva en cada video:
> 1. Abre el editor H5P Interactive Video (Moodle, WordPress, Lumi o h5p-standalone).
> 2. Importa el `.mp4` del tema como fuente del video.
> 3. Agrega una interacción tipo **Single Choice Set** o **Multiple Choice** en la Pausa 1
>    → activa "Pausar video".
> 4. Repite en la Pausa 2.
> 5. Usa los enunciados, opciones y retroalimentación del `.docx` generado para ese tema.

## Notas
- Si un tema ya tiene `narration.mp3`, no regenera el audio (cuesta créditos).
- Los `.mp4` y `.mp3` no van a git; respaldarlos aparte.
- Los `.docx` de evaluación **sí van a git** (son contenido del curso).
- Para un solo tema usa `/videos-eval X.Y.Z` del proyecto CourseFramework.
