# CourseFrameworkLesson

Framework para crear cursos de certificación **generando una lección completa de una sola vez**.
Se parte del PDF oficial del examen; Claude (Claude Code) genera, **lección por lección**, la teoría,
las preguntas, todas las actividades interactivas y todos los fragmentos HTML.

> **Diferencia clave con CourseFramework:** en este proyecto los skills trabajan a nivel de lección
> (`/word-lesson 1.1`) en lugar de tema por tema (`/word-content 1.1.1`). Ideal cuando el autor
> quiere revisar una lección completa de una sola vez en lugar de ir tema por tema.

```
PDF del examen ─ /init-course ─► course.config.js (unidades → lecciones → temas) + carpetas
                                         │
          Capturas del simulador         │  por cada lección X.Y
      certificación/Variante N/*.png     ▼
           └── /exam-import ──►  preguntas_por_tema.json (alimenta los skills siguientes)
                                         │
                                         ▼
 /word-lesson → /questions-lesson → /activities-lesson → /html-lesson → (/videos-lesson | /videos-eval-lesson)
```

## Requisitos

| Qué | Para qué | Obligatorio |
|-----|----------|-------------|
| [Claude Code](https://claude.com/claude-code) | Ejecutar los comandos | Sí |
| Node.js 18+ | Generar Word y probar actividades | Sí |
| Python 3.9+ | Leer el PDF (`pymupdf`), convertir Word a HTML y generar Excel (`openpyxl`) | Sí |
| Google Chrome | Renderizar los videos | Solo para `/videos-lesson` y `/videos-eval-lesson` |
| Cuenta de ElevenLabs + clave API (`.env`) | Voz de los videos | Solo para `/videos-lesson` y `/videos-eval-lesson` |

Funciona en Windows, Mac y Linux.

## Puesta en marcha (primera vez)

1. **Abrir una terminal en la carpeta del proyecto**.
2. **Instalar dependencias** (un solo comando):
   ```
   node setup.js
   ```
   Instala `pymupdf` y `openpyxl` (Python), las librerías de `_tools/` (Node), el kit de videos
   y crea el archivo `.env` si no existe.
3. **Revisar `course.config.js`**: nombre, certificación, paleta y voces.
4. **Abrir Claude Code en esta carpeta**:
   ```
   claude
   ```
5. **Inicializar el curso** (una sola vez):
   ```
   /init-course
   ```
   Lee el PDF del examen, llena `units` en `course.config.js`, crea las carpetas `Unidad N - …/`
   y propone un escenario. Confirma o cambia el escenario antes de continuar.

## Importar preguntas del examen real (`/exam-import`)

Opcional pero recomendado antes de generar contenido. Alinea automáticamente el enfoque de cada
skill con las preguntas reales del examen.

1. Crea `certificación/` en la raíz.
2. Dentro, crea una subcarpeta con cualquier nombre (ej. `Variante 1`).
3. Coloca las capturas del simulador (`.png` / `.jpg`).

**Convención de nombres:**

| Nombre | Significa |
|--------|-----------|
| `1.png`, `2.png` | Pregunta 1, pregunta 2 (imagen única) |
| `8.1.png`, `8.2.png` | Pregunta 8, partes 1 y 2 (una sola pregunta multi-imagen) |

```
/exam-import
```

Genera `Banco de Preguntas.docx`, `Cobertura de Objetivos.xlsx` y `preguntas_por_tema.json`.
Para agregar más variantes después: añade subcarpeta y vuelve a ejecutar `/exam-import`.

## Producción por lección

Los números son el ID de la lección en `course.config.js` (unidad.lección). Revisa el resultado
de cada skill antes de pasar al siguiente.

| Comando | Resultado | Carpeta de salida |
|---------|-----------|-------------------|
| `/word-lesson 1.1` | Word de teoría completo de la lección (todos los temas + resumen) | `Unidad N - …/Teoría/` |
| `/questions-lesson 1.1` | Word de preguntas de evaluación (todos los temas) | `…/Preguntas/` |
| `/activities-lesson 1.1` | Todas las actividades HTML interactivas de la lección | `…/Actividades/` |
| `/html-lesson 1.1` | Todos los fragmentos HTML del ebook de la lección | `…/Contenido HTML/` |
| `/videos-lesson 1.1` | Un video por cada tema de la lección (ElevenLabs) | `Videos/Unidad N/` |
| `/videos-eval-lesson 1.1` | Un video con pausas de evaluación H5P + Word con 2 preguntas por cada tema (solo si lo pides) | `Videos/Unidad N/` |

> Si ya ejecutaste `/exam-import`, los skills leen automáticamente las preguntas del examen para
> cada tema y alinean el enfoque del contenido.

## Videos con voces de ElevenLabs

`/videos-lesson X.Y` produce un `.mp4` por cada tema de la lección, en orden.

`/videos-eval-lesson X.Y` hace lo mismo pero incluye cues orales de pausa ("Hagamos una pausa aquí para evaluar…") en puntos narrativos naturales, y genera además un `.docx` por tema con las dos preguntas de opción múltiple (timestamp, 4 opciones, respuesta correcta, retroalimentación) listo para configurar en H5P Interactive Video (Lumi, Moodle, WordPress o `h5p-standalone`).

Para configurar la clave de ElevenLabs:

1. **Crear la clave** en [elevenlabs.io](https://elevenlabs.io) → *Developers* → *API Keys*.
2. **Crear `.env`** (si no existe):
   ```bash
   # Mac / Linux
   cp .env.example .env
   # Windows (PowerShell)
   Copy-Item .env.example .env
   ```
3. **Pegar la clave** en `.env`:
   ```
   ELEVENLABS_API_KEY=tu_clave
   ```
4. **Verificar**:
   ```bash
   python _video_kit/kit.py doctor
   python _video_kit/kit.py selftest
   ```
5. **Logo** (opcional): copia tu logo como `LogoCurso.png` en la raíz.

Notas:
- Narrar gasta créditos (~2,000 por video). Un `narration.mp3` existente nunca se regenera sin pedirlo.
- Requiere Node.js 22+ y Google Chrome.
- Los `.mp4` y `.mp3` no van a git; respáldalos aparte.

## Solución de problemas

| Síntoma | Causa y solución |
|---------|------------------|
| `Unknown command: /word-lesson` | Claude Code abierto fuera de esta carpeta. Ciérralo y ábrelo con `claude` aquí. |
| `No module named 'fitz'` | Ejecuta `node setup.js` (o `pip install -r requirements.txt`). |
| `No module named 'openpyxl'` | Ejecuta `node setup.js` (o `pip install -r requirements.txt`). |
| `Cannot find module 'docx'` | Ejecuta `node setup.js` (o `cd _tools && npm install`). |
| `python3` no existe (Windows) | Usa `python`. Los comandos detectan cuál existe. |
| `/exam-import`: no encuentra la carpeta | Crea `certificación/` con al menos una subcarpeta y capturas dentro. |
| `/videos-lesson` / `/videos-eval-lesson`: falta `ELEVENLABS_API_KEY` | Falta `.env` o la clave sigue como `pega_aqui_tu_clave`. |
| `/videos-lesson` / `/videos-eval-lesson`: falta ffmpeg | Ejecuta `python _video_kit/kit.py setup`. |
| `/videos-lesson` / `/videos-eval-lesson`: `402 paid_plan_required` | La voz requiere plan de pago en ElevenLabs. |

## Estructura

```
course.config.js          ← configuración del curso (el autor la edita al inicio)
CLAUDE.md                 ← guía que Claude lee al abrir la sesión
pendientes.md             ← lo crea /exam-import si hay temas que revisar
setup.js                  ← instalador de dependencias (node setup.js)
requirements.txt          ← dependencias de Python (pymupdf, openpyxl)
.claude/commands/         ← los comandos /… (no editar)
  init-course.md          ← skill: inicializar desde el PDF del examen
  exam-import.md          ← skill: importar preguntas del examen
  word-lesson.md          ← skill: teoría completa de una lección
  questions-lesson.md     ← skill: preguntas de toda la lección
  activities-lesson.md    ← skill: actividades interactivas de la lección
  html-lesson.md          ← skill: fragmentos HTML de la lección
  videos-lesson.md        ← skill: videos de todos los temas de la lección
  videos-eval-lesson.md   ← skill: videos con pausas H5P + Word de preguntas por tema
  videos.md               ← skill: video individual por tema (mismo que CourseFramework)
_fuente-assets/           ← runtime de actividades (no tocar)
_tools/                   ← herramientas internas (no tocar)
_video_kit/               ← kit de videos (no tocar)
.env.example              ← plantilla de la clave de ElevenLabs
certificación/            ← el autor crea esta carpeta y pone las imágenes del examen
  Variante 1/
    1.png, 2.png …
  Banco de Preguntas.docx
  Cobertura de Objetivos.xlsx
  preguntas_por_tema.json
Videos/                   ← videos generados (no van a git)
Unidad N - …/             ← contenido del curso (lo crea /init-course)
  Teoría/                 ← Lección X.Y - Título.docx
  Preguntas/              ← Lección X.Y - Preguntas.docx
  Actividades/            ← X.Y.Z Título.html (uno por tema)
  Contenido HTML/         ← X.Y.Z Título.html (uno por tema)
  Proyecto/
```
