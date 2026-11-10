#!/usr/bin/env python3
"""Ensambla las escenas de un tema en su index.html y lo valida.

Uso:  python _video_kit/tools/assemble_scenes.py X.Y.Z [carpeta_partes]

Lee tres archivos de texto (por defecto en Videos/Unidad N/_fuente_X.Y.Z/_partes/):
  css.txt     estilos propios de las escenas
  scenes.txt  el HTML de las <section class="scene"> (ids s1..sN)
  anim.txt    las animaciones (todo tiempo de contenido con at(t))
y los inserta en la plantilla que dejó `kit.py scaffold` (index.html). Luego corre
`hyperframes validate` y muestra el resultado. El index.html debe ser la plantilla
recién creada (aún sin escenas): si ya fue ensamblado, vuelve a hacer scaffold.
"""
try:
    import sys as _s; _s.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import glob, os, re, subprocess, sys

if len(sys.argv) < 2:
    sys.exit(__doc__)
tid = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
found = glob.glob(os.path.join(ROOT, "Videos", "Unidad *", "_fuente_" + tid))
if not found:
    sys.exit("No existe la carpeta _fuente_%s (haz primero kit.py scaffold %s)" % (tid, tid))
folder = found[0]
parts = sys.argv[2] if len(sys.argv) > 2 else os.path.join(folder, "_partes")

def rd(name):
    with open(os.path.join(parts, name), encoding="utf-8") as f:
        return f.read()

idx = os.path.join(folder, "index.html")
tpl = open(idx, encoding="utf-8").read()
if "ANIMACIONES DE CONTENIDO" not in tpl or 'id="s1"' not in tpl:
    sys.exit("index.html no parece la plantilla recién creada (¿ya estaba ensamblado?)")
css, scenes, anim = rd("css.txt"), rd("scenes.txt"), rd("anim.txt")

marker = "      /* ---------- INTRO y CIERRE"
if marker not in tpl:
    sys.exit("No encuentro el marcador de INTRO y CIERRE en la plantilla")
tpl = tpl.replace(marker, "      /* ---------- escenas de contenido (tema %s) ---------- */\n%s\n%s" % (tid, css, marker), 1)

a = tpl.index('      <section class="scene" id="s1">')
b = tpl.index("      <!-- ================= FIN ESCENAS DE CONTENIDO")
tpl = tpl[:a] + scenes + "\n" + tpl[b:]

start = "      /* ================= ANIMACIONES DE CONTENIDO (reemplazar/extender por tema) ================= */\n"
a = tpl.index(start) + len(start)
b = tpl.index("      /* ================= FIN ANIMACIONES DE CONTENIDO")
tpl = tpl[:a] + anim + "\n" + tpl[b:]
open(idx, "w", encoding="utf-8").write(tpl)

bad = [l for l in anim.split("\n") if re.search(r"\},\s*\d+(\.\d+)?\);", l)]
print("líneas con tiempo sin at():", len(bad))
for l in bad:
    print("  ", l.strip())

npx = "npx.cmd" if os.name == "nt" else "npx"
r = subprocess.run([npx, "hyperframes@0.6.70", "validate"], cwd=folder, capture_output=True, text=True, encoding="utf-8", errors="replace")
out = (r.stdout or "") + (r.stderr or "")
lines = [l for l in out.splitlines() if l.strip()]
print("validate:", "\n".join(lines[:12]))
sys.exit(0 if "No console errors" in out else 1)
