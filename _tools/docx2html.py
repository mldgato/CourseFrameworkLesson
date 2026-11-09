# -*- coding: utf-8 -*-
# Convierte un .docx de TEORÍA (generado con lib-leccion.js) en un FRAGMENTO HTML
# con estilos EN LÍNEA en cada etiqueta, listo para pegar en el editor de la plataforma.
# No emite <html>/<head>/<body>: solo el contenido.
#   Uso:  python3 docx2html.py "entrada.docx" "salida.html"
import sys, re, html, zipfile

NAVY="#123a5c"; STEEL="#1a6fa3"; INK="#1e2f3f"; LINE="#e2e8f0"; LIGHT="#eaf4fb"; CHIP="#f1f5f9"; CODEBG="#0f172a"; CODEINK="#e2e8f0"; OK="#1f7a3d"

def wrap_container(frag):
    """Envuelve un fragmento en un contenedor de ancho legible y márgenes, con
    fondo de cuadrícula sutil de borde a borde (el div externo no lleva
    max-width, así la cuadrícula llena el ancho real del contenedor de la
    plataforma) y tipografía Helvetica/Arial aplicada por herencia desde el
    div interno (decisión del usuario, 2026-09-05; paleta azul del logo IT
    Specialist, tipografía y fondo de cuadrícula, decisión del usuario, 2026-09-10)."""
    return ('<div style="width:100%;box-sizing:border-box;background-color:#fbfdff;'
            'background-image:linear-gradient(#e3edf5 1px, transparent 1px),'
            'linear-gradient(90deg, #e3edf5 1px, transparent 1px);background-size:26px 26px;'
            'padding:28px 0 32px;">\n'
            '<div style="max-width:900px;margin:0 auto;padding:0 24px;box-sizing:border-box;'
            'font-family:helvetica,arial,sans-serif;">\n'
            + frag.rstrip("\n") + '\n</div>\n</div>\n')

def esc(s): return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def unesc(s): return html.unescape(s)

def runs_of(p):
    return re.findall(r"<w:r\b[^>]*>(.*?)</w:r>", p, re.S)

def run_text(r):
    return "".join(unesc(m) for m in re.findall(r"<w:t[^>]*>(.*?)</w:t>", r, re.S))

def run_html(r):
    """Renderiza un run como HTML respetando negrita e inline-code."""
    t = run_text(r)
    if not t: return ""
    rpr = re.search(r"<w:rPr>(.*?)</w:rPr>", r, re.S)
    rpr = rpr.group(1) if rpr else ""
    is_code = 'w:ascii="Consolas"' in rpr
    is_bold = "<w:b/>" in rpr or "<w:b " in rpr
    color = re.search(r'<w:color w:val="([0-9A-Fa-f]{6})"', rpr)
    color = color.group(1).upper() if color else ""
    if is_code:
        return ('<code style="font-family:Consolas,\'Courier New\',monospace;background:%s;border:1px solid %s;'
                'border-radius:4px;padding:1px 5px;color:%s;font-size:0.92em;">%s</code>' % (CHIP, LINE, STEEL, esc(t)))
    if is_bold and color == "1F3864":
        return '<strong style="color:%s;font-weight:700;">%s</strong>' % (NAVY, esc(t))
    if is_bold:
        return "<strong>%s</strong>" % esc(t)
    return esc(t)

def inline(p):
    return "".join(run_html(r) for r in runs_of(p))

def para_props(p):
    ppr = re.search(r"<w:pPr>(.*?)</w:pPr>", p, re.S)
    ppr = ppr.group(1) if ppr else ""
    style = re.search(r'<w:pStyle w:val="([^"]+)"', ppr)
    fill = re.search(r'<w:shd[^>]*w:fill="([0-9A-Fa-f]{6})"', ppr)
    return (style.group(1) if style else None,
            "<w:numPr>" in ppr,
            fill.group(1).upper() if fill else None)

