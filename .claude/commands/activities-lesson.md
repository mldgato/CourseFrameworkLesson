---
description: Genera todas las actividades HTML interactivas para UNA lección entera (un archivo por tema). Uso: /activities-lesson X.Y
argument-hint: X.Y
---

# Skill: Generar Actividades Interactivas (lección completa)

**Argumento recibido:** `$ARGUMENTS` (la lección, p. ej. `1.1`). Si viene vacío, pídelo al autor.

## Uso
```
/activities-lesson 1.1
```

## Lo que hace
Genera **en una sola pasada** un archivo HTML de actividad interactiva por cada tema de la lección.
El autor revisa todas las actividades en el navegador al final.

## Pasos internos (invisibles para el autor)

### 1. Leer el contexto
- Lee `course.config.js` → lección X.Y y lista de todos sus temas.
- **Preguntas del examen real:** si existe `certificación/preguntas_por_tema.json` (o `certificacion/`),
  extrae las preguntas de cada tema. Úsalas para diseñar ejercicios que entrenen el mismo tipo de
  razonamiento del examen real (si el examen usa dropdowns en código, usa `QuizDragMatch` o
  `QuizChoice`; si usa clasificación, usa `QuizSort`).
- Para cada tema, lee su Word de teoría si existe y sus preguntas si existen.

### 2. Generar la actividad de cada tema

**Repite los Pasos 2a–2c para cada tema X.Y.Z de la lección, en orden.**

#### 2a. Diseñar la actividad del tema

**Estructura de pasos:**
1. **Repaso** — resumen del tema: texto + lista de puntos clave + un callout.
   - Incluye etiqueta discreta: `Objetivo {topic.id}` con tooltip `{certification} · Objetivo {lesson.id}: {lesson.objective}`.
2. **Práctica** — 1–2 ejercicios interactivos.
3. **Evaluación** — 2–4 preguntas evaluables (o inyectadas desde el Word de preguntas si existe).

**Reglas de diseño:**
- Paleta slate + índigo, compatible con modo oscuro
- Sin scroll de página; el contenido va dentro de `.step`
- Badge `practica` (índigo) o `analogia` (ámbar) según el tipo
- Emojis permitidos
- ID de la actividad: `{config.id}-X.Y.Z`

**Widgets disponibles:**
```js
QuizChoice(sel, {options:[{label, ok, fb}]})
QuizMulti(sel, {options:[{label, ok}], hint})
QuizSort(sel, {items:[{label,cat}], cats:[...]})
QuizMatch(sel, {pairs:[{l, r}]})
QuizOrder(sel, {items:[...]})
QuizDragMatch(sel, {pairs:[{l,r}]})
```

#### 2b. Escribir el HTML del tema

El archivo embebe inline (en `<script>`) las versiones minificadas de:
- `_fuente-assets/xperienceed.js`
- `_fuente-assets/deck.js`
- `_fuente-assets/quiz.js`

Termina siempre con:
```js
Xp.init({ id: "COURSE_ID-X.Y.Z", title: "Título del tema" });
Deck.init();
```

#### 2c. Verificar el tema
```bash
node _tools/test_activity_smoke.js "Unidad N - .../Actividades/X.Y.Z Título.html"
```
Si falla, corrige el HTML antes de pasar al siguiente tema.

### 3. Entregar
Al terminar todos los temas, confirma al autor:
- Lista de archivos generados (uno por línea con su ruta)
- Número de ejercicios evaluables por actividad
- Cuáles pasaron la verificación automática
- Si alguno falló la verificación (y qué corregiste)

## Carpeta de salida
`Unidad N - .../Actividades/X.Y.Z Título.html`  (un archivo por cada tema de la lección)
