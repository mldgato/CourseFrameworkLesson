---
description: Produce el video completo para UN tema (guion, narración con ElevenLabs, animación, render). Uso: /videos X.Y.Z [con la voz Nombre]
argument-hint: X.Y.Z [voz]
---

# Skill: Producir Video (un tema a la vez)

**Argumento recibido:** `$ARGUMENTS` (el tema, p. ej. `1.1.1`, y opcionalmente una voz, p. ej. `1.1.1 con la voz Liz`). Si viene vacío, pide el tema al autor.

## Uso
```
/videos 1.1.1
```

## Regla principal
Esta skill **termina siempre con un `.mp4` generado**. No te detengas a pedir aprobaciones intermedias: escribe el guion, narra, anima y renderiza de corrido, y al final entrega el video junto con el guion y `cues.txt` para que el autor los revise. Solo te detienes si falta algo que solo el autor puede dar (la clave de ElevenLabs o Node/Python/Chrome) y, en ese caso, dile exactamente qué hacer (ver Paso 0).

## Paso 0. Preparar y verificar el entorno (siempre, antes de gastar créditos)

Usa `python` (o `python3` si `python` no existe).

```bash
python _video_kit/kit.py doctor
```

- Si falta `ffmpeg`/`ffprobe`/`venv`: ejecuta tú mismo `python _video_kit/kit.py setup` y vuelve a correr `doctor`.
- Si falta Node.js 22+, Python 3.10+ o Google Chrome: detente y dile al autor qué instalar (con el enlace de descarga).
- Si dice **`ELEVENLABS_API_KEY: NO encontrada`**: detente y dile al autor, sin pedirle la clave:
  1. Si no existe `.env` en la raíz: copiar `.env.example` a `.env` (`cp .env.example .env` en Mac/Linux, `Copy-Item .env.example .env` en PowerShell).
  2. Abrir `.env` y reemplazar `pega_aqui_tu_clave` con su clave de [elevenlabs.io](https://elevenlabs.io) → Developers → API Keys.
  3. Volver a ejecutar `/videos X.Y.Z`.

  **Nunca** le pidas pegar la clave en el chat, ni la imprimas, ni la escribas en logs, guiones o archivos distintos de `.env`. Solo se envía a `api.elevenlabs.io`.
- Si `doctor` dice "sin temas: corre /init-course": indica al autor que ejecute `/init-course` primero.

Además valida que el tema exista en `course.config.js` (unidades → lecciones → temas). Si no existe, dilo y detente.

## Paso 1. Scaffolding
```bash
python _video_kit/kit.py scaffold X.Y.Z
```
Crea `Videos/Unidad N/_fuente_X.Y.Z/` con `teoria.md` (extraída del Word de teoría si existe), `SCRIPT.md` (marcador) e `index.html` (plantilla con intro y cierre ya integrados). El logo de la intro es `LogoCurso.png` de la raíz; si no existe, usa el nombre del curso.

Si la carpeta ya tiene `narration.mp3`, **no la regeneres** (cuesta créditos): usa `scaffold --keep-narration` y `narrate --reuse`, salvo que el autor pida otra narración.

## Paso 2. Escribir el guion
Lee `teoria.md` (o, si dice que no hay Word, el PDF del examen y `course.config.js`). Escribe `SCRIPT.md` con **solo la narración** (sin encabezados `#` ni notas):
- **330–460 palabras** (2–3 min)
- Español neutro; cifras y términos técnicos en palabras ("cuatro mil quinientos")
- **Sin mencionar el examen, la certificación ni el nombre del proveedor**
- Ejemplos con el escenario de `course.config.js → scenario.name`; si inventas datos, márcalos como ilustrativos
- Etiquetas de tono de ElevenLabs v3 `[curious]`, `[warmly]`, `[softly]` al inicio de párrafos (pocas, máximo una por párrafo; no aparecen en pantalla)
- Moneda: "dólares"
- Código o siglas: léelos palabra por palabra o descríbelos; nunca deletrees símbolos

## Paso 3. Narrar (gasta créditos)
Elige la voz: la que pida el autor en `$ARGUMENTS`; si no pidió ninguna, `course.config.js → voices.default`. Acepta el **nombre** (como está en `voices.ids`) o un ID de ElevenLabs:
```bash
python _video_kit/kit.py narrate X.Y.Z --voice Jorge --voice-name Jorge
```
El comando avisa cuántos caracteres (≈ créditos) envía, transcribe el audio con ElevenLabs Scribe, genera `cues.txt` (oraciones y palabras con su segundo) y sincroniza los tiempos del `index.html`.

Errores frecuentes:
- `402 paid_plan_required`: la voz es de biblioteca y el plan es gratuito → dilo al autor (usar una voz predefinida o subir de plan).
- `401`: clave inválida → que el autor genere otra y actualice `.env`.

Revisa tú mismo `cues.txt`: que diga "dólares", que no haya leído etiquetas `[..]` y que no cambie cifras. Si la duración queda fuera de 2–3 min o una línea clave se deformó, corrige el guion y regenera **una sola vez** con `narrate X.Y.Z --force`; si vuelve a fallar, entrega el resultado con la advertencia.

## Paso 4. Componer las escenas
Crea `Videos/Unidad N/_fuente_X.Y.Z/_partes/` con tres archivos de texto:
- `css.txt`: estilos de las escenas
- `scenes.txt`: el HTML de las `<section class="scene" id="s1">…</section>` (ids `s1`…`sN`, 4–6 escenas: gancho, concepto, ejemplo con el escenario, enumeración/comparación, resumen)
- `anim.txt`: animaciones GSAP, con todo tiempo de contenido escrito como `at(t)` (t = segundo de `cues.txt`). Usa los helpers `wipe(nueva, at(t), anterior)` y `swap(salida, entrada, at(t))` de la plantilla

**Objetivo de certificación (solo visual, breve):** incluye en la escena de gancho (`s1`) o en la de resumen una etiqueta pequeña en una esquina, p. ej. `OBJETIVO {topic.id}` (con el nombre corto de la certificación si cabe), visible unos ~3–4 s (cumple "texto ≥ 2 s"), con entrada y salida suaves y sin competir con el contenido. **No se narra** ni se agrega al guion (sigue vigente "sin mencionar el examen ni la certificación" en la narración). Datos de `course.config.js`.

Reglas de diseño y de HyperFrames: lee `_video_kit/template/DESIGN.md` (fondo navy, acento único, tipografía Fraunces/JetBrains Mono, sin emojis, texto ≥ 2 s en pantalla, sin `Math.random`, sin salidas antes de un barrido, timelines síncronos).

```bash
python _video_kit/tools/assemble_scenes.py X.Y.Z
```
Debe terminar validando sin errores; si falla, corrige los archivos de `_partes/` y vuelve a ensamblar (si el `index.html` ya fue ensamblado, haz `scaffold --keep-narration` primero).

## Paso 5. Revisar y renderizar
```bash
python _video_kit/kit.py snap X.Y.Z      # fotogramas; mira snapshots/contact-sheet-*.jpg
python _video_kit/kit.py render X.Y.Z    # tarda varios minutos: ejecútalo en segundo plano
python _video_kit/tools/check_video.py X.Y.Z
```
Corrige solapes, texto fuera de cuadro o escenas transparentes que veas en `snap` antes de renderizar. `render` hace lint → validate → render → mezcla el audio completo → verifica duración y volumen → copia a `Videos/Unidad N/X.Y.Z Título.mp4` → actualiza el control. Si algo falla, el comando aborta con el motivo: corrígelo y repite.

## Paso 6. Entregar
Informa al autor:
- Ruta exacta del `.mp4` y su duración
- Voz usada y caracteres narrados (créditos gastados)
- Que pasó la verificación de `render`
- Ruta del guion (`SCRIPT.md`) para que lo revise
- Advertencias (acento de la voz, datos ilustrativos inventados, duración fuera de rango)

## Estructura del video
- Intro 3 s: logo del curso (fondo claro)
- Contenido narrado con motion graphics
- Cierre ~4.6 s: "Un curso desarrollado por" + logo de la institución

## Otros comandos útiles
```bash
python _video_kit/kit.py status          # avance por unidad
python _video_kit/kit.py next 5          # próximos temas pendientes
python _video_kit/kit.py selftest        # prueba completa sin créditos
```

## Nota
Los `.mp4` y `.mp3` **no van a git** (están en `.gitignore`), tampoco `.env` ni `_video_kit/entorno/`. Respalda los videos aparte.
