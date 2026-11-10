---
description: Lee el PDF del examen, extrae los objetivos y configura automáticamente course.config.js con la estructura de unidades, lecciones y temas. También crea las carpetas del curso y sugiere un escenario pedagógico.
---

# Skill: Inicializar el curso desde el PDF del examen

## Cuándo usarlo
Al comenzar un curso nuevo. Se ejecuta UNA SOLA VEZ (o cuando cambia la estructura del examen).

## Lo que hace
1. Lee el PDF del examen con `fitz` (pymupdf)
2. Extrae los dominios (→ Unidades), objetivos (→ Lecciones) y sub-objetivos (→ Temas)
3. Escribe la sección `units` en `course.config.js`
4. Crea las carpetas del curso
5. Sugiere un escenario pedagógico apropiado para el tema

## Pasos de ejecución

### 1. Encontrar el PDF
Busca en la raíz del proyecto un archivo `.pdf`. Si hay más de uno, pregunta al usuario cuál es el del examen.

### 2. Leer el PDF
```python
import fitz  # pip install pymupdf
doc = fitz.open("ruta/al/examen.pdf")
texto = "\n".join(page.get_text() for page in doc)
```

### 3. Extraer la estructura
El PDF de objetivos ITS tiene esta jerarquía típica:
- **Dominio** (ej. "1. Data Basics — 15–20%") → Unidad
- **Objetivo** (ej. "1.1 Define the concept of data science") → Lección
- **Sub-objetivo** (ej. "1.1.1 Fundamental disciplines") → Tema

Extrae cada nivel y constrúyelos como objetos JavaScript.

### 4. Actualizar course.config.js
Lee el archivo actual, reemplaza solo el campo `units` y el `scenario` (si está vacío), conserva todo lo demás.

Formato de cada unidad:
```js
{
  id: 1,
  title: "Nombre de la unidad en español",
  folderName: "Unidad 1 - Nombre de la unidad",
  lessons: [
    {
      id: "1.1",
      title: "Título de la lección en español",
      objective: "Texto del objetivo del examen",
      topics: [
        { id: "1.1.1", title: "Título del tema en español" },
      ],
    },
  ],
}
```

**Traducir al español** si el PDF está en inglés. El curso se imparte en español.

### 5. Crear carpetas
Para cada unidad en `units`:
```bash
mkdir -p "Unidad N - Nombre/Teoría"
mkdir -p "Unidad N - Nombre/Preguntas"
mkdir -p "Unidad N - Nombre/Actividades"
mkdir -p "Unidad N - Nombre/Contenido HTML"
mkdir -p "Unidad N - Nombre/Proyecto"
```

### 6. Sugerir escenario
Si `scenario.name` está vacío, propone un nombre y descripción de empresa ficticia coherente con el tema del curso. Pide confirmación antes de escribirlo.

### 7. Seleccionar estilo gráfico
Indica al autor:

> **Paso opcional: elige el estilo visual del curso.**
> Abre `_tools/theme-gallery.html` en el navegador para ver una muestra de los 5 estilos disponibles (Ocean, Forest, Obsidian, Amber, Crimson). Cuando elijas uno, haz clic en **Seleccionar** — el ID se copiará al portapapeles — y luego escríbelo en `course.config.js → theme`. Por ahora el curso usa el estilo predeterminado `"ocean"`.

No esperes confirmación para continuar; el autor puede cambiar el tema en cualquier momento editando `course.config.js`.

## Al terminar
Muestra un resumen:
- Cuántas unidades, lecciones y temas se extrajeron
- Qué carpetas se crearon
- Cuál es el escenario sugerido
- Estilo gráfico activo (el valor actual de `course.config.js → theme`)

Pregunta si el usuario quiere ajustar algo antes de continuar.
