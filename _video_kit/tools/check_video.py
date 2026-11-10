#!/usr/bin/env python3
"""Extrae 6 fotogramas del MP4 final de un tema y los junta en una hoja de contactos.

Uso:  python _video_kit/tools/check_video.py X.Y.Z
Salida: Videos/Unidad N/_fuente_X.Y.Z/final_check.png  (y muestra duración del video)
"""
try:
    import sys as _s; _s.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import glob, os, subprocess, sys, tempfile

if len(sys.argv) < 2:
    sys.exit(__doc__)
tid = sys.argv[1]
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
mp4s = [p for p in glob.glob(os.path.join(ROOT, "Videos", "Unidad *", tid + " *.mp4"))]
if not mp4s:
    sys.exit("No hay MP4 final para " + tid)
mp4 = mp4s[0]
folder = glob.glob(os.path.join(ROOT, "Videos", "Unidad *", "_fuente_" + tid))[0]
plat = glob.glob(os.path.join(ROOT, "_video_kit", "entorno", "*"))
ffmpeg = ffprobe = None
for d in plat:
    for base in ("ffmpeg", "ffprobe"):
        for ext in (".exe", ""):
            p = os.path.join(d, "bin", base + ext)
            if os.path.exists(p):
                if base == "ffmpeg": ffmpeg = ffmpeg or p
                else: ffprobe = ffprobe or p
if not ffmpeg or not ffprobe:
    sys.exit("Falta ffmpeg/ffprobe: corre  python _video_kit/kit.py setup")

dur = float(subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4],
                           capture_output=True, text=True).stdout.strip())
times = [1.5, dur * 0.15, dur * 0.35, dur * 0.55, dur * 0.8, dur - 3.0]
tmp = tempfile.mkdtemp()
for i, t in enumerate(times):
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-ss", "%.2f" % t, "-i", mp4, "-frames:v", "1",
                    "-vf", "scale=640:-1", os.path.join(tmp, "f%d.png" % i)], check=True)
out = os.path.join(folder, "final_check.png")
subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", os.path.join(tmp, "f%d.png"), "-filter_complex", "tile=3x2",
                "-frames:v", "1", out], check=True)
print("video:", os.path.basename(mp4), "| duración: %.1f s" % dur)
print("hoja de contactos:", out)
