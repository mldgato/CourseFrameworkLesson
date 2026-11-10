#!/usr/bin/env python3
"""Genera _partes/{css,scenes,anim}.txt de un video a partir de una especificación en Python.
Uso (dentro de un script): from vbuild import *; V=Video("3.1.1","Tema 3.1.1 · SELECT básico","Leer <em>datos</em>")
  s=V.scene(start,end,"Título con <em>énfasis</em>", first=False)   # la 1.ª escena lleva eyebrow + h1 grande
  s.code(lines, t, lt, size=34, width=1500, hl=[])      # lines: HTML por línea; lt: tiempos por línea
  s.nb2((k1,v1),(k2,v2), t1, t2)                          # dos cajas
  s.tags([(texto,t,fill),...], size=36)                   # fila de chips
  s.chip(texto,t,fill=False,size=36)
  s.card(k,ti,de,t,tde)                                   # tarjeta (de opcional)
  s.table(cols,widths,rows,th_t,size=30)                  # rows: [(cells,t,clases por celda opcional)]
  s.steps([(texto,t),...])
  V.write()   # escribe _partes/ (css copiado de 2.3.3) y llama a assemble_scenes
Los tiempos t son segundos de la NARRACIÓN (cues.txt); at() ya suma la intro."""
import os, sys, shutil, subprocess, html as _h
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
E = {"y": 'y: 40, opacity: 0, duration: 0.6, ease: "power3.out"', "x": 'x: -40, opacity: 0, duration: 0.5, ease: "expo.out"',
     "xr": 'x: 40, opacity: 0, duration: 0.5, ease: "expo.out"', "xl": 'x: -60, opacity: 0, duration: 0.6, ease: "expo.out"',
     "xrr": 'x: 60, opacity: 0, duration: 0.6, ease: "expo.out"', "chip": 'y: 26, opacity: 0, duration: 0.5, ease: "back.out(1.6)"',
     "code": 'y: 30, opacity: 0, duration: 0.5, ease: "power3.out"', "eb": 'y: -24, opacity: 0, duration: 0.6, ease: "power2.out"',
     "h1": 'y: 60, opacity: 0, duration: 0.8, ease: "power3.out"', "fade": 'opacity: 0, y: 14, duration: 0.5, ease: "power2.out"',
     "row": 'x: -60, opacity: 0, duration: 0.5, ease: "expo.out"', "th": 'y: 30, opacity: 0, duration: 0.5, ease: "power3.out"'}
class Scene:
    def __init__(s, v, n, start, end, title, first, eyebrow):
        s.v, s.n, s.start, s.end, s.title, s.first, s.eyebrow = v, n, start, end, title, first, eyebrow
        s.html, s.anim, s.k = [], [], 0
    def _id(s): s.k += 1; return "%s%d" % (chr(96 + s.n), s.k)
    def _a(s, i, kind, t): s.anim.append('      tl.from("#%s", { %s }, at(%.1f));' % (i, E[kind], t))
    def code(s, lines, t, lt, size=34, width=1500, hl=()):
        cid = "code%d" % s.n; ids = []
        out = ['<div class="code" id="%s" style="width:%dpx;font-size:%dpx">' % (cid, width, size)]
        for j, l in enumerate(lines):
            i = s._id(); ids.append(i); out.append('  <span class="ln2%s" id="%s">%s</span>' % (" hl" if j in hl else "", i, l))
        out.append('</div>'); s.html.append("\n".join(out)); s._a(cid, "code", t)
        for i, tt in zip(ids, lt): s._a(i, "x", tt)
    def nb2(s, a, b, t1, t2, w=560, h=180):
        i1, i2 = s._id(), s._id()
        s.html.append('<div class="row" style="gap:50px"><div class="nb" id="%s" style="width:%dpx;height:%dpx"><div class="k">%s</div><div class="v serif" style="font-size:42px">%s</div></div>'
                      '<div class="nb" id="%s" style="width:%dpx;height:%dpx;border-color:#4fb3ea"><div class="k">%s</div><div class="v serif" style="font-size:42px">%s</div></div></div>' % (i1, w, h, a[0], a[1], i2, w, h, b[0], b[1]))
        s._a(i1, "xl", t1); s._a(i2, "xrr", t2)
    def tags(s, items, size=36):
        sp = []
        for txt, t, fill in items:
            i = s._id(); sp.append('<span class="chip%s" id="%s" style="font-size:%dpx">%s</span>' % (" fill" if fill else "", i, size, txt)); s._a(i, "chip", t)
        s.html.append('<div class="tags" style="min-height:0">%s</div>' % "".join(sp))
    def chip(s, txt, t, fill=False, size=36):
        i = s._id(); s.html.append('<span class="chip%s" id="%s" style="font-size:%dpx">%s</span>' % (" fill" if fill else "", i, size, txt)); s._a(i, "xr" if fill else "chip", t)
    def card(s, k, ti, de, t, tde=None, w=1400, size=46):
        i = s._id(); d = ""
        if de: di = i + "d"; d = '<div class="de" id="%s">%s</div>' % (di, de)
        s.html.append('<div class="card" id="%s" style="width:%dpx"><div class="k">%s</div><div class="ti serif" style="font-size:%dpx">%s</div>%s</div>' % (i, w, k, size, ti, d))
        s._a(i, "y", t)
        if de: s._a(di, "fade", tde if tde else t + 3)
    def table(s, cols, widths, rows, th_t, size=30):
        g = "grid-template-columns:" + " ".join("%dpx" % w for w in widths); tot = sum(widths) + 6 * (len(widths) - 1)
        out = ['<div class="tb" style="width:%dpx">' % tot, '  <div class="tr th" style="%s">%s</div>' % (g, "".join("<span>%s</span>" % c for c in cols))]
        ids = []
        for r in rows:
            cells, t = r[0], r[1]; cls = r[2] if len(r) > 2 else [""] * len(cells); i = s._id(); ids.append((i, t))
            out.append('  <div class="tr" id="%s" style="%s;font-size:%dpx">%s</div>' % (i, g, size, "".join('<span%s>%s</span>' % (' class="%s"' % c if c else "", x) for x, c in zip(cells, cls))))
        out.append('</div>'); s.html.append("\n".join(out)); s.anim.append('      tl.from("#s%d .tr.th", { %s }, at(%.1f));' % (s.n, E["th"], th_t))
        for i, t in ids: s._a(i, "row", t)
    def steps(s, items):
        for txt, t in items:
            i = s._id(); s.html.append('<div class="stp" id="%s"><b>%d</b><span>%s</span></div>' % (i, int(i[1:]), txt)); s._a(i, "y", t)
