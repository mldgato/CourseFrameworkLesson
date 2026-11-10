# DESIGN — Videos por tema

## Style Prompt
Explicador didáctico, sobrio y nítido. Lienzo oscuro navy con una cuadrícula técnica muy tenue (guiño a la cuadrícula del ebook del curso). Un solo acento azul cielo. La tipografía cinética lleva el peso: el concepto aparece "suelto" y frío, y al recibir contexto se ensambla y se ilumina. Movimiento preciso y sereno, sin rebotes; entradas suaves con power3/expo, sin salidas antes de un barrido. Escenario único de ejemplos: el de course.config.js → scenario.name.

## Colors (contenido)
- Fondo: `#0b2238` · Superficie/tarjetas: `#123a5c` · Texto: `#eaf4fb` · Texto secundario: `#9fbdd6` · Acento único: `#4fb3ea`

## Colors (INTRO y CIERRE — pantallas de marca, fondo claro)
- Fondo `#fbfdff` con cuadrícula `#e3edf5` (80 px, como el ebook). Barra de acento `#1a6fa3` (280×8 px).
- Motivo: LogoCurso.png (azul marino sobre transparente) y etc_iberoamerica_logo.svg (gris `#313b44` + naranja) son oscuros: NUNCA se colocan sobre el navy del contenido.

## Typography
- Titulares/frases: **Fraunces** (serif, 300 vs 800). Datos/etiquetas: **JetBrains Mono** (400/700). Nunca dos sans.
- Titulares 90 px+, cuerpo 34 px+, etiquetas 26 px+. Los .woff2 viven en assets/fonts/ (embebidos localmente; el compilador no resuelve Fraunces solo).

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
