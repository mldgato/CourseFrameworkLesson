---
description: Lee las imágenes del examen de certificación, genera el Banco de Preguntas en Word y la Cobertura de Objetivos en Excel. Detecta temas ya desarrollados que podrían necesitar revisión de enfoque. Uso: /exam-import
---

# Skill: Importar Preguntas del Examen de Certificación

## Uso
```
/exam-import
```

No recibe argumentos. Procesa todas las variantes disponibles en la carpeta `certificación/`.

## Qué produce
- `certificación/Banco de Preguntas.docx` — todas las preguntas, opciones y respuestas correctas marcadas
- `certificación/Cobertura de Objetivos.xlsx` — matriz de preguntas vs. objetivos del curso
- `certificación/preguntas_por_tema.json` — índice liviano que usan los otros skills para alinear el enfoque
- Aviso en el chat si algún tema ya desarrollado podría necesitar revisión
- Actualización de `pendientes.md` en la raíz si hay temas pendientes de revisar

---

## Paso 0 — Verificar entorno

Lee `course.config.js`. Detecta el ejecutable Python disponible:
```bash
python --version
```
Si falla, intenta `python3 --version`. Usa el que responda. Llama a esa variable `PY` para el resto del skill.

Verifica que openpyxl esté disponible:
```bash
PY -c "import openpyxl"
```
Si falla, instálalo:
```bash
PY -m pip install openpyxl --quiet
```

---

## Paso 1 — Descubrir carpetas y agrupar imágenes

### 1a. Localizar la carpeta raíz del examen
Busca en la raíz del proyecto una carpeta llamada `certificación` o `certificacion` (con o sin tilde). Si no existe, dile al autor exactamente qué crear:
```
Crea en la raíz del proyecto una carpeta llamada "certificación" y dentro de ella
una subcarpeta con el nombre que quieras (por ejemplo "Variante 1"). Coloca ahí
las imágenes PNG/JPG de las preguntas del examen y vuelve a ejecutar /exam-import.
```

### 1b. Listar variantes
Cada subcarpeta directa dentro de `certificación/` es una variante (nombre libre). Lista todas.
Si no hay ninguna subcarpeta pero sí hay imágenes directamente dentro de `certificación/`, trata
ese nivel como una sola variante llamada `"Principal"`.

### 1c. Recopilar y agrupar imágenes por variante
Para cada variante, lista todos los archivos `.png`, `.jpg`, `.jpeg` (cualquier capitalización).

**Regla de agrupación de preguntas multi-imagen:**
- Archivo `N.png` o `N.jpg` → pregunta N, imagen única
- Archivos `N.1.png`, `N.2.png`, `N.3.png`... → pregunta N, imágenes 1, 2, 3... (agrupar como una sola pregunta)
- Archivos `Na.png`, `Nb.png`... → también se tratan como partes de la pregunta N

Ordena las preguntas numéricamente (1, 2, ..., 10, 11 — no alfabéticamente). Dentro de cada
grupo multi-imagen, ordena las partes por número o letra.

Construye internamente una lista de grupos:
```
variante: "Variante 1"
  grupo: { n: 1, partes: ["certificación/Variante 1/1.png"] }
  grupo: { n: 8, partes: ["certificación/Variante 1/8.1.png", "8.2.png", "8.3.png", "8.4.png"] }
  ...
```

---

## Paso 2 — Leer y transcribir cada pregunta

Para cada grupo (pregunta), lee todas sus imágenes usando tu capacidad de visión. Extrae:

### Transcripción verbatim
- **Enunciado:** cópialo exactamente como aparece en la imagen, sin parafrasear ni corregir.
  Si hay una tabla de datos en el contexto, descríbela de forma estructurada (columnas y filas).
  Si hay código, cópialo exactamente.
- **Opciones (A, B, C, D...):** para preguntas de opción múltiple, copia cada opción tal como aparece.
- **Área de respuesta interactiva:** si la pregunta tiene dropdowns, arrastrar-soltar, diagrama o
  código con huecos, describe el mecanismo y el estado visible en las imágenes.

### Tipo de pregunta
Clasifícala en uno de estos tipos:
- `mc` — opción múltiple, una sola respuesta correcta (radio buttons)
- `ms` — selección múltiple, varias correctas (checkboxes)
- `cloze_dropdown` — completar código o texto eligiendo entre opciones en dropdowns
- `drag_drop` — arrastrar elementos a posiciones o categorías
- `erd` — diseño de diagrama (entidad-relación, etc.) seleccionando opciones
- `otro` — cualquier formato no listado arriba (descríbelo)

