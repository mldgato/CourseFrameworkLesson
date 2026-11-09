---
description: Genera todos los fragmentos HTML del ebook para UNA lección entera (un archivo por tema). Uso: /html-lesson X.Y
argument-hint: X.Y
---

# Skill: Generar Contenido HTML del Ebook (lección completa)

**Argumento recibido:** `$ARGUMENTS` (la lección, p. ej. `1.1`). Si viene vacío, pídelo al autor.

## Uso
```
/html-lesson 1.1
```

## Lo que hace
Genera **en una sola pasada** el fragmento HTML del ebook para cada tema de la lección. Cada tema
produce su propio archivo HTML. El autor revisa todos al final.

## Pasos internos (invisibles para el autor)

### 1. Leer el contexto
- Lee `course.config.js` → lección X.Y y lista de todos sus temas.
- Lee el Word de teoría de la lección si existe (es la fuente principal del contenido).
- **Preguntas del examen real:** si existe `certificación/preguntas_por_tema.json` (o `certificacion/`),
  extrae las preguntas de cada tema para verificar que el fragmento HTML cubre los conceptos clave
  que el examen evalúa (sin agregar quizzes; eso es exclusivo de las Actividades).

### 2. Convertir o generar cada tema

**Si existe el Word de la lección**, convierte todos los temas de una vez con:
```bash
# Mac/Linux:
python _tools/docx2html.py --split \
  "Unidad N - .../Teoría/Lección X.Y - Título.docx" \
  "Unidad N - .../Contenido HTML" "X.Y"

# Windows (PowerShell):
python _tools/docx2html.py --split `
  "Unidad N - ...\Teoría\Lección X.Y - Título.docx" `
  "Unidad N - ...\Contenido HTML" "X.Y"
```
Esto genera un archivo por tema. Luego verifica cada uno.

**Si no existe el Word**, genera el contenido HTML de cada tema directamente desde el PDF y `course.config.js`.

### 3. Reglas del fragmento (aplica a cada tema)

**Estructura obligatoria:**
```html
<div style="background:#fbfdff; background-image: linear-gradient(#e3edf5 1px, transparent 1px), linear-gradient(90deg, #e3edf5 1px, transparent 1px); background-size: 26px 26px;">
  <div style="max-width:900px; padding:0 24px; font-family:helvetica,arial,sans-serif">
    <!-- contenido del tema aquí -->
  </div>
</div>
```

**Paleta** (desde `course.config.js → palette`):
- Encabezados y negritas → `navy`
- Subtítulos y acentos → `steel`
- Texto → `#1e2f3f`; fondos de recuadro → `#eaf4fb`
- Cada `<td>` lleva `background:#ffffff`

**Jerarquía:** título de tema → `<h2>`, subtítulo → `<h3>`, sub-subtítulo → `<h4>`

**Objetivo de certificación (obligatorio):** justo después del `<h2>` del tema debe haber un recuadro
compacto (fondo `#eaf4fb`, borde izquierdo `steel`, texto pequeño) con:
`Objetivo de certificación {certification} · {topic.id} {topic.title}` y
`Objetivo {lesson.id}: {lesson.objective}`.

**Regla de contenido:** solo repaso y exploración. Sin quizzes.

### 4. Retrofit interactivo (opcional, por tema)
Si algún tema tiene tabla de clasificación o glosario con dos columnas, pregunta al autor si aplica tarjetas flip:
```bash
python _tools/add_flashcards.py "Contenido HTML/X.Y.Z Título.html"
```
**Nunca forzar interactividad donde no hay tabla adecuada.**

### 5. Entregar
Al terminar todos los temas, confirma al autor:
- Lista de archivos generados (uno por línea con su ruta y longitud aproximada en caracteres)
- Si algún tema tiene tarjetas flip aplicadas
- Si algún fragmento careció del recuadro de objetivo y lo agregaste manualmente

## ⚠️ Aviso importante
Si algún archivo ya tiene tarjetas flip o timeline aplicados manualmente, **NO volver a ejecutar `--split`** sobre ese tema: destruiría el `<style>/<script>` interactivo. En ese caso, edita el archivo directamente.

## Carpeta de salida
`Unidad N - .../Contenido HTML/X.Y.Z Título.html`  (un archivo por cada tema de la lección)