def is_all_bold_navy(p):
    rs = runs_of(p)
    if not rs: return False
    any_text = False
    for r in rs:
        if not run_text(r).strip(): continue
        any_text = True
        rpr = re.search(r"<w:rPr>(.*?)</w:rPr>", r, re.S)
        rpr = rpr.group(1) if rpr else ""
        if not ("<w:b/>" in rpr or "<w:b " in rpr): return False
        c = re.search(r'<w:color w:val="([0-9A-Fa-f]{6})"', rpr)
        if not c or c.group(1).upper() != "1F3864": return False
    return any_text

def code_lines(p):
    parts = re.findall(r"(<w:br/>|<w:t[^>]*>.*?</w:t>)", p, re.S)
    out = ""
    for pt in parts:
        if pt == "<w:br/>": out += "\n"
        else: out += unesc(re.sub(r"<[^>]+>", "", pt))
    return out

def h(tag, style, txt): return '<%s style="%s">%s</%s>' % (tag, style, txt, tag)

def render_para(p):
    style, is_bullet, fill = para_props(p)
    if style == "Heading1":
        return ("blk", None, h("h2", "margin:26px 0 10px;color:%s;font-size:22px;font-weight:700;line-height:1.25;" % NAVY, esc(run_text(p).strip())))
    if style == "Heading2":
        return ("blk", None, h("h3", "margin:22px 0 8px;color:%s;font-size:18px;font-weight:700;" % STEEL, esc(run_text(p).strip())))
    if fill == "0F172A":  # bloque de código
        code = esc(code_lines(p))
        return ("blk", None, ('<pre style="margin:12px 0;background:%s;color:%s;padding:14px 16px;border-radius:10px;overflow:auto;'
                'font-family:Consolas,\'Courier New\',monospace;font-size:13.5px;line-height:1.55;"><code style="font-family:inherit;background:none;border:none;padding:0;color:inherit;">%s</code></pre>' % (CODEBG, CODEINK, code)))
    if is_bullet:
        return ("li", None, '<li style="margin:5px 0;color:%s;font-size:15px;line-height:1.6;">%s</li>' % (INK, inline(p)))
    # el.h3 (subtítulo en negrita navy)
    if is_all_bold_navy(p):
        return ("blk", None, h("h4", "margin:18px 0 6px;color:%s;font-size:16px;font-weight:700;" % NAVY, esc(run_text(p).strip())))
    # el.num (empieza con "N.  " en negrita)
    rs = runs_of(p)
    if rs and re.match(r"^\s*\d+\.\s{2}$", run_text(rs[0])):
        n = run_text(rs[0]).strip()
        rest = "".join(run_html(r) for r in rs[1:])
        return ("blk", None, '<p style="margin:0 0 8px;padding-left:4px;color:%s;font-size:15px;line-height:1.6;"><strong style="color:%s;font-weight:700;">%s&nbsp;&nbsp;</strong>%s</p>' % (INK, STEEL, esc(n), rest))
    txt = inline(p)
    if not txt.strip(): return ("blk", None, "")
    return ("blk", None, '<p style="margin:0 0 12px;color:%s;font-size:15px;line-height:1.6;text-align:justify;">%s</p>' % (INK, txt))