### Respuesta correcta
Usa tu conocimiento de la certificación indicada en `course.config.js → certification` para
determinar la(s) respuesta(s) correcta(s). Para preguntas interactivas (cloze_dropdown, drag_drop,
erd), describe la respuesta completa con precisión técnica.

**Nunca inventes si no estás seguro:** si una pregunta es ambigua o no puedes determinar la
respuesta con certeza, márcala con `respuesta_incierta: true` y describe las opciones más probables.

### Mapeo al objetivo del curso
Con base en el contenido de la pregunta y en los `units` de `course.config.js`, identifica:
- La lección más probable (`lesson.id` + `lesson.objective`)
- El tema más probable (`topic.id` + `topic.title`)

Si una pregunta cubre dos temas, mapéala al más específico. Si genuinamente no encaja en ningún
tema del curso, indica `objetivo: null` y anota el motivo.

### Resultado interno por pregunta
Al terminar de leer todas las imágenes de cada variante, tendrás un arreglo interno de objetos:
```
{
  n: 1,
  variante: "Variante 1",
  tipo: "mc",
  multiImagen: false,
  enunciado: "...(verbatim)...",
  opciones: [                          // solo para mc / ms
    { letra: "A", texto: "...", correcta: true },
    { letra: "B", texto: "...", correcta: false },
    ...
  ],
  respuesta_descripcion: null,         // para tipos interactivos
  contexto_codigo: null,               // para cloze_dropdown con código
  respuesta_incierta: false,
  objetivo: {
    unidad_id: 1, unidad_titulo: "...",
    leccion_id: "1.1", leccion_objetivo: "...",
    tema_id: "1.1.1", tema_titulo: "..."
  }
}
```

---

## Paso 3 — Detectar modo (primera vez vs. actualización)

Comprueba si ya existe `certificación/Banco de Preguntas.docx`:
- **No existe:** modo "primera vez". Continúa con el Paso 4.
- **Existe:** modo "actualización". Informa al autor: "Detecté [N] preguntas totales. Los archivos
  anteriores serán reemplazados por una versión actualizada con todas las variantes."

---

## Paso 4 — Generar Word (Banco de Preguntas.docx)

### 4a. Crear el script temporal

Crea `_tools/_tmp_exam_word.js` con el siguiente contenido (reemplaza `/* DATOS */` con los datos
reales que extrajiste en el Paso 2):

