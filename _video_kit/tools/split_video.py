#!/usr/bin/env python3
"""Parte un mp4 en trozos de 9 MB dentro de _video_upload_tmp/<X.Y.Z>/ (para subirlo con file_upload, limite 10 MB)."""
import glob, os, sys
tid = sys.argv[1]
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
f = glob.glob(os.path.join(root, "Videos", "Unidad *", tid + " *.mp4"))
if not f:
    sys.exit("no hay mp4 para " + tid)
f = f[0]
out = os.path.join(root, "_video_upload_tmp", tid)
os.makedirs(out, exist_ok=True)
size = os.path.getsize(f); n = 0; CH = 9 * 1024 * 1024
with open(f, "rb") as src:
    while True:
        b = src.read(CH)
        if not b: break
        n += 1
        open(os.path.join(out, "part%d.bin" % n), "wb").write(b)
print(json_out := "%s|%d|%d|%s" % (os.path.basename(f)[:-4], size, n, out))
