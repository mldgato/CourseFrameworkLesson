#!/usr/bin/env python3
"""Reajusta los at(t) de un anim.txt viejo a una narración nueva (palabras alineadas entre cues viejos y nuevos).
Uso: python3 retime_cues.py cues_viejo.txt cues_nuevo.txt anim_entrada.txt anim_salida.txt
Las palabras que coinciden en ambas narraciones fijan anclas; entre anclas se interpola linealmente.
Siempre revisar después con kit.py snap (las escenas cuyo texto cambió quedan aproximadas)."""
import re, sys, difflib, bisect
def words(p):
    t = open(p, encoding="utf-8").read().split("## Palabras", 1)[1]
    out = []
    for m in re.finditer(r"(\d+(?:\.\d+)?):(\S+)", t):
        w = re.sub(r"[^\wáéíóúüñ]", "", m.group(2).lower())
        if w: out.append((float(m.group(1)), w))
    return out
old, new = words(sys.argv[1]), words(sys.argv[2])
sm = difflib.SequenceMatcher(None, [w for _, w in old], [w for _, w in new], autojunk=False)
anch = []
for b in sm.get_matching_blocks():
    for k in range(b.size): anch.append((old[b.a + k][0], new[b.b + k][0]))
anch.sort()
xs = [a for a, _ in anch]; ys = [b for _, b in anch]
def mp(t):
    if not xs: return t
    if t <= xs[0]: return ys[0] + (t - xs[0])
    if t >= xs[-1]: return ys[-1] + (t - xs[-1])
    i = bisect.bisect_right(xs, t) - 1
    x0, x1, y0, y1 = xs[i], xs[i + 1], ys[i], ys[i + 1]
    return y0 if x1 == x0 else y0 + (t - x0) * (y1 - y0) / (x1 - x0)
s = open(sys.argv[3], encoding="utf-8").read()
s = re.sub(r"at\((\d+(?:\.\d+)?)\)", lambda m: "at(%.1f)" % mp(float(m.group(1))), s)
s = re.sub(r"\((\d+(?:\.\d+)?) – (\d+(?:\.\d+)?)\)", lambda m: "(%.1f – %.1f)" % (mp(float(m.group(1))), mp(float(m.group(2)))), s)
open(sys.argv[4], "w", encoding="utf-8").write(s)
print("anclas: %d de %d palabras viejas / %d nuevas" % (len(anch), len(old), len(new)))
