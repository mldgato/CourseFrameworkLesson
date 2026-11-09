/* Generador del documento de PREGUNTAS DE EVALUACIÓN por lección.
   Requiere ./lib-leccion.js y el paquete npm 'docx'.
   Tipos de pregunta:
     'mc'    -> opción múltiple (una correcta)
     'ms'    -> selección múltiple (varias correctas)
     'cloze' -> arrastrar y soltar palabras en un párrafo (huecos {1},{2}... + banco + respuestas)
     'sort'      -> clasificación: agrupar elementos en categorías (agregado 2026-09-03, desde 2.3)
     'match'     -> emparejar elementos de dos columnas, con <select> (agregado 2026-09-03, desde 2.3)
     'order'     -> ordenar una secuencia arrastrando y soltando (agregado 2026-09-03, para lecciones futuras)
     'dragmatch' -> emparejar arrastrando palabras hacia sus definiciones (agregado 2026-09-03, para lecciones futuras)
   Uso: buildQuestions(meta, topics, outPath)
     meta   = {unit, title, objective, runningHead}
     topics = [{ code:"1.4.1", title:"...", questions:[ q, ... ] }]
     q (mc/ms)      = { type, stem, options:[{t, ok?}] }
     q (cloze)      = { type:'cloze', stem, paragraph:"...{1}...{2}...", bank:[...], answers:[...] }
     q (sort)       = { type:'sort', stem, cats:["Cat A","Cat B",...], items:[{t:"...", cat:"Cat A"}, ...] }
     q (match)      = { type:'match', stem, pairs:[{l:"Izquierda 1", r:"Derecha 1"}, ...] }
     q (order)      = { type:'order', stem, items:["Paso 1...", "Paso 2...", ...] }  (en el ORDEN correcto)
     q (dragmatch)  = { type:'dragmatch', stem, pairs:[{l:"Palabra", r:"Definición"}, ...] }
*/
const { el, pack, C } = require("./lib-leccion.js");
const { Paragraph, TextRun, ShadingType, BorderStyle } = require("docx");
const { NAVY, STEEL, GREY, OK, OKBG, CODECHIP } = C;

const LETTERS = ["a", "b", "c", "d", "e", "f"];
const TYPE_LABEL = {
  mc: "Opción múltiple · una respuesta",
  ms: "Selección múltiple · varias respuestas",
  cloze: "Arrastrar y soltar · completar el párrafo",
  sort: "Clasificación · agrupar en categorías",
  match: "Emparejar · relaciona los elementos",
  order: "Ordenar secuencia · arrastra en el orden correcto",
  dragmatch: "Arrastrar y emparejar · une cada palabra con su definición",
};

