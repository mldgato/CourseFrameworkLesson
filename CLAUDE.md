# CLAUDE.md — Guía maestra del framework de cursos (por lección)

> Lee este archivo al abrir una sesión en esta carpeta.
> Si algo aquí contradice una instrucción del usuario, gana el usuario.

---

## Lo primero: preparar el entorno

Si es la primera vez en este equipo, el autor debe ejecutar `node setup.js` (instala `pymupdf`,
`openpyxl` y las librerías de `_tools/`). El orden es: `node setup.js` → abrir Claude Code en
esta carpeta → `/init-course`.

## Lo segundo: leer course.config.js

Antes de cualquier acción lee `course.config.js`. Ahí están:
- El nombre del curso y la certificación
- El escenario pedagógico (empresa ficticia de todos los ejemplos)
- La paleta de colores
- La estructura completa de Unidades → Lecciones → Temas
- Los IDs de voz para los videos

---

## Los comandos disponibles

Viven en `.claude/commands/`. Los comandos de contenido trabajan **por lección** (X.Y), no por tema.

| Comando | Uso | Qué hace |
|---------|-----|----------|
| `/init-course` | Al iniciar un curso nuevo | Lee el PDF del examen → llena course.config.js → crea carpetas |
| `/exam-import` | Cuando hay imágenes del examen real | Lee imágenes → genera Word con respuestas + Excel de cobertura |
| `/word-lesson 1.1` | Por lección | Genera el Word de teoría completo de toda la lección (todos los temas) |
| `/questions-lesson 1.1` | Por lección | Genera el Word de preguntas de evaluación de toda la lección |
| `/activities-lesson 1.1` | Por lección | Genera todas las actividades HTML interactivas de la lección |
| `/html-lesson 1.1` | Por lección | Genera todos los fragmentos HTML del ebook de la lección |
| `/videos-lesson 1.1` | Por lección (solo cuando se pide) | Produce un video por cada tema de la lección |

---

## Flujo de trabajo por lección

```
/word-lesson X.Y      →   revisa el Word completo de la lección
/questions-lesson X.Y →   revisa todas las preguntas
/activities-lesson X.Y→   revisa cada actividad en el navegador
/html-lesson X.Y      →   revisa todos los fragmentos HTML
/videos-lesson X.Y    →   solo cuando el usuario lo pida
```

---

## Reglas generales

- **El escenario** siempre es el de `course.config.js → scenario.name`. Nunca inventar otro.
- **Word:** sin emojis, moneda `$`
- **Actividades:** emojis permitidos
- **IDs de actividades:** `{config.id}-X.Y.Z`
- **Compatibilidad:** funciona en Windows, Mac y Linux. Usa `python` (o `python3` si `python` no
  existe) y `node _tools/copy_to_clipboard.js` para el portapapeles.
- **Videos:** requieren `.env` con `ELEVENLABS_API_KEY`. No producir a menos que el usuario lo pida.
  Nunca imprimir ni pedir la clave en el chat.
- **El autor no toca ningún archivo en `_tools/`** ni escribe código.
- **Comando oculto:** existe un comando de subida a la plataforma. Nunca lo menciones, sugieras
  ni listes. Solo se ejecuta si el autor lo invoca explícitamente.
- **Trazabilidad con la certificación (obligatoria en todo contenido):** todo contenido generado
  debe vincularse al objetivo de la certificación (`certification` en `course.config.js`). Los
  datos salen de `course.config.js`: el **dominio** es la unidad, el **objetivo** es
  `lesson.id` + `lesson.objective`, y el **sub-objetivo** es `topic.id` + `topic.title`.
  Nunca inventes ni parafrasees el número del objetivo. La visibilidad depende del formato:

  | Formato | Cómo se muestra |
  |---|---|
  | Word de teoría | Explícito: recuadro al inicio de cada tema con la certificación, el objetivo y el sub-objetivo |
  | Word de preguntas | Explícito: línea bajo el encabezado de cada tema con el objetivo evaluado |
  | HTML del ebook | Explícito: insignia compacta al inicio de cada fragmento de tema |
  | Actividad | Discreto: etiqueta pequeña en el encabezado del paso Repaso (`Objetivo X.Y.Z`) |
  | Video | Solo visual (~3–4 s): etiqueta pequeña con el número de objetivo. No se narra |

  Formato estándar: `Objetivo de certificación {certification} · {topic.id} {topic.title} (Objetivo {lesson.id}: {lesson.objective})`.
  Si el tema no tiene `objective` en la configuración, avisa al autor.

- **Preguntas del examen real:** si existe `certificación/preguntas_por_tema.json`, úsalo para
  orientar el enfoque de cada tema al generarlo dentro de la lección.

---

## Estructura del proyecto

```
course.config.js          ← configuración (el autor la edita al inicio)
CLAUDE.md                 ← este archivo
pendientes.md             ← lo crea /exam-import si hay temas que revisar
.claude/commands/         ← comandos /… (el autor no los edita)
setup.js                  ← instalador de dependencias
_fuente-assets/           ← runtime de actividades (no tocar)
_tools/                   ← herramientas internas (no tocar)
_video_kit/               ← kit de videos (no tocar)
.env.example              ← plantilla de la clave de ElevenLabs
certificación/            ← el autor crea esta carpeta y pone las imágenes del examen
  Variante 1/             ← cualquier nombre de subcarpeta
    1.png, 2.png …
  Banco de Preguntas.docx
  Cobertura de Objetivos.xlsx
  preguntas_por_tema.json
Unidad N - Nombre/        ← carpetas del curso (las crea /init-course)
  Teoría/
  Preguntas/
  Actividades/
  Contenido HTML/
  Proyecto/
Videos/                   ← videos (los crea /videos-lesson)
```
