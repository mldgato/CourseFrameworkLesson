#!/usr/bin/env python3
"""Genera _partes/anim.txt a partir de _partes/anim.spec y cues.txt.

Uso: python3 _video_kit/tools/build_anim.py 3.2.1

anim.spec (una instruccion por linea, '#' comenta):
  S <n> "frase"            escena n arranca (barrido) cuando se dice la frase; la 1 usa 0.3 y no lleva wipe
  E <id> "frase" <tipo>    el elemento entra cuando se dice la frase (busqueda monotona hacia adelante)
Tipos: y (sube), xl (desde izquierda), xr (desde derecha), chip (rebote), pop (escala)
La frase se busca en la secuencia de palabras de cues.txt (sin mayusculas ni puntuacion).
"""
import re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def norm(w):
    w = unicodedata.normalize("NFC", w.lower())
    return re.sub(r"[^\w]", "", w)

def load_words(cues):
    txt = cues.read_text(encoding="utf-8")
    part = txt.split("## Palabras", 1)[1]
    words = []
    for m in re.finditer(r"([0-9]+(?:\.[0-9]+)?):(\S+)", part):
        words.append((float(m.group(1)), norm(m.group(2))))
    return [w for w in words if w[1]]

def find(words, phrase, start):
    toks = [norm(t) for t in phrase.split() if norm(t)]
    for i in range(start, len(words) - len(toks) + 1):
        if all(words[i + k][1] == toks[k] for k in range(len(toks))):
            return i, words[i][0]
    raise SystemExit(f"No encuentro la frase '{phrase}' despues de la palabra {start}")

KINDS = {
    "y": 'y: 40, opacity: 0, duration: 0.6, ease: "power3.out"',
    "xl": 'x: -50, opacity: 0, duration: 0.5, ease: "expo.out"',
    "xr": 'x: 50, opacity: 0, duration: 0.5, ease: "expo.out"',
    "chip": 'y: 26, opacity: 0, duration: 0.5, ease: "back.out(1.6)"',
    "pop": 'scale: 0.85, opacity: 0, duration: 0.5, ease: "back.out(1.4)"',
}

def main(t):
    base = next((ROOT / "Videos").glob(f"Unidad */_fuente_{t}"))
    words = load_words(base / "cues.txt")
    spec = (base / "_partes" / "anim.spec").read_text(encoding="utf-8")
    out, pos, prev = [], 0, None
    for raw in spec.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'S\s+(\d+)\s+"(.+)"$', line)
        if m:
            n, phrase = int(m.group(1)), m.group(2)
            if n == 1:
                out.append(f"      /* ===== ESCENA 1 ===== */")
                out.append('      tl.from("#s1-eyebrow", { y: -24, opacity: 0, duration: 0.6, ease: "power2.out" }, at(0.3));')
                out.append('      tl.from("#s1-h", { y: 60, opacity: 0, duration: 0.8, ease: "power3.out" }, at(0.5));')
                prev = 1
                continue
            i, tm = find(words, phrase, pos)
            pos = i
            out.append(f"\n      /* ===== ESCENA {n} ({tm:.1f}) ===== */")
            out.append(f'      wipe("#s{n}", at({tm:.1f}), "#s{prev}");')
            out.append(f'      tl.from("#s{n}-h", {{ y: 40, opacity: 0, duration: 0.6, ease: "power3.out" }}, at({tm + 0.3:.1f}));')
            prev = n
            continue
        m = re.match(r'E\s+(\S+)\s+"(.+)"\s+(\w+)$', line)
        if m:
            sel, phrase, kind = m.groups()
            i, tm = find(words, phrase, pos)
            pos = i
            target = sel if sel.startswith(("#", ".")) else "#" + sel
            out.append(f'      tl.from("{target}", {{ {KINDS[kind]} }}, at({tm:.1f}));')
            continue
        raise SystemExit(f"Linea no valida: {line}")
    (base / "_partes" / "anim.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"anim.txt escrito ({len(out)} lineas) para {t}")

if __name__ == "__main__":
    main(sys.argv[1])