```javascript
const fs   = require('fs');
const path = require('path');
const { el, pack, C } = require('./lib-leccion.js');
const {
  Paragraph, TextRun, BorderStyle, ShadingType, AlignmentType
} = require('docx');
const { NAVY, STEEL, GREY, OK, OKBG, LIGHT } = C;

const cfg = require(path.join(__dirname, '..', 'course.config.js'));
const OUT  = process.argv[2] ||
             path.join(__dirname, '..', 'certificacion', 'Banco de Preguntas.docx');

const TIPO_LABEL = {
  mc:              'Opción múltiple · una respuesta correcta',
  ms:              'Selección múltiple · varias respuestas correctas',
  cloze_dropdown:  'Completar código · seleccionar en lista desplegable',
  drag_drop:       'Arrastrar y soltar',
  erd:             'Diseño de diagrama · seleccionar tipo de relación',
  otro:            'Otro formato',
};

// ── DATOS EXTRAÍDOS POR /exam-import ────────────────────────────────────────
const PREGUNTAS = [
  /* DATOS */
];
// ────────────────────────────────────────────────────────────────────────────

function separador(texto) {
  return new Paragraph({
    spacing: { before: 300, after: 100 },
    border: {
      bottom: { style: BorderStyle.SINGLE, size: 6, color: STEEL, space: 4 },
      top:    { style: BorderStyle.SINGLE, size: 6, color: STEEL, space: 4 },
    },
    shading: { type: ShadingType.CLEAR, fill: LIGHT },
    children: [new TextRun({ text: texto, bold: true, color: STEEL, size: 22, allCaps: true })],
  });
}

function marcadorIncierto() {
  return el.callout(
    '⚠ Respuesta a verificar',
    'Esta pregunta fue marcada como incierta. Verifica la respuesta correcta en la guía oficial.'
  );
}

const children = [];

// Portada del banco
children.push(el.h1('Banco de Preguntas de Certificación'));
children.push(el.p(`${cfg.name}  ·  ${cfg.certification}`));
children.push(el.sp(80));

const totalPreguntas = PREGUNTAS.length;
const variantes = [...new Set(PREGUNTAS.map(q => q.variante))];
children.push(el.p(
  `Total de preguntas: **${totalPreguntas}**  ·  Variantes: **${variantes.join(', ')}**`
));
children.push(el.sp(200));

// Preguntas agrupadas por variante
for (const v of variantes) {
  children.push(separador(`Variante: ${v}`));
  children.push(el.sp(80));

  const pqs = PREGUNTAS.filter(q => q.variante === v);
  pqs.forEach((q, idx) => {
    // Encabezado de pregunta
    const tituloP = q.multiImagen
      ? `Pregunta ${q.n}  (multi-imagen)`
      : `Pregunta ${q.n}`;
    children.push(el.h2(tituloP));
    children.push(el.label(TIPO_LABEL[q.tipo] || q.tipo));

    // Enunciado
    children.push(el.p(q.enunciado));

    // Código de contexto (cloze_dropdown)
    if (q.contexto_codigo) {
      children.push(el.code(q.contexto_codigo.split('\n')));
    }

    // Opciones mc / ms
    if (q.opciones && q.opciones.length) {
      q.opciones.forEach(o => {
        children.push(el.opt(o.letra, o.texto, o.correcta));
      });
    }

    // Respuesta interactiva
    if (q.respuesta_descripcion) {
      children.push(el.callout('Respuesta correcta', q.respuesta_descripcion));
    }

    // Respuesta incierta
    if (q.respuesta_incierta) {
      children.push(marcadorIncierto());
    }

    // Objetivo
    if (q.objetivo) {
      children.push(el.p(
        `Objetivo: **${q.objetivo.leccion_id}** ${q.objetivo.leccion_objetivo} → ` +
        `**${q.objetivo.tema_id}** ${q.objetivo.tema_titulo}`
      ));
    } else {
      children.push(el.p('Objetivo: no identificado en el temario actual'));
    }

    if (idx < pqs.length - 1) children.push(el.sp(100));
  });

  children.push(el.sp(200));
}

pack(
  {
    title:       'Banco de Preguntas de Certificación',
    runningHead: `${cfg.name} · Banco de Preguntas · ${cfg.certification}`,
  },
  children,
  OUT
)
.then(() => { try { fs.unlinkSync(__filename); } catch (_) {} })
.catch(e => { console.error(e); try { fs.unlinkSync(__filename); } catch (_) {} process.exit(1); });
```

**Reglas para llenar `PREGUNTAS`:**
- Incluye **todas** las preguntas de **todas** las variantes en el orden en que se leyeron.
- Para preguntas de tipo `mc` o `ms`: llena `opciones` y deja `respuesta_descripcion: null`.
- Para tipos interactivos: llena `respuesta_descripcion` con texto preciso y `opciones: []`.
- Si hay código de contexto (instrucción SQL incompleta, etc.), ponlo en `contexto_codigo`
  como string con saltos de línea `\n`.
- Escapa correctamente las comillas y caracteres especiales del JavaScript.

### 4b. Ejecutar y limpiar

Asegúrate de que las dependencias de Node estén instaladas:
```bash
# Mac/Linux:
cd _tools && npm install --silent && cd ..

# Windows (PowerShell):
Set-Location _tools; npm install --silent; Set-Location ..
```

Determina la ruta de salida correcta (con o sin tilde, según el nombre real de la carpeta):
```bash
node _tools/_tmp_exam_word.js "certificación/Banco de Preguntas.docx"
```
El script se autoeliminará. Si falla, elimínalo manualmente:
```bash
# Mac/Linux:   rm _tools/_tmp_exam_word.js
# Windows:     Remove-Item _tools\_tmp_exam_word.js
```

---

## Paso 5 — Generar Excel (Cobertura de Objetivos.xlsx)

### 5a. Crear el script temporal

Crea `_tools/_tmp_exam_excel.py` con el siguiente contenido (rellena `PREGUNTAS` y `CFG`):