function inline(t) {
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

function renderQuestion(q, n) {
  const out = [];
  out.push(new Paragraph({ spacing: { before: 160, after: 40 }, children: [
    new TextRun({ text: "Pregunta " + n + ".  ", bold: true, color: NAVY, size: 22 }),
    ...inline(q.stem),
  ] }));
  out.push(new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: TYPE_LABEL[q.type], italics: true, size: 17, color: STEEL })] }));

  if (q.type === "mc" || q.type === "ms") {
    q.options.forEach((o, i) => out.push(el.opt(LETTERS[i], o.t, !!o.ok)));
  } else if (q.type === "cloze") {
    const parts = q.paragraph.split(/\{(\d+)\}/);
    const runs = [];
    for (let i = 0; i < parts.length; i++) {
      if (i % 2 === 0) { if (parts[i]) runs.push(new TextRun({ text: parts[i], size: 22 })); }
      else runs.push(new TextRun({ text: " ______(" + parts[i] + ") ", bold: true, color: STEEL, size: 22 }));
    }
    out.push(new Paragraph({ spacing: { after: 70, line: 300 }, indent: { left: 260 }, children: runs }));
    out.push(new Paragraph({ spacing: { after: 40 }, indent: { left: 260 }, children: [
      new TextRun({ text: "Banco de palabras:  ", bold: true, size: 20, color: NAVY }),
      new TextRun({ text: q.bank.join("   ·   "), size: 20 }),
    ] }));
    out.push(new Paragraph({ spacing: { after: 40 }, indent: { left: 260 }, shading: { type: ShadingType.CLEAR, fill: OKBG }, children: [
      new TextRun({ text: "Respuestas:  ", bold: true, size: 19, color: OK }),
      new TextRun({ text: q.answers.map((a, i) => "(" + (i + 1) + ") " + a).join("    "), size: 19, color: OK }),
    ] }));
  } else if (q.type === "sort") {
    out.push(new Paragraph({ spacing: { after: 60 }, indent: { left: 260 }, children: [
      new TextRun({ text: "Categorías:  ", bold: true, size: 20, color: NAVY }),
      new TextRun({ text: q.cats.join("   ·   "), size: 20 }),
    ] }));
    q.items.forEach(it => out.push(new Paragraph({ spacing: { after: 30 }, indent: { left: 260 }, children: [
      new TextRun({ text: "-  ", size: 21 }),
      new TextRun({ text: it.t, size: 21 }),
      new TextRun({ text: "  →  ", size: 21 }),
      new TextRun({ text: it.cat, bold: true, size: 21, color: OK, shading: { type: ShadingType.CLEAR, fill: OKBG } }),
    ] })));
  } else if (q.type === "match") {
    q.pairs.forEach((p, i) => out.push(new Paragraph({ spacing: { after: 30 }, indent: { left: 260 }, children: [
      new TextRun({ text: (i + 1) + ")  ", size: 21 }),
      new TextRun({ text: p.l, size: 21 }),
      new TextRun({ text: "  →  ", size: 21 }),
      new TextRun({ text: p.r, bold: true, size: 21, color: OK, shading: { type: ShadingType.CLEAR, fill: OKBG } }),
    ] })));
  } else if (q.type === "order") {
    q.items.forEach((it, i) => out.push(new Paragraph({ spacing: { after: 30 }, indent: { left: 260 }, children: [
      new TextRun({ text: (i + 1) + ")  ", bold: true, size: 21, color: OK, shading: { type: ShadingType.CLEAR, fill: OKBG } }),
      new TextRun({ text: it, size: 21 }),
    ] })));
  } else if (q.type === "dragmatch") {
    q.pairs.forEach((p, i) => out.push(new Paragraph({ spacing: { after: 30 }, indent: { left: 260 }, children: [
      new TextRun({ text: (i + 1) + ")  ", size: 21 }),
      new TextRun({ text: p.l, size: 21 }),
      new TextRun({ text: "  →  ", size: 21 }),
      new TextRun({ text: p.r, bold: true, size: 21, color: OK, shading: { type: ShadingType.CLEAR, fill: OKBG } }),
    ] })));
  }
  return out;
}

function buildQuestions(meta, topics, outPath) {
  const body = [];
  body.push(new Paragraph({ spacing: { before: 120, after: 0 }, children: [new TextRun({ text: meta.unit.toUpperCase(), bold: true, size: 18, color: STEEL, characterSpacing: 30 })] }));
  body.push(new Paragraph({ spacing: { after: 20 }, children: [new TextRun({ text: meta.title, bold: true, size: 38, color: NAVY })] }));
  body.push(new Paragraph({ spacing: { after: 100 }, border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: STEEL, space: 6 } }, children: [new TextRun({ text: meta.objective, italics: true, size: 21, color: GREY })] }));
  body.push(el.p("Estas preguntas evalúan cada tema de la lección y se responden después de estudiar la teoría y realizar la actividad interactiva. Las respuestas correctas aparecen resaltadas para uso del docente."));

  let count = 0;
  topics.forEach(tp => {
    body.push(el.h1("Tema " + tp.code + " — " + tp.title));
    tp.questions.forEach(q => { count++; renderQuestion(q, count).forEach(x => body.push(x)); });
  });

  return pack(meta, body, outPath);
}

module.exports = { buildQuestions };