def render_table(tbl):
    rows = re.findall(r"<w:tr\b[^>]*>(.*?)</w:tr>", tbl, re.S)
    # callout = 1 fila, 1 celda, con relleno EAF0F8
    if len(rows) == 1:
        cells = re.findall(r"<w:tc\b[^>]*>(.*?)</w:tc>", rows[0], re.S)
        if len(cells) == 1 and "EAF0F8" in cells[0]:
            ps = re.findall(r"<w:p\b[^>]*>.*?</w:p>", cells[0], re.S)
            title = esc(run_text(ps[0]).strip()) if ps else ""
            body = "".join(inline(x) for x in ps[1:])
            return ('<div style="margin:14px 0;border-left:4px solid %s;background:%s;border-radius:8px;padding:12px 16px;">'
                    '<p style="margin:0 0 4px;color:%s;font-weight:700;text-transform:uppercase;font-size:12.5px;letter-spacing:0.4px;">%s</p>'
                    '<p style="margin:0;color:%s;font-size:14.5px;line-height:1.6;">%s</p></div>' % (STEEL, LIGHT, STEEL, title, INK, body))
    # tabla de datos: primera fila con relleno 1F3864 = cabecera
    out = '<table style="border-collapse:collapse;width:100%;margin:14px 0;font-size:14px;">'
    for i, r in enumerate(rows):
        cells = re.findall(r"<w:tc\b[^>]*>(.*?)</w:tc>", r, re.S)
        header = ("1F3864" in cells[0]) if cells else False
        out += "<tr>"
        for c in cells:
            txt = inline(c) or "&nbsp;"
            if header:
                out += '<th style="background:%s;color:#ffffff;text-align:left;padding:8px 12px;border:1px solid %s;font-weight:700;">%s</th>' % (NAVY, NAVY, txt)
            else:
                out += '<td style="padding:7px 12px;border:1px solid %s;background:#ffffff;color:%s;vertical-align:top;">%s</td>' % (LINE, INK, txt)
        out += "</tr>"
    out += "</table>"
    return out

def blocks(body):
    """Recorre <w:p> y <w:tbl> de nivel superior, en orden."""
    i = 0; res = []
    while i < len(body):
        t = body.find("<w:tbl>", i); pp = body.find("<w:p>", i)
        p2 = body.find("<w:p ", i)
        pstart = min([x for x in (pp, p2) if x >= 0], default=-1)
        if t < 0 and pstart < 0: break
        if t >= 0 and (pstart < 0 or t < pstart):
            end = body.find("</w:tbl>", t) + len("</w:tbl>")
            res.append(("tbl", body[t:end])); i = end
        else:
            end = body.find("</w:p>", pstart) + len("</w:p>")
            res.append(("p", body[pstart:end])); i = end
    return res

def convert(docx_path, out_path):
    x = zipfile.ZipFile(docx_path).read("word/document.xml").decode("utf-8")
    body = re.search(r"<w:body>(.*)</w:body>", x, re.S).group(1)
    bl = blocks(body)
    # Omitir la portada del Word (rótulo de unidad, título y línea de objetivo):
    # empezar en el primer bloque con estilo de encabezado (Descripción de la lección).
    start = 0
    for idx, (kind, xml) in enumerate(bl):
        if kind == "p" and para_props(xml)[0] in ("Heading1", "Heading2"):
            start = idx; break
    bl = bl[start:]
    items = []
    for kind, xml in bl:
        if kind == "tbl":
            items.append(("blk", render_table(xml)))
        else:
            role, _, out = render_para(xml)
            items.append((role, out))
    # agrupar <li> consecutivos en <ul>
    html_parts = []; run = []
    def flush():
        if run: html_parts.append('<ul style="margin:0 0 12px;padding-left:22px;">' + "".join(run) + "</ul>"); run.clear()
    for role, out in items:
        if not out: continue
        if role == "li" and out.startswith("<li"):
            run.append(out)
        else:
            flush(); html_parts.append(out)
    flush()
    frag = "\n".join(html_parts) + "\n"
    frag = wrap_container(frag)
    open(out_path, "w", encoding="utf-8").write(frag)
    print("OK", out_path.split("/")[-1], len(frag), "bytes")

def render_group(bl_group):
    """Aplica a un sub-grupo de bloques el mismo render + agrupado de <li> que convert()."""
    items = []
    for kind, xml in bl_group:
        if kind == "tbl":
            items.append(("blk", render_table(xml)))
        else:
            role, _, out = render_para(xml)
            items.append((role, out))
    html_parts = []; run = []
    def flush():
        if run: html_parts.append('<ul style="margin:0 0 12px;padding-left:22px;">' + "".join(run) + "</ul>"); run.clear()
    for role, out in items:
        if not out: continue
        if role == "li" and out.startswith("<li"):
            run.append(out)
        else:
            flush(); html_parts.append(out)
    flush()
    return "\n".join(html_parts) + "\n"