```python
import os, json
from pathlib import Path
import openpyxl
from openpyxl.styles import (
    Font, PatternFill, Alignment, Border, Side, numbers
)
from openpyxl.utils import get_column_letter

# ── DATOS EXTRAÍDOS POR /exam-import ────────────────────────────────────────
CFG = {
    "name":          "NOMBRE_CURSO",
    "certification": "CERTIFICACION",
}
PREGUNTAS = [
    # Mismo formato que en el script de Word
]
# ────────────────────────────────────────────────────────────────────────────

NAVY  = "1F3864"
STEEL = "2E5496"
WHITE = "FFFFFF"
LIGHT = "EAF0F8"
OK_BG = "E6F4EA"
WARN  = "FFF3CD"

def fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)

def thin_border():
    s = Side(style="thin", color="BFBFBF")
    return Border(left=s, right=s, top=s, bottom=s)

def header_cell(ws, row, col, text, navy=False):
    c = ws.cell(row=row, column=col, value=text)
    c.font      = Font(name="Calibri", bold=True, color=WHITE if navy else NAVY, size=10)
    c.fill      = fill(NAVY if navy else LIGHT)
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border    = thin_border()
    return c

def data_cell(ws, row, col, text, bg=WHITE, bold=False, wrap=True):
    c = ws.cell(row=row, column=col, value=text)
    c.font      = Font(name="Calibri", size=10, bold=bold)
    c.fill      = fill(bg)
    c.alignment = Alignment(horizontal="left", vertical="top", wrap_text=wrap)
    c.border    = thin_border()
    return c

wb = openpyxl.Workbook()

# ═══════════════════════════════════════════════════════════════
# HOJA 1: Cobertura
# ═══════════════════════════════════════════════════════════════
ws1 = wb.active
ws1.title = "Cobertura"
ws1.freeze_panes = "A6"

# Fila 1: título
c = ws1.cell(row=1, column=1,
             value=f"Cobertura de Objetivos — {CFG['name']} · {CFG['certification']}")
c.font = Font(name="Calibri", bold=True, size=14, color=NAVY)
ws1.row_dimensions[1].height = 22

# Fila 2: descripción
total_pqs = len(PREGUNTAS)
variantes = list(dict.fromkeys(q["variante"] for q in PREGUNTAS))
c2 = ws1.cell(row=2, column=1,
              value=f"{total_pqs} pregunta(s) extraídas de: {', '.join(variantes)}")
c2.font = Font(name="Calibri", size=10, color="595959", italic=True)

# Fila 3: métricas
# Calcula cuántos temas (sub-objetivos) están cubiertos
temas_con_preguntas = set(
    q["objetivo"]["tema_id"]
    for q in PREGUNTAS
    if q.get("objetivo") and q["objetivo"].get("tema_id")
)

# Fila 3 — celdas de métrica (encabezados)
header_cell(ws1, 3, 1, "Temas cubiertos")
header_cell(ws1, 3, 2, "Total de preguntas")
header_cell(ws1, 3, 3, "Variantes procesadas")

# Fila 4 — valores
data_cell(ws1, 4, 1, len(temas_con_preguntas), bold=True)
data_cell(ws1, 4, 2, total_pqs, bold=True)
data_cell(ws1, 4, 3, len(variantes), bold=True)

# Fila 5 — encabezados de columnas
COLS = ["Unidad", "Lección", "Tema (sub-objetivo)", "Estado",
        "N.º Pregunta", "Enunciado resumido", "Variante", "Tipo", "Respuesta incierta"]
for i, col in enumerate(COLS, 1):
    header_cell(ws1, 5, i, col, navy=True)
ws1.row_dimensions[5].height = 30

# Anchos de columna
COL_WIDTHS = [22, 28, 32, 14, 12, 55, 18, 22, 18]
for i, w in enumerate(COL_WIDTHS, 1):
    ws1.column_dimensions[get_column_letter(i)].width = w

# Filas de datos — una fila por pregunta
row = 6
for q in PREGUNTAS:
    obj = q.get("objetivo") or {}
    enunciado_corto = (q.get("enunciado") or "")[:120]
    if len(q.get("enunciado") or "") > 120:
        enunciado_corto += "…"
    estado_bg = OK_BG if obj.get("tema_id") else WARN
    incierta_txt = "Sí ⚠" if q.get("respuesta_incierta") else ""

    data_cell(ws1, row, 1, f"{obj.get('unidad_id', '')} · {obj.get('unidad_titulo', '')}" if obj else "—")
    data_cell(ws1, row, 2,
              f"{obj.get('leccion_id', '')} {obj.get('leccion_objetivo', '')}" if obj else "—")
    data_cell(ws1, row, 3,
              f"{obj.get('tema_id', '')} {obj.get('tema_titulo', '')}" if obj else "— Sin asignar —",
              bg=estado_bg)
    data_cell(ws1, row, 4, "Cubierto" if obj.get("tema_id") else "Sin tema", bg=estado_bg, bold=True)
    data_cell(ws1, row, 5, q["n"], bold=True)
    data_cell(ws1, row, 6, enunciado_corto)
    data_cell(ws1, row, 7, q["variante"])
    data_cell(ws1, row, 8, q.get("tipo", ""))
    data_cell(ws1, row, 9, incierta_txt, bg=WARN if q.get("respuesta_incierta") else WHITE)
    ws1.row_dimensions[row].height = 40
    row += 1

# ═══════════════════════════════════════════════════════════════
# HOJA 2: Preguntas
# ═══════════════════════════════════════════════════════════════
ws2 = wb.create_sheet("Preguntas")
ws2.freeze_panes = "A3"

c = ws2.cell(row=1, column=1,
             value=f"Banco de Preguntas — {CFG['name']} · {CFG['certification']}")
c.font = Font(name="Calibri", bold=True, size=14, color=NAVY)

COLS2 = ["N.º", "Variante", "Enunciado", "Tipo",
         "Opciones", "Respuesta(s) correcta(s)", "Lección", "Tema"]
for i, col in enumerate(COLS2, 1):
    header_cell(ws2, 2, i, col, navy=True)
ws2.row_dimensions[2].height = 28

COL_WIDTHS2 = [6, 18, 65, 20, 55, 40, 28, 32]
for i, w in enumerate(COL_WIDTHS2, 1):
    ws2.column_dimensions[get_column_letter(i)].width = w

row2 = 3
for q in PREGUNTAS:
    obj = q.get("objetivo") or {}

    # Opciones: unir en texto legible
    if q.get("opciones"):
        ops_txt = "\n".join(
            f"{o['letra']}. {o['texto']}{' ✓' if o.get('correcta') else ''}"
            for o in q["opciones"]
        )
        resp_txt = ", ".join(
            o["letra"] for o in q["opciones"] if o.get("correcta")
        )
    else:
        ops_txt  = "Ver descripción →"
        resp_txt = q.get("respuesta_descripcion", "")

    if q.get("respuesta_incierta"):
        resp_txt = "⚠ " + resp_txt

    data_cell(ws2, row2, 1, q["n"], bold=True)
    data_cell(ws2, row2, 2, q["variante"])
    data_cell(ws2, row2, 3, q.get("enunciado", ""))
    data_cell(ws2, row2, 4, q.get("tipo", ""))
    data_cell(ws2, row2, 5, ops_txt)
    data_cell(ws2, row2, 6, resp_txt,
              bg=OK_BG if not q.get("respuesta_incierta") else WARN)
    data_cell(ws2, row2, 7,
              f"{obj.get('leccion_id', '')} {obj.get('leccion_objetivo', '')}" if obj else "—")
    data_cell(ws2, row2, 8,
              f"{obj.get('tema_id', '')} {obj.get('tema_titulo', '')}" if obj else "—")
    ws2.row_dimensions[row2].height = 60
    row2 += 1

# Guardar
out_path = Path(__file__).parent.parent / "certificacion" / "Cobertura de Objetivos.xlsx"
# Intenta también con tilde
alt_path = Path(__file__).parent.parent / "certificación" / "Cobertura de Objetivos.xlsx"
if not out_path.parent.exists() and alt_path.parent.exists():
    out_path = alt_path

wb.save(str(out_path))
print(f"OK  {out_path.name}  ({out_path.stat().st_size} bytes)")

# Autoeliminación
try:
    os.remove(__file__)
except Exception:
    pass
```

