#!/usr/bin/env python3
"""Agrega una sección de flashcards de repaso interactivo justo después de una
tabla existente en un fragmento de Contenido HTML, reusando el patrón aprobado
en 1.6.1 (CLAUDE.md, 2026-09-18): <style>/<script> reales, SIN íconos, SIN
nada evaluativo. No modifica la tabla original ni ningún otro contenido.

Uso:
    python3 add_flashcards.py "archivo.html" [--table-index N] [--dry-run]

--table-index: si el archivo tiene más de una <table>, cuál usar (0-based,
               por defecto 0 = la primera).
--dry-run: imprime el HTML generado sin escribir el archivo.
"""
import sys
import re
import os
from html.parser import HTMLParser


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []  # list of (start_offset, end_offset)
        self._depth = 0
        self._start = None

    def handle_starttag(self, tag, attrs):
        if tag == "table" and self._depth == 0:
            self._start = self.getpos()
        if tag == "table":
            self._depth += 1

    def handle_endtag(self, tag):
        if tag == "table":
            self._depth -= 1
            if self._depth == 0 and self._start is not None:
                self.tables.append((self._start, self.getpos()))
                self._start = None


def pos_to_offset(text, line, col):
    lines = text.split("\n")
    offset = sum(len(l) + 1 for l in lines[: line - 1]) + col
    return offset


def extract_table_span(text, table_index):
    p = TableParser()
    p.feed(text)
    if table_index >= len(p.tables):
        raise SystemExit(f"El archivo solo tiene {len(p.tables)} tabla(s); pediste índice {table_index}")
    (sl, sc), (el, ec) = p.tables[table_index]
    start = pos_to_offset(text, sl, sc)
    end_tag_start = pos_to_offset(text, el, ec)
    end = text.index(">", end_tag_start) + 1
    return start, end


def normalize_ws(text):
    # colapsa saltos de línea / indentación del HTML pretty-printed en un solo espacio,
    # pero preserva las etiquetas (no toca el contenido dentro de <pre>/<code>, que no
    # aparece en celdas de estas tablas de curso).
    return re.sub(r'\s+', ' ', text).strip()


def render_inline_code(text):
    # algunas tablas del curso escriben código con comillas invertidas Markdown
    # (`SELECT ...`) en vez de <code>, porque docx2html.py no convierte ese
    # formato dentro de celdas de tabla (sí lo hace en párrafos normales). Como
    # las flashcards muestran ese texto suelto (sin la celda de tabla alrededor),
    # las comillas invertidas quedan visibles y feas si no se convierten aquí.
    code_style = (
        "font-family:Consolas,'Courier New',monospace;"
        "background:#dcecf6;border:1px solid #bfe0f0;border-radius:4px;"
        "padding:1px 4px;color:#123a5c;font-size:0.92em;"
    )
    return re.sub(
        r'`([^`]+)`',
        lambda m: f'<code style="{code_style}">{m.group(1)}</code>',
        text,
    )


def strip_outer_strong(cell_html):
    cell_html = normalize_ws(cell_html)
    m = re.match(r'^<strong[^>]*>(.*)</strong>$', cell_html, re.S)
    if m:
        cell_html = normalize_ws(m.group(1))
    return render_inline_code(cell_html)


def parse_table_rows(table_html):
    rows = re.findall(r'<tr>(.*?)</tr>', table_html, re.S)
    parsed = []
    for row in rows:
        is_header = "<th" in row
        cell_tag = "th" if is_header else "td"
        cells = re.findall(rf'<{cell_tag}[^>]*>(.*?)</{cell_tag}>', row, re.S)
        cells = [strip_outer_strong(c) for c in cells]
        parsed.append((is_header, cells))
    return parsed


def topic_prefix(filename):
    base = os.path.basename(filename)
    m = re.match(r'^(\d+)\.(\d+)\.(\d+)', base)
    if m:
        return "p" + "".join(m.groups())
    m = re.match(r'^Lecci[oó]n (\d+)\.(\d+)', base)
    if m:
        return "pk" + "".join(m.groups())
    raise SystemExit(f"No pude extraer un prefijo único de: {base}")


def build_style(prefix):
    return f"""<style>
#{prefix} .{prefix}-cards{{display:flex;gap:16px;margin:18px 0;flex-wrap:wrap;}}
#{prefix} .{prefix}-card{{flex:1 1 220px;min-width:200px;height:190px;perspective:1200px;cursor:pointer;}}
#{prefix} .{prefix}-card-inner{{position:relative;width:100%;height:100%;transition:transform 0.6s cubic-bezier(.4,.2,.2,1);transform-style:preserve-3d;box-shadow:0 2px 8px rgba(18,58,92,0.15);border-radius:12px;}}
#{prefix} .{prefix}-card.is-flipped .{prefix}-card-inner{{transform:rotateY(180deg);}}
#{prefix} .{prefix}-card-front,#{prefix} .{prefix}-card-back{{position:absolute;inset:0;backface-visibility:hidden;border-radius:12px;padding:16px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;}}
#{prefix} .{prefix}-card-front{{background:linear-gradient(160deg,#123a5c,#1a6fa3);color:#ffffff;}}
#{prefix} .{prefix}-card-back{{background:#eaf4fb;color:#1e2f3f;transform:rotateY(180deg);text-align:left;justify-content:flex-start;overflow:auto;}}
#{prefix} .{prefix}-card:hover .{prefix}-card-inner{{box-shadow:0 6px 16px rgba(18,58,92,0.28);transform:translateY(-2px);}}
#{prefix} .{prefix}-card.is-flipped:hover .{prefix}-card-inner{{transform:rotateY(180deg) translateY(-2px);}}
#{prefix} .{prefix}-card-title{{font-weight:700;font-size:16.5px;line-height:1.3;}}
#{prefix} .{prefix}-card-hint{{font-size:12px;margin-top:10px;opacity:0.85;}}
#{prefix} .{prefix}-card-back p{{margin:0 0 6px;font-size:13.5px;line-height:1.5;}}
#{prefix} .{prefix}-card-back p:last-child{{margin-bottom:0;}}
#{prefix} .{prefix}-card-back strong{{color:#123a5c;}}
</style>
"""


