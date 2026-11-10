#!/usr/bin/env python3
"""Toma capturas al final de cada escena (segundo de la siguiente escena - 0.6, + intro 3 s)."""
import re, subprocess, sys
from pathlib import Path
t = sys.argv[1]
root = Path(__file__).resolve().parents[2]
base = next((root / "Videos").glob(f"Unidad */_fuente_{t}"))
anim = (base / "_partes" / "anim.txt").read_text(encoding="utf-8")
starts = [float(x) for x in re.findall(r'wipe\("#s\d+", at\(([\d.]+)\)', anim)]
cues = (base / "cues.txt").read_text(encoding="utf-8")
end = max(float(m) for m in re.findall(r"-\s*([\d.]+)\s", cues.split("## Palabras")[0]))
ts = [s + 3 - 0.6 for s in starts] + [end + 3 - 0.3]
subprocess.run([sys.executable, str(root / "_video_kit/kit.py"), "snap", t, "--at", ",".join(f"{x:.1f}" for x in ts)])