**Reglas para llenar `CFG` y `PREGUNTAS`:**
- `CFG`: copia `name` y `certification` de `course.config.js`.
- `PREGUNTAS`: **exactamente** el mismo array de objetos que en el script de Word (reutiliza la misma
  estructura para no transcribir los datos dos veces).
- Escapa correctamente las comillas en Python (usa `"""` o `\'` según sea necesario).
- Las cadenas de texto multilínea úsalas con `\\n` en un string normal o con `"""..."""`.

### 5b. Ejecutar y limpiar

```bash
PY _tools/_tmp_exam_excel.py
```
El script se autoeliminará. Si falla:
```bash
# Mac/Linux:   rm _tools/_tmp_exam_excel.py
# Windows:     Remove-Item _tools\_tmp_exam_excel.py
```

---

## Paso 6 — Generar JSON de índice (preguntas_por_tema.json)

Escribe directamente el archivo `certificación/preguntas_por_tema.json` (o `certificacion/`).
El formato es un objeto cuyas claves son los `tema_id` de `course.config.js`:

```json
{
  "1.1.1": [
    {
      "n": 1,
      "variante": "Variante 1",
      "enunciado_corto": "Primeros 150 caracteres del enunciado…",
      "tipo": "mc",
      "respuesta_incierta": false
    }
  ],
  "2.3.2": [ ... ],
  "_sin_tema": [
    {
      "n": 15,
      "variante": "Variante 1",
      "enunciado_corto": "...",
      "tipo": "cloze_dropdown",
      "respuesta_incierta": false
    }
  ]
}
```

