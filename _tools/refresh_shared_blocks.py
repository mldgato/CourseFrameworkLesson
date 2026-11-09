#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidad reutilizable (ver CLAUDE.md §7.6): dado un archivo de actividad ya
construido, reemplaza los bloques <script> embebidos de motor-sql.js, sql-ui.js
y quiz.js por el contenido ACTUAL de _fuente-assets/, y quita el paso de
Evaluación + widgets + invocaciones ya inyectados por inject_preguntas.py (para
que el archivo quede en estado "recién copiado, sin preguntas inyectadas" y se
le pueda correr inject_preguntas.py normal después, como con una actividad nueva).

No toca: <style>, xperienceed.js, datos.js, deck.js, ni el contenido propio de
los pasos/tema (eso se edita a mano después).

Uso: python3 refresh_shared_blocks.py entrada.html salida.html
"""
import re
import sys
import os

ASSETS = os.path.join(os.path.dirname(__file__), "..", "_fuente-assets")

SIGNATURES = [
    ("Mini-motor SQL (SELECT) para el curso ITS Databases.", "motor-sql.js"),
    ("Widgets SQL del curso: esquema, playground y ejercicios autoevaluados.", "sql-ui.js"),
    ("Widgets de evaluación conceptual (sin SQL): elección y clasificación.", "quiz.js"),
]


def read_asset(name):
    with open(os.path.join(ASSETS, name), encoding="utf-8") as f:
        return f.read().strip("\n")


def replace_script_block(content, signature, new_body):
    """Reemplaza el <script>...</script> que contiene el texto `signature`
    en algún punto cerca de su inicio (independientemente de en qué línea del
    comentario de apertura aparezca)."""
    sig_idx = content.find(signature)
    if sig_idx == -1:
        raise SystemExit("No se encontró la firma en el archivo: " + signature)
    start = content.rfind("<script>", 0, sig_idx)
    if start == -1:
        raise SystemExit("No se encontró '<script>' antes de la firma: " + signature)
    end = content.find("</script>", sig_idx)
    if end == -1:
        raise SystemExit("No se encontró '</script>' después de la firma: " + signature)
    end += len("</script>")
    return content[:start] + "<script>\n" + new_body + "\n</script>" + content[end:]


def strip_injected_questions(content):
    content = re.sub(r"<!-- PREGUNTAS-LECCION:BEGIN -->.*?<!-- PREGUNTAS-LECCION:END -->\n?", "", content, flags=re.S)
    content = re.sub(r"<script>\s*/\* Widgets de evaluacion -- preguntas de la leccion.*?</script>\s*", "", content, flags=re.S)
    content = re.sub(r"  /\* PREGUNTAS-LECCION:INVOCATIONS:BEGIN \*/.*?/\* PREGUNTAS-LECCION:INVOCATIONS:END \*/\n?", "", content, flags=re.S)
    # Compatibilidad con archivos generados ANTES del fix de --force (2026-09-03):
    # sus invocaciones Quiz*("#pregN", ...) no quedaron delimitadas por marcadores.
    content = re.sub(r'^[ \t]*Quiz(?:Choice|Multi|Sort|Cloze|Match)\("#preg\d+".*?\);\n', "", content, flags=re.M)
    return content


def main():
    if len(sys.argv) != 3:
        print("Uso: python3 refresh_shared_blocks.py entrada.html salida.html", file=sys.stderr)
        sys.exit(1)
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        content = f.read()
    content = strip_injected_questions(content)
    for signature, filename in SIGNATURES:
        content = replace_script_block(content, signature, read_asset(filename))
    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)
    print("OK", dst)


if __name__ == "__main__":
    main()
