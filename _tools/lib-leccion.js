/* Librería reutilizable para generar los Word del curso (teoría y preguntas).
   Requiere el paquete npm 'docx' (npm install docx en esta carpeta).
   Uso: require('./lib-leccion.js') -> { el, pack, head, build, C } */
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType, Header, Footer, PageNumber
} = require('docx');
const fs = require('fs');
const path = require('path');

let cfg = {};
try { cfg = require(path.join(__dirname, '..', 'course.config.js')); } catch {}
const pal = cfg.palette || {};

const C = {
  NAVY:    pal.navy   || "1F3864",
  STEEL:   pal.steel  || "2E5496",
  GREY:    pal.grey   || "595959",
  LIGHT:   pal.light  || "EAF0F8",
  CODEBG:  "0F172A", CODECHIP: "F1F5F9", OK: "1F7A3D", OKBG: "E6F4EA",
};
const { NAVY, STEEL, GREY, LIGHT, CODEBG, CODECHIP, OK, OKBG } = C;

function text(t) {
  const runs = []; const re = /(\*\*[^*]+\*\*|`[^`]+`)/g; let last = 0, m;
  while ((m = re.exec(t))) {
    if (m.index > last) runs.push(new TextRun({ text: t.slice(last, m.index), size: 22 }));
    const tok = m[0];
    if (tok.startsWith("**")) runs.push(new TextRun({ text: tok.slice(2, -2), bold: true, size: 22, color: NAVY }));
    else runs.push(new TextRun({ text: tok.slice(1, -1), font: "Consolas", size: 21, color: STEEL, shading: { type: ShadingType.CLEAR, fill: CODECHIP } }));
    last = re.lastIndex;
  }
  if (last < t.length) runs.push(new TextRun({ text: t.slice(last), size: 22 }));
  return runs;
}

const el = {
  p: (t, o = {}) => new Paragraph({ spacing: { after: 120, line: 288 }, alignment: o.align || AlignmentType.JUSTIFIED, children: text(t) }),
  h1: t => new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 130 }, children: [new TextRun({ text: t, bold: true, color: NAVY, size: 30 })] }),
  h2: t => new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 90 }, children: [new TextRun({ text: t, bold: true, color: STEEL, size: 25 })] }),
  h3: t => new Paragraph({ spacing: { before: 160, after: 70 }, children: [new TextRun({ text: t, bold: true, color: NAVY, size: 22 })] }),
  li: t => new Paragraph({ bullet: { level: 0 }, spacing: { after: 70, line: 276 }, children: text(t) }),
  num: (t, n) => new Paragraph({ spacing: { after: 70, line: 276 }, indent: { left: 360, hanging: 260 }, children: [new TextRun({ text: (n) + ".  ", bold: true, color: STEEL, size: 22 })].concat(text(t)) }),
  q: t => new Paragraph({ spacing: { after: 90, line: 276 }, indent: { left: 360, hanging: 260 }, children: [new TextRun({ text: "?  ", bold: true, color: STEEL, size: 22 })].concat(text(t)) }),
  sp: (h) => new Paragraph({ spacing: { after: h || 120 } }),
  code: lines => new Paragraph({
    spacing: { before: 80, after: 120 }, shading: { type: ShadingType.CLEAR, fill: CODEBG },
    border: { top: { style: BorderStyle.SINGLE, size: 2, color: CODEBG, space: 6 }, bottom: { style: BorderStyle.SINGLE, size: 2, color: CODEBG, space: 6 }, left: { style: BorderStyle.SINGLE, size: 2, color: CODEBG, space: 8 }, right: { style: BorderStyle.SINGLE, size: 2, color: CODEBG, space: 8 } },
    children: lines.flatMap((l, i) => (i ? [new TextRun({ break: 1, text: l, font: "Consolas", size: 20, color: "E2E8F0" })] : [new TextRun({ text: l, font: "Consolas", size: 20, color: "E2E8F0" })]))
  }),
  callout: (title, body) => new Table({
    width: { size: 9360, type: WidthType.DXA }, columnWidths: [9360],
    borders: { top: { style: BorderStyle.SINGLE, size: 2, color: STEEL }, bottom: { style: BorderStyle.SINGLE, size: 2, color: STEEL }, left: { style: BorderStyle.SINGLE, size: 18, color: STEEL }, right: { style: BorderStyle.SINGLE, size: 2, color: STEEL }, insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE } },
    rows: [new TableRow({ children: [new TableCell({ width: { size: 9360, type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill: LIGHT }, margins: { top: 100, bottom: 100, left: 160, right: 140 }, children: [
      new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: title, bold: true, color: STEEL, size: 20, allCaps: true })] }),
      new Paragraph({ children: text(body) })
    ] })] })]
  }),
  table: (headers, rows, opts = {}) => {
    const total = 9360; const widths = opts.widths || headers.map(() => Math.floor(total / headers.length));
    const mk = (cells, head) => new TableRow({ tableHeader: !!head, children: cells.map((c, j) => new TableCell({ width: { size: widths[j], type: WidthType.DXA }, shading: { type: ShadingType.CLEAR, fill: head ? NAVY : "FFFFFF" }, margins: { top: 50, bottom: 50, left: 90, right: 90 }, children: [new Paragraph({ children: [new TextRun({ text: c, bold: !!head, color: head ? "FFFFFF" : "000000", size: 19 })] })] })) });
    return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths, rows: [mk(headers, true), ...rows.map(r => mk(r, false))] });
  },
  // Opción de pregunta (para lib-preguntas). correct=true la marca como correcta.
  opt: (letter, t, correct) => new Paragraph({
    spacing: { after: 50, line: 264 }, indent: { left: 360, hanging: 260 },
    children: [
      new TextRun({ text: letter + ")  ", bold: true, color: correct ? OK : GREY, size: 22 }),
      ...text(t),
      ...(correct ? [new TextRun({ text: "   (respuesta correcta)", bold: true, color: OK, size: 19 })] : []),
    ],
    shading: correct ? { type: ShadingType.CLEAR, fill: OKBG } : undefined,
  }),
  label: t => new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: t, bold: true, italics: true, color: STEEL, size: 18, allCaps: true })] }),
};

function pack(meta, children, outPath) {
  const courseName = (cfg.courseName || cfg.name || "Curso") + "    ·    Página ";
  const doc = new Document({
    creator: cfg.name || "Curso", title: meta.title,
    styles: { default: { document: { run: { font: "Calibri", size: 22, color: "000000" } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: "Calibri", bold: true, size: 30, color: NAVY }, paragraph: { spacing: { before: 300, after: 130 }, outlineLevel: 0 } },
        { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: "Calibri", bold: true, size: 25, color: STEEL }, paragraph: { spacing: { before: 240, after: 90 }, outlineLevel: 1 } },
      ] },
    sections: [{
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF", space: 4 } }, children: [new TextRun({ text: meta.runningHead, size: 16, color: GREY })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: courseName, size: 16, color: GREY }), new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GREY })] })] }) },
      children,
    }],
  });
  return Packer.toBuffer(doc).then(b => { fs.writeFileSync(outPath, b); console.log("OK", outPath.split("/").pop(), b.length); });
}

// Cabecera de lección: título + Descripción + Objetivos generales + Palabras clave.
function head(meta) {
  const h = [];
  h.push(new Paragraph({ spacing: { before: 120, after: 0 }, children: [new TextRun({ text: meta.unit.toUpperCase(), bold: true, size: 18, color: STEEL, characterSpacing: 30 })] }));
  h.push(new Paragraph({ spacing: { after: 20 }, children: [new TextRun({ text: meta.title, bold: true, size: 40, color: NAVY })] }));
  h.push(new Paragraph({ spacing: { after: 60 }, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: STEEL, space: 6 } }, children: [new TextRun({ text: meta.objective, italics: true, size: 21, color: GREY })] }));
  h.push(el.sp(160));
  if (meta.intro) { h.push(el.h2("Descripción de la lección")); h.push(el.p(meta.intro)); }
  if (meta.objectives && meta.objectives.length) {
    h.push(el.h2("Objetivos generales"));
    h.push(el.p("Al finalizar esta lección, el participante será capaz de:"));
    meta.objectives.forEach(o => h.push(el.li(o)));
  }
  if (meta.keywords && meta.keywords.length) {
    h.push(el.h2("Palabras clave"));
    h.push(el.table(["Palabra clave", "Significado"], meta.keywords.map(k => [k.t, k.d]), { widths: [2900, 6460] }));
    h.push(el.sp(120));
  }
  return h;
}

function build(meta, body, outPath) { return pack(meta, head(meta).concat(body), outPath); }

module.exports = { el, pack, head, build, C };