Usa la clave especial `"_sin_tema"` para preguntas que no pudiste mapear a ningún objetivo.

---

## Paso 7 — Detectar temas que necesitan revisión de enfoque

Para cada tema que tiene preguntas en el JSON generado, comprueba si ya existe su Word de teoría:

```bash
# Mac/Linux:
ls "Unidad N - .../Teoría/"

# Windows (PowerShell):
Get-ChildItem "Unidad N - ...\Teoría\"
```

Si el archivo de teoría existe **Y** el enunciado de alguna pregunta de ese tema sugiere un ángulo,
habilidad o caso de uso que el título del tema no cubre explícitamente, incluye ese tema en la lista
de revisión. Usa tu juicio para determinar si el ángulo es realmente diferente o solo complementario.

Construye internamente una lista `TEMAS_A_REVISAR`:
```
{
  tema_id: "1.1.1",
  tema_titulo: "...",
  ruta_word: "Unidad 1 - .../Teoría/Lección 1.1 - ....docx",
  preguntas_relacionadas: [1, 5],
  motivo: "La P5 evalúa [ángulo específico] que va más allá de [título del tema]"
}
```

---

## Paso 8 — Actualizar pendientes.md

Si `TEMAS_A_REVISAR` no está vacío, actualiza o crea `pendientes.md` en la raíz:

```markdown
# Pendientes del curso

> Generado/actualizado por `/exam-import` el FECHA.
> El autor decide qué cambios aplicar. Elimina una fila cuando la hayas resuelto.

## Temas con posible desalineación de enfoque

| Tema | Archivo de teoría | Preguntas del examen | Acción sugerida |
|------|-------------------|----------------------|-----------------|
| 1.1.1 Título | Unidad 1 - .../Teoría/... | P5, P12 (Variante 1) | Revisar si el enfoque actual cubre [motivo] |
```

Si ya existe `pendientes.md`, **agrega** las nuevas filas sin borrar las anteriores; indica la fecha
de la nueva detección en cada fila nueva. No repitas filas que ya estaban.

---

## Paso 9 — Entregar resumen al autor

Muestra en el chat:

```
✅ /exam-import completado

📄 Banco de Preguntas:  certificación/Banco de Preguntas.docx
   [N] preguntas · [V] variante(s): [lista]
   [X] preguntas con respuesta incierta (marcadas en el Word)

📊 Cobertura de Objetivos:  certificación/Cobertura de Objetivos.xlsx
   [Y] temas cubiertos de [Z] en el temario

🗂  Índice JSON:  certificación/preguntas_por_tema.json

⚠️  Temas con posible revisión de enfoque: [N]
   → Ver pendientes.md para el detalle
```

Si no hay temas a revisar, omite la última sección.

Si hubo preguntas con `respuesta_incierta: true`, lista sus números y pide al autor que las verifique
contra la guía oficial o el material de estudio.

---

## Notas de compatibilidad (Windows / Mac)

- Rutas: usa siempre `/` en Bash (Mac) y `\` o `/` en PowerShell (Windows); los scripts de Node y
  Python usan `path.join` / `Path` que son cross-platform.
- Python: usa `PY` (el ejecutable que respondió en el Paso 0).
- Eliminación de temporales: los scripts se autoelim inan; en caso de fallo, usa `rm` (Mac) o
  `Remove-Item` (Windows).
- Nombre de la carpeta `certificación`: puede tener tilde o no; los scripts de Python intentan
  ambas variantes automáticamente. Pasa siempre el nombre exacto que veas en disco al Node script.
- Nunca uses rutas absolutas en los scripts temporales; usa siempre `__dirname` / `__file__` para
  calcular rutas relativas.