def build_script(prefix):
    return f"""<script>
(function(){{
  var root = document.getElementById('{prefix}');
  if(!root) return;
  var cards = root.querySelectorAll('.{prefix}-card');
  for (var i=0;i<cards.length;i++){{
    (function(card){{
      function toggle(){{
        var flipped = card.classList.toggle('is-flipped');
        card.setAttribute('aria-pressed', flipped ? 'true' : 'false');
      }}
      card.addEventListener('click', toggle);
      card.addEventListener('keydown', function(e){{
        if(e.key==='Enter'||e.key===' '){{ e.preventDefault(); toggle(); }}
      }});
    }})(cards[i]);
  }}
}})();
</script>
"""


def build_cards_html(prefix, header, rows, skip_cols=None, intro_text=None, heading=None, plain=False):
    skip_cols = skip_cols or []
    html = []
    html.append(f'<h3 style="margin:22px 0 8px;color:#1a6fa3;font-size:18px;font-weight:700;">{heading or "Repaso interactivo: toca cada tarjeta"}</h3>\n')
    html.append(f'<p style="margin:0 0 10px;color:#1e2f3f;font-size:14.5px;line-height:1.6;">{intro_text or "Toca (o pulsa Enter) sobre cada tarjeta para voltearla y comprobar si recuerdas cada concepto."}</p>\n')
    html.append(f'<div class="{prefix}-cards">\n')
    for cells in rows:
        front = cells[0]
        back_lines = []
        for i in range(1, len(cells)):
            if i in skip_cols:
                continue
            if plain:
                back_lines.append(f'<p>{cells[i]}</p>')
            else:
                label = header[i] if i < len(header) else ""
                back_lines.append(f'<p><strong>{label}:</strong> {cells[i]}</p>')
        html.append(f'<div class="{prefix}-card" tabindex="0" role="button" aria-pressed="false">\n')
        html.append(f'<div class="{prefix}-card-inner">\n')
        html.append(f'<div class="{prefix}-card-front">\n<div class="{prefix}-card-title">{front}</div>\n<div class="{prefix}-card-hint">Toca para ver el detalle</div>\n</div>\n')
        html.append(f'<div class="{prefix}-card-back">\n{"".join(back_lines)}\n</div>\n')
        html.append('</div>\n</div>\n')
    html.append('</div>\n')
    return "".join(html)


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit(__doc__)
    dry_run = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]
    plain = "--plain" in args
    args = [a for a in args if a != "--plain"]
    table_index = 0
    if "--table-index" in args:
        idx = args.index("--table-index")
        table_index = int(args[idx + 1])
        args = args[:idx] + args[idx + 2:]
    heading = None
    if "--heading" in args:
        idx = args.index("--heading")
        heading = args[idx + 1]
        args = args[:idx] + args[idx + 2:]
    intro_text = None
    if "--intro-text" in args:
        idx = args.index("--intro-text")
        intro_text = args[idx + 1]
        args = args[:idx] + args[idx + 2:]
    filename = args[0]

    text = open(filename, encoding="utf-8").read()
    if "<style>" in text or re.search(r'class="p\w+-card"', text):
        raise SystemExit("El archivo ya parece tener un bloque <style>/flashcards. Revisa a mano.")

    start, end = extract_table_span(text, table_index)
    table_html = text[start:end]
    rows = parse_table_rows(table_html)
    if not rows or not rows[0][0]:
        raise SystemExit("No encontré fila de encabezado (<th>) en la tabla.")
    header = rows[0][1]
    data_rows = [cells for is_header, cells in rows[1:] if not is_header]

    prefix = topic_prefix(filename)
    cards_html = build_cards_html(prefix, header, data_rows, heading=heading, intro_text=intro_text, plain=plain)
    style = build_style(prefix)
    script = build_script(prefix)

    # id="p..." en el div contenedor externo (primer <div ... style="width:100%;...">)
    new_text = text
    open_re = re.compile(r'<div\s+style="width:100%;box-sizing:border-box;background-color:#fbfdff[^>]*>')
    m = open_re.search(new_text)
    if not m:
        raise SystemExit("No encontré el div contenedor externo esperado.")
    old_open = m.group(0)
    new_open = re.sub(r'^<div\s+', f'<div id="{prefix}" ', old_open, count=1)
    new_text = new_text.replace(old_open, new_open, 1)

    # insertar cards justo después de la tabla (recalcular offset porque el texto cambió por el id insertado antes de la tabla)
    shift = len(new_open) - len(old_open)
    end_shifted = end + shift
    new_text = new_text[:end_shifted] + "\n" + cards_html + new_text[end_shifted:]

    # style al inicio, script al final
    new_text = style + new_text + script

    if dry_run:
        print(cards_html)
        print("---STYLE---")
        print(style)
        print("---SCRIPT---")
        print(script)
    else:
        open(filename, "w", encoding="utf-8").write(new_text)
        print(f"OK: {filename} ({len(data_rows)} tarjetas, prefijo {prefix})")


if __name__ == "__main__":
    main()