def convert_split(docx_path, out_dir, lesson_label):
    """Genera el Contenido HTML DIVIDIDO POR TEMA (estándar del curso, ver CLAUDE.md §5b):
       - 'Lección <lesson_label> - Introducción.html'  -> Descripción/Objetivos/Palabras clave
       - '<nombre del archivo de la actividad>.html'   -> un archivo por cada tema (Heading1)
       - 'Lección <lesson_label> - Resumen.html'        -> el cierre "Resumen de la lección"
       Los nombres de los archivos por tema se toman de Actividades/ (carpeta hermana de
       Contenido HTML dentro de la misma Unidad), emparejando por orden, para que
       Contenido HTML y Actividades usen siempre el mismo nombre de archivo por tema."""
    import os, glob
    x = zipfile.ZipFile(docx_path).read("word/document.xml").decode("utf-8")
    body = re.search(r"<w:body>(.*)</w:body>", x, re.S).group(1)
    bl = blocks(body)
    start = 0
    for idx, (kind, xml) in enumerate(bl):
        if kind == "p" and para_props(xml)[0] in ("Heading1", "Heading2"):
            start = idx; break
    bl = bl[start:]

    # Partir en grupos: el primero (intro) termina en el primer Heading1;
    # cada Heading1 posterior abre un grupo nuevo e incluye su propio encabezado
    # como primer bloque del grupo (para que cada archivo lleve su <h2>).
    groups = []  # lista de (heading_text_or_None, [bloques])
    cur_heading = None
    cur = []
    for kind, xml in bl:
        if kind == "p" and para_props(xml)[0] == "Heading1":
            groups.append((cur_heading, cur))
            cur_heading = run_text(xml).strip()
            cur = [(kind, xml)]
        else:
            cur.append((kind, xml))
    groups.append((cur_heading, cur))
    # groups[0] es la intro (heading=None); groups[1:] son un heading1 por tema,
    # y el último de esos debe ser "Resumen de la lección".

    activities_dir = os.path.join(os.path.dirname(os.path.normpath(out_dir)), "Actividades")
    prefix = lesson_label + "."
    act_files = sorted(
        (f for f in glob.glob(os.path.join(activities_dir, prefix + "*.html"))),
        key=lambda f: [int(n) for n in re.match(r".*?(\d+)\.(\d+)\.(\d+)", os.path.basename(f)).groups()]
    )
    topic_groups = groups[1:-1]
    resumen_group = groups[-1]
    if len(act_files) != len(topic_groups):
        print("AVISO: %d temas en el .docx pero %d actividades en %s — revisa el emparejamiento." %
              (len(topic_groups), len(act_files), activities_dir))

    os.makedirs(out_dir, exist_ok=True)
    intro_path = os.path.join(out_dir, "Lección %s - Introducción.html" % lesson_label)
    open(intro_path, "w", encoding="utf-8").write(wrap_container(render_group(groups[0][1])))
    print("OK", os.path.basename(intro_path))

    for i, (heading, blks) in enumerate(topic_groups):
        name = os.path.splitext(os.path.basename(act_files[i]))[0] if i < len(act_files) else heading
        topic_path = os.path.join(out_dir, name + ".html")
        open(topic_path, "w", encoding="utf-8").write(wrap_container(render_group(blks)))
        print("OK", os.path.basename(topic_path))

    resumen_path = os.path.join(out_dir, "Lección %s - Resumen.html" % lesson_label)
    open(resumen_path, "w", encoding="utf-8").write(wrap_container(render_group(resumen_group[1])))
    print("OK", os.path.basename(resumen_path))
    if resumen_group[0] and "resumen" not in resumen_group[0].lower():
        print("AVISO: el último bloque Heading1 se llama '%s', no 'Resumen de la lección'. Revisa el .docx." % resumen_group[0])

if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--split":
        # python3 docx2html.py --split "entrada.docx" "carpeta Contenido HTML" "X.Y"
        convert_split(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        convert(sys.argv[1], sys.argv[2])
