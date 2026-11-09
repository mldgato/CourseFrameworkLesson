---
description: Genera el Word de teoría completo para UNA lección entera (todos sus temas de una vez). Uso: /word-lesson X.Y
argument-hint: X.Y
---

# Skill: Generar Teoría en Word (lección completa)

**Argumento recibido:** `$ARGUMENTS` (la lección, p. ej. `1.1`). Si viene vacío, pídelo al autor.

## Uso
```
/word-lesson 1.1
```

## Lo que hace
Genera **en una sola pasada** el documento Word de teoría completo de la lección indicada, con
todos sus temas. El autor revisa el Word una vez al final, no tema por tema.

## Pasos internos (invisibles para el autor)

### 1. Leer el contexto
- Lee `course.config.js` → encuentra la lección X.Y: su título, objetivo, lista de temas y la unidad.
- Lee el PDF del examen (si existe en la raíz) para el detalle de los sub-objetivos.
- **Preguntas del examen real:** si existe `certificación/preguntas_por_tema.json` (o `certificacion/`),
  extrae las preguntas de cada tema de la lección. Úsalas para orientar el enfoque del contenido.
- Verifica si ya existe el archivo Word de la lección. Si existe, pregunta antes de sobreescribir.

### 2. Redactar el contenido de cada tema

Para **cada tema X.Y.Z** de la lección, en orden, genera:

**Estructura por tema:**
- **Callout de objetivo de certificación (obligatorio):** `Objetivo de certificación {certification} · {topic.id} {topic.title}` y `Objetivo {lesson.id}: {lesson.objective}`. Datos de `course.config.js`, sin inventar.
- **3–5 párrafos** de desarrollo (empieza con el "por qué" antes del "qué")
- **Ejemplo trabajado** usando el escenario de `course.config.js → scenario.name`
- **Tabla comparativa** si aplica (conceptos vs. características, etc.)
- **Recuadro "Error común"** con el malentendido más frecuente
- **Recuadro "Para la evaluación"** con lo que el examen mide de este tema

**Reglas:**
- Sin emojis
- Moneda: `$`
- Si hay preguntas del examen real para ese tema, asegúrate de que el contenido cubre el ángulo que evalúan

Al terminar el último tema, agrega una sección **"Resumen de la lección"** que:
- Resume los conceptos clave de cada tema en 2–3 líneas
- Lista las habilidades adquiridas
- Menciona los errores comunes más importantes de toda la lección

### 3. Generar el Word (invisible)

Crea `_tools/_tmp_wordlesson{X}{Y}.js` con todo el contenido embebido y ejecútalo:

```bash
# Mac/Linux:
cd _tools && npm install --silent && cd ..
node _tools/_tmp_wordlesson{X}{Y}.js "Unidad N - .../Teoría/Lección X.Y - Título.docx"

# Windows (PowerShell):
Set-Location _tools; npm install --silent; Set-Location ..
node _tools/_tmp_wordlesson{X}{Y}.js "Unidad N - ...\Teoría\Lección X.Y - Título.docx"
```

**Estructura del script:**
```javascript
const fs   = require('fs');
const path = require('path');
const { el, pack, head, C } = require('./lib-leccion.js');
const cfg = require(path.join(__dirname, '..', 'course.config.js'));
const OUT = process.argv[2];

// meta de la lección
const META = {
  unit:       "Unidad N – Título de la unidad",
  title:      "X.Y Título de la lección",
  objective:  "Objetivo de la lección",
  runningHead:"Curso · Lección X.Y",
  intro:      "Descripción de la lección",
  objectives: ["Objetivo 1", "Objetivo 2"],   // objetivos de aprendizaje
  keywords:   [{ t: "Término", d: "Definición" }],
};

// Contenido de cada tema como arreglo de elementos el.*
const TEMAS = [
  {
    id: "X.Y.1", titulo: "Título",
    contenido: [ /* el.h1(), el.callout(), el.p(), el.table(), ... */ ]
  },
  // ...más temas
];

// Resumen de la lección
const RESUMEN = [ /* el.h1("Resumen de la lección"), el.p(), el.li(), ... */ ];

const children = head(META);
TEMAS.forEach(t => { children.push(...t.contenido); });
children.push(...RESUMEN);

pack(META, children, OUT)
  .then(() => { try { fs.unlinkSync(__filename); } catch(_){} })
  .catch(e => { console.error(e); try { fs.unlinkSync(__filename); } catch(_){} process.exit(1); });
```

El script se autoeliminará. Si falla, elimínalo:
```bash
# Mac/Linux:   rm _tools/_tmp_wordlesson{X}{Y}.js
# Windows:     Remove-Item _tools\_tmp_wordlesson{X}{Y}.js
```

### 4. Entregar
Confirma al autor:
- Ruta del archivo generado
- Número de temas incluidos y número aproximado de caracteres por tema
- Si alguna pregunta del examen real orientó el enfoque de algún tema
- Resumen de la lección incluido al final

## Carpeta de salida
`Unidad N - .../Teoría/Lección X.Y - Título.docx`
