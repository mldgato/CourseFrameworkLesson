#!/bin/bash
# Uso: split_for_upload.sh X.Y.Z ...  -> _video_upload_tmp/X.Y.Z/part?.bin (trozos de 9 MB) e imprime id|tamaño|nombre sin .mp4
cd "$(dirname "$0")/../.." || exit 1
for t in "$@"; do
  f=$(ls Videos/Unidad\ */"$t "*.mp4 2>/dev/null | head -1)
  [ -z "$f" ] && { echo "NO MP4 $t"; continue; }
  mkdir -p "_video_upload_tmp/$t"; rm -f "_video_upload_tmp/$t"/part*
  split -b 9437184 -d -a 1 "$f" "_video_upload_tmp/$t/part"
  for p in _video_upload_tmp/$t/part?; do mv "$p" "$p.bin"; done
  b=$(basename "$f" .mp4)
  echo "$t|$(stat -f %z "$f")|$b|$(ls _video_upload_tmp/$t | wc -l | tr -d ' ')"
done
