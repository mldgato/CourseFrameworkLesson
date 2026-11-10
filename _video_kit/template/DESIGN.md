# DESIGN — Videos por tema

## Style Prompt
Explicador didáctico, sobrio y nítido. Lienzo oscuro navy con una cuadrícula técnica muy tenue (guiño a la cuadrícula del ebook del curso) **— excepto cuando el tema tiene `noGrid: true` en `_tools/themes.json`; en ese caso el fondo del contenido es limpio, sin cuadrícula**. Un solo acento de color. La tipografía cinética lleva el peso: el concepto aparece "suelto" y frío, y al recibir contexto se ensambla y se ilumina. Movimiento preciso y sereno, sin rebotes; entradas suaves con power3/expo, sin salidas antes de un barrido. Escenario único de ejemplos: el de course.config.js → scenario.name.

## Colors y tipografía — se toman del tema activo

Los colores y fuentes del video provienen de `course.config.js → theme`, vía `_tools/themes.json`.
Lee el skill `/videos` (Paso 0) para ver cómo cargarlos. Los valores de referencia para el tema
predeterminado `"ocean"` son los siguientes; **si el tema es otro, usa los valores del tema
elegido en su lugar**.

### Colors (contenido) — tema "ocean" como referencia
- Fondo: `{video.bg}` · Superficie/tarjetas: `{video.surface}` · Texto: `{video.text}` · Texto secundario: `{video.text2}` · Acento único: `{video.accent}`

### Colors (INTRO y CIERRE — pantallas de marca, fondo claro) — tema "ocean" como referencia
- Fondo `{video.introBg}` con cuadrícula `{video.introGrid}` (80 px). Si `video.introGrid` es `transparent` (tema `noGrid`), omite completamente el `background-image` de cuadrícula; el fondo queda liso. Barra de acento `{video.introBar}` (280×8 px).
- Motivo: LogoCurso.png (azul marino sobre transparente) y etc_iberoamerica_logo.svg (gris `#313b44` + naranja) son oscuros: NUNCA se colocan sobre un fondo oscuro del contenido.

### Typography — tema "ocean" como referencia
- Titulares/frases: **`{video.fontHeading}`** (archivo: `{video.fontHeadingFile}`). Datos/etiquetas: **`{video.fontMono}`** (archivo: `{video.fontMonoFile}`). Nunca dos sans.
- Si el archivo .woff2 del tema no existe en `assets/fonts/`, usa `fraunces.woff2` / `jetbrains-mono.woff2` como fallback.
- Titulares 90 px+, cuerpo 34 px+, etiquetas 26 px+. Los .woff2 viven en assets/fonts/ (embebidos localmente).

## Estructura fija de cada video
1. INTRO ≤ 3 s: LogoCurso.png (aparece, barra de acento, barrido de salida). La narración arranca justo al terminar (t = INTRO).
2. CONTENIDO: narración de ~2–3 min con escenas sincronizadas palabra por palabra.
3. Pausa breve (~0.9 s) y CIERRE (~4.6 s): "Un curso desarrollado por" + logo ETC Iberoamérica, con desvanecido final.

## What NOT to Do
- Sin emojis ni íconos decorativos. Sin degradados de texto ni neón cian/púrpura. Sin `#000`/`#fff` puros en el contenido.
- Sin salidas (exit tweens) antes de un barrido; solo en el cierre.
- Una idea por pantalla; nada de párrafos. Texto legible ≥ 2 s.
- Moneda: `$`/"dólares" (nunca quetzales ni €). Sin acento ni vocabulario de España en el guion.
- Sin la palabra "nova". Los ejemplos usan siempre el escenario de course.config.js → scenario.name (o se marcan como datos ilustrativos).