class Video:
    def __init__(s, vid, eyebrow, h1, h1size=112):
        s.vid, s.eyebrow, s.h1, s.h1size, s.scenes = vid, eyebrow, h1, h1size, []
    def scene(s, start, end, title=None, first=False):
        n = len(s.scenes) + 1; sc = Scene(s, n, start, end, title if title else s.h1, first, s.eyebrow if first else None); s.scenes.append(sc); return sc
    def write(s):
        folder = [d for d in __import__("glob").glob(os.path.join(ROOT, "Videos", "Unidad *", "_fuente_" + s.vid))][0]
        parts = os.path.join(folder, "_partes"); os.makedirs(parts, exist_ok=True)
        shutil.copy(os.path.join(ROOT, "Videos", "Unidad 2", "_fuente_2.3.3", "_partes", "css.txt"), os.path.join(parts, "css.txt"))
        sh, an = [], []
        for sc in s.scenes:
            head = ""
            if sc.first:
                head = '        <div class="eyebrow" id="s1-eyebrow">%s</div>\n        <div class="h1" id="s1-h" style="font-size:%dpx">%s</div>\n' % (sc.eyebrow, s.h1size, sc.title)
            else:
                head = '        <div><div class="h1" id="s%d-h">%s</div></div>\n' % (sc.n, sc.title)
            body = "\n".join("            " + l.replace("\n", "\n            ") for l in sc.html)
            sh.append('      <section class="scene" id="s%d"><div class="pad">\n%s        <div class="stage">\n          <div class="stg">\n%s\n          </div>\n        </div>\n      </div></section>\n' % (sc.n, head, body))
            an.append("\n      /* =========== ESCENA %d (%.1f – %.1f) =========== */" % (sc.n, sc.start, sc.end))
            if sc.n > 1: an.append('      wipe("#s%d", at(%.1f), "#s%d");' % (sc.n, sc.start, sc.n - 1))
            if sc.first: an.append('      tl.from("#s1-eyebrow", { %s }, at(0.3));\n      tl.from("#s1-h", { %s }, at(0.5));' % (E["eb"], E["h1"]))
            else: an.append('      tl.from("#s%d-h", { %s }, at(%.1f));' % (sc.n, E["y"], sc.start + 0.3))
            an.extend(sc.anim)
        open(os.path.join(parts, "scenes.txt"), "w", encoding="utf-8").write("\n".join(sh))
        open(os.path.join(parts, "anim.txt"), "w", encoding="utf-8").write("\n".join(an).lstrip("\n") + "\n")
        print("escenas:", len(s.scenes), "| animaciones:", sum(1 for l in an if "tl.from" in l))
        r = subprocess.run([sys.executable, os.path.join(ROOT, "_video_kit", "tools", "assemble_scenes.py"), s.vid], capture_output=True, text=True)
        print("\n".join(r.stdout.strip().split("\n")[-3:]), r.stderr[-300:])
