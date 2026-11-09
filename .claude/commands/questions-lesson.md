---
description: Genera el Word de preguntas de evaluación completo para UNA lección entera (todos sus temas). Uso: /questions-lesson X.Y
argument-hint: X.Y
---

# Skill: Generar Preguntas en Word (lección completa)

**Argumento recibido:** `$ARGUMENTS` (la lección, p. ej. `1.1`). Si viene vacío, pídelo al autor.

## Uso
```
/questions-lesson 1.1
```

## Lo que hace
Genera **en una sola pasada** el documento Word de preguntas de evaluación para todos los temas
de la lección indicada. El autor revisa el Word una sola vez al final.

## Pasos internos (invisibles para el autor)

### 1. Leer el contexto
- Lee `course.config.js` → encuentra la lección X.Y y todos sus temas.
- Lee el Word de teoría de la lección si ya existe (para basar las preguntas en el contenido real).
- **Preguntas del examen real:** si existe `certificación/preguntas_por_tema.json` (o `certificacion/`),
  extrae las preguntas de cada tema. Úsalas como referencia de estilo y dificultad: los distractores
  y el tipo de razonamiento del examen real deben reflejarse. No copies enunciados verbatim.
- Verifica si ya existe el archivo de preguntas. Si existe, pregunta antes de sobreescribir.

### 2. Diseñar las preguntas de cada tema

Para **cada tema X.Y.Z** de la lección, en orden, genera **2–5 preguntas** según la complejidad:

**Reglas:**
- **Objetivo de certificación (obligatorio):** bajo el encabezado de cada tema, una línea
  `Objetivo de certificación {certification} · {topic.id} {topic.title} (Objetivo {lesson.id}: {lesson.objective})`.
- Mezcla al menos 2 tipos diferentes por tema.
- Los distractores son errores reales, no inventados.
- Usa el escenario del curso en los enunciados cuando aplique.
- Sin emojis.

**Los 7 tipos disponibles:**

| Tipo | Descripción |
|------|-------------|
| `mc` | Opción múltiple (una correcta), respuesta inmediata |
| `ms` | Selección múltiple (varias correctas) + botón Comprobar |
| `cloze` | Completar huecos arrastrando palabras de un banco |
| `sort` | Clasificar elementos en 2–3 categorías |
| `match` | Emparejar dos columnas con `<select>` |
| `order` | Ordenar una secuencia arrastrando |
| `dragmatch` | Emparejar arrastrando palabras a sus definiciones |

### 3. Generar el Word (invisible)

Crea `_tools/_tmp_questionslesson{X}{Y}.js` con todas las preguntas embebidas y ejecútalo:

```bash
# Mac/Linux:
node _tools/_tmp_questionslesson{X}{Y}.js "Unidad N - .../Preguntas/Lección X.Y - Preguntas.docx"

# Windows:
node _tools\_tmp_questionslesson{X}{Y}.js "Unidad N - ...\Preguntas\Lección X.Y - Preguntas.docx"
```

**Estructura del script** (usa `lib-preguntas.js`):
```javascript
const fs   = require('fs');
const path = require('path');
const { buildQuestions } = require('./lib-preguntas.js');
const cfg = require(path.join(__dirname, '..', 'course.config.js'));
const OUT = process.argv[2];

const META = {
  unit:       "Unidad N – Título",
  title:      "Lección X.Y – Preguntas de evaluación",
  objective:  "Objetivo de la lección",
  runningHead:"Curso · Lección X.Y – Preguntas",
};

const TOPICS = [
  {
    code: "X.Y.1",
    title: "Título del tema",
    questions: [
      { type: "mc", stem: "...", options: [{ t: "...", ok: true }, { t: "..." }] },
      { type: "sort", stem: "...", cats: ["Cat A", "Cat B"], items: [{ t: "...", cat: "Cat A" }] },
      // ...más preguntas del tema
    ]
  },
  // ...más temas
];

buildQuestions(META, TOPICS, OUT)
  .then(() => { try { fs.unlinkSync(__filename); } catch(_){} })
  .catch(e => { console.error(e); try { fs.unlinkSync(__filename); } catch(_){} process.exit(1); });
```

El script se autoeliminará. Si falla:
```bash
# Mac/Linux:   rm _tools/_tmp_questionslesson{X}{Y}.js
# Windows:     Remove-Item _tools\_tmp_questionslesson{X}{Y}.js
```

### 4. Verificar si ya existe la actividad HTML de cada tema
Si existe la actividad HTML de algún tema (`Actividades/X.Y.Z Título.html`), inyecta las preguntas:
```bash
# Mac/Linux o Windows:
python _tools/inject_preguntas.py "Unidad N - ..."
```
(O usa `python3` si `python` no existe.)

### 5. Entregar
Confirma al autor:
- Ruta del Word generado
- Total de preguntas por tema y tipos utilizados
- Si se inyectaron en actividades existentes

## Carpeta de salida
`Unidad N - .../Preguntas/Lección X.Y - Preguntas.docx`
