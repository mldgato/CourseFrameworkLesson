#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inyecta, en cada actividad interactiva (.html) de una unidad, un paso final
"Evaluación" con las preguntas de su tema, tomadas del Word de Preguntas de la
lección (vía extract_preguntas_docx.py). Ver CLAUDE.md §7.8.

Uso:
  python3 inject_preguntas.py "Unidad 1 - Diseño de Bases de Datos" [--force]
  python3 inject_preguntas.py "Unidad 2 - Gestión de Objetos con DDL" [--force]

Es idempotente: si una actividad ya tiene el marcador de preguntas inyectadas,
se salta (a menos que se pase --force, que la reemplaza por completo).
"""
import glob
import html
import json
import os
import re
import sys

from extract_preguntas_docx import get_paragraphs, parse_topics

MARK_BEGIN = "<!-- PREGUNTAS-LECCION:BEGIN -->"
MARK_END = "<!-- PREGUNTAS-LECCION:END -->"
WIDGETS_MARK = "/* Widgets de evaluacion -- preguntas de la leccion"
INV_BEGIN = "  /* PREGUNTAS-LECCION:INVOCATIONS:BEGIN */"
INV_END = "  /* PREGUNTAS-LECCION:INVOCATIONS:END */"

TYPE_LABEL_DISPLAY = {
    "mc": "Opción múltiple",
    "ms": "Selección múltiple",
    "cloze": "Completa el párrafo",
    "sort": "Clasificación",
    "match": "Emparejar elementos",
    "order": "Ordenar secuencia",
    "dragmatch": "Arrastrar y emparejar",
}

WIDGETS_BLOCK = '''<script>
/* Widgets de evaluacion -- preguntas de la leccion (inyectadas automaticamente
   desde el Word de Preguntas de esta leccion; ver CLAUDE.md §7.8).
   Redefine QuizChoice (con retroalimentacion por defecto) y agrega QuizMulti
   (varias correctas) y QuizCloze (completar huecos con banco de palabras). */
(function () {
  "use strict";
  const $ = (s, r) => (r || document).querySelector(s);
  const declare = id => { if (window.Xp) window.Xp.declare(id); };
  const record = (id, ok) => { if (window.Xp) window.Xp.record(id, ok); };

  window.QuizChoice = function (sel, opts) {
    const el = $(sel); if (!el) return;
    declare(sel);
    const box = document.createElement("div"); box.className = "row";
    const out = document.createElement("div"); out.className = "out"; out.style.marginTop = "10px";
    opts.options.forEach(o => {
      const b = document.createElement("button"); b.type = "button"; b.className = "chip"; b.innerHTML = o.label;
      b.addEventListener("click", () => {
        Array.from(box.children).forEach(x => x.classList.remove("sel")); b.classList.add("sel");
        const fb = o.fb || (o.ok ? "¡Correcto! Es la respuesta correcta." : "No es correcto. Revisa el tema e inténtalo de nuevo.");
        out.innerHTML = '<div class="msg ' + (o.ok ? "ok" : "bad") + '"><span class="ic">' + (o.ok ? "✓" : "✗") + "</span>" + fb + "</div>";
        record(sel, o.ok);
      });
      box.appendChild(b);
    });
    el.appendChild(box); el.appendChild(out);
  };

  window.QuizMulti = function (sel, opts) {
    const el = $(sel); if (!el) return;
    declare(sel);
    const state = {};
    const wrap = document.createElement("div"); wrap.style.cssText = "display:flex;flex-direction:column;gap:8px;align-items:flex-start";
    opts.options.forEach((o, i) => {
      const b = document.createElement("button"); b.type = "button"; b.className = "chip"; b.innerHTML = o.label;
      b.style.textAlign = "left";
      b.addEventListener("click", () => { state[i] = !state[i]; b.classList.toggle("sel", state[i]); });
      wrap.appendChild(b);
    });
    const bar = document.createElement("div"); bar.className = "row"; bar.style.marginTop = "6px";
    const check = document.createElement("button"); check.type = "button"; check.className = "btn"; check.textContent = "Comprobar";
    bar.appendChild(check);
    const out = document.createElement("div"); out.className = "out"; out.style.marginTop = "10px";
    check.addEventListener("click", () => {
      let allOk = true;
      opts.options.forEach((o, i) => { if (!!state[i] !== !!o.ok) allOk = false; });
      out.innerHTML = allOk
        ? '<div class="msg ok"><span class="ic">✓</span>¡Correcto! Marcaste exactamente las opciones correctas.</div>'
        : '<div class="msg bad"><span class="ic">✗</span>No es correcto. ' + (opts.hint || "Revisa tu selección e inténtalo de nuevo.") + '</div>';
      record(sel, allOk);
    });
    el.appendChild(wrap); el.appendChild(bar); el.appendChild(out);
  };

  window.QuizCloze = function (sel, opts) {
    const el = $(sel); if (!el) return;
    declare(sel);
    const p = document.createElement("p");
    const parts = String(opts.paragraph).split(/\\{(\\d+)\\}/);
    const selects = [];
    for (let i = 0; i < parts.length; i++) {
      if (i % 2 === 0) { if (parts[i]) p.appendChild(document.createTextNode(parts[i])); }
      else {
        const idx = parseInt(parts[i], 10) - 1;
        const s = document.createElement("select");
        s.style.cssText = "font:inherit;font-weight:650;margin:0 3px;padding:4px 8px;border:1px solid var(--line-2);border-radius:8px;background:var(--surface-2);color:var(--ink)";
        const blank = document.createElement("option"); blank.value = ""; blank.textContent = "— elige —";
        s.appendChild(blank);
        opts.bank.forEach(w => { const o = document.createElement("option"); o.value = w; o.textContent = w; s.appendChild(o); });
        selects[idx] = s;
        p.appendChild(s);
      }
    }
    const bar = document.createElement("div"); bar.className = "row"; bar.style.marginTop = "10px";
    const check = document.createElement("button"); check.type = "button"; check.className = "btn"; check.textContent = "Comprobar";
    bar.appendChild(check);
    const out = document.createElement("div"); out.className = "out"; out.style.marginTop = "10px";
    check.addEventListener("click", () => {
      let ok = 0, done = 0;
      selects.forEach((s, i) => { if (s.value) done++; if (s.value === opts.answers[i]) ok++; });
      if (done < selects.length) { out.innerHTML = '<div class="msg bad"><span class="ic">!</span>Completa todos los huecos antes de comprobar.</div>'; return; }
      const allOk = ok === selects.length;
      out.innerHTML = allOk
        ? '<div class="msg ok"><span class="ic">✓</span>¡Perfecto! Completaste correctamente el párrafo.</div>'
        : '<div class="msg bad"><span class="ic">✗</span>Acertaste ' + ok + " de " + selects.length + ". " + (opts.hint || "Revisa e inténtalo de nuevo.") + '</div>';
      record(sel, allOk);
    });
    el.appendChild(p); el.appendChild(bar); el.appendChild(out);
  };

  /* Emparejar elementos de dos columnas (un <select> por elemento izquierdo). opts:{pairs:[{l,r}], hint}.
     No se redefine aqui QuizSort: ya viene embebido en la plantilla de la actividad (_fuente-assets/quiz.js)
     y su firma (items/cats/hint) ya es la que necesita el tipo 'sort'. */
  window.QuizMatch = function (sel, opts) {
    const el = $(sel); if (!el) return;
    declare(sel);
    const wrap = document.createElement("div");
    wrap.style.cssText = "display:flex;flex-direction:column;gap:10px";
    const selects = [];
    opts.pairs.forEach((p, i) => {
      const row = document.createElement("div");
      row.style.cssText = "display:flex;gap:10px;align-items:center;flex-wrap:wrap";
      const label = document.createElement("span");
      label.innerHTML = p.l; label.style.cssText = "flex:1;min-width:150px;font-weight:600";
      const s = document.createElement("select");
      s.style.cssText = "font:inherit;font-weight:650;padding:4px 8px;border:1px solid var(--line-2);border-radius:8px;background:var(--surface-2);color:var(--ink);min-width:160px";
      const blank = document.createElement("option"); blank.value = ""; blank.textContent = "— elige —";
      s.appendChild(blank);
      opts.pairs.forEach(pp => { const o = document.createElement("option"); o.value = pp.r; o.textContent = pp.r; s.appendChild(o); });
      selects.push(s);
      row.appendChild(label); row.appendChild(s);
      wrap.appendChild(row);
    });
    const bar = document.createElement("div"); bar.className = "row"; bar.style.marginTop = "6px";
    const check = document.createElement("button"); check.type = "button"; check.className = "btn"; check.textContent = "Comprobar";
    bar.appendChild(check);
    const out = document.createElement("div"); out.className = "out"; out.style.marginTop = "10px";
    check.addEventListener("click", () => {
      let ok = 0, done = 0;
      selects.forEach((s, i) => { if (s.value) done++; if (s.value === opts.pairs[i].r) ok++; });
      if (done < selects.length) { out.innerHTML = '<div class="msg bad"><span class="ic">!</span>Empareja todos los elementos antes de comprobar.</div>'; return; }
      const allOk = ok === selects.length;
      out.innerHTML = allOk
        ? '<div class="msg ok"><span class="ic">✓</span>¡Perfecto! Emparejaste correctamente los ' + ok + " elementos.</div>"
        : '<div class="msg bad"><span class="ic">✗</span>Acertaste ' + ok + " de " + selects.length + ". " + (opts.hint || "Revisa e inténtalo de nuevo.") + "</div>";
      record(sel, allOk);
    });
    el.appendChild(wrap); el.appendChild(bar); el.appendChild(out);
  };

  /* Ordenar secuencia arrastrando y soltando (Pointer Events). opts:{items:[...orden correcto...], hint}. */
  window.QuizOrder = function (sel, opts) {
    const el = $(sel); if (!el) return;
    declare(sel);
    const list = document.createElement("div");
    list.style.cssText = "display:flex;flex-direction:column;gap:8px";
    const shuffled = opts.items.map((label, idx) => ({ label, idx }));
    for (let i = shuffled.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); const t = shuffled[i]; shuffled[i] = shuffled[j]; shuffled[j] = t; }
    shuffled.forEach(it => {
      const row = document.createElement("div");
      row.className = "orditem";
      row.dataset.idx = it.idx;
      row.style.cssText = "display:flex;align-items:center;gap:10px;padding:9px 12px;border:1px solid var(--line-2);border-radius:10px;background:var(--surface);cursor:grab;touch-action:none;user-select:none";
      const grip = document.createElement("span"); grip.textContent = "⠿"; grip.style.cssText = "color:var(--muted);font-weight:700";
      const txt = document.createElement("span"); txt.style.flex = "1"; txt.textContent = it.label;
      row.appendChild(grip); row.appendChild(txt);
      list.appendChild(row);
    });
    el.appendChild(list);

    let dragEl = null, startY = 0;
    function onDown(e) {
      const row = e.target.closest(".orditem");
      if (!row || !list.contains(row)) return;
      dragEl = row; startY = e.clientY;
      dragEl.setPointerCapture(e.pointerId);
      dragEl.style.position = "relative"; dragEl.style.zIndex = "10"; dragEl.style.boxShadow = "var(--shadow-lg)";
    }
    function onMove(e) {
      if (!dragEl) return;
      const dy = e.clientY - startY;
      dragEl.style.transform = "translateY(" + dy + "px)";
      const dragRect = dragEl.getBoundingClientRect();
      const dragCenter = dragRect.top + dragRect.height / 2;
      const siblings = Array.from(list.children).filter(c => c !== dragEl);
      for (const sib of siblings) {
        const r = sib.getBoundingClientRect();
        const sibCenter = r.top + r.height / 2;
        const dragIsAfterSib = !!(sib.compareDocumentPosition(dragEl) & Node.DOCUMENT_POSITION_FOLLOWING);
        if (dragIsAfterSib && dragCenter < sibCenter) { list.insertBefore(dragEl, sib); startY = e.clientY; dragEl.style.transform = "translateY(0px)"; break; }
        if (!dragIsAfterSib && dragCenter > sibCenter) { list.insertBefore(dragEl, sib.nextSibling); startY = e.clientY; dragEl.style.transform = "translateY(0px)"; break; }
      }
    }
    function onUp() {
      if (!dragEl) return;
      dragEl.style.position = ""; dragEl.style.zIndex = ""; dragEl.style.boxShadow = ""; dragEl.style.transform = "";
      dragEl = null;
    }
    list.addEventListener("pointerdown", onDown);
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);

    const bar = document.createElement("div"); bar.className = "row"; bar.style.marginTop = "10px";
    const check = document.createElement("button"); check.type = "button"; check.className = "btn"; check.textContent = "Comprobar";
    bar.appendChild(check);
    const out = document.createElement("div"); out.className = "out"; out.style.marginTop = "10px";
    check.addEventListener("click", () => {
      const currentOrder = Array.from(list.children).map(c => parseInt(c.dataset.idx, 10));
      const allOk = currentOrder.every((v, i) => v === i);
      out.innerHTML = allOk
        ? '<div class="msg ok"><span class="ic">✓</span>¡Perfecto! El orden es correcto.</div>'
        : '<div class="msg bad"><span class="ic">✗</span>El orden todavía no es correcto. ' + (opts.hint || "Revisa e inténtalo de nuevo.") + '</div>';
      record(sel, allOk);
    });
    el.appendChild(bar); el.appendChild(out);
  };

  /* Emparejar arrastrando: palabras (izquierda) se arrastran hacia su definición
     (derecha), con Pointer Events. opts:{pairs:[{l,r}], hint}. */
  window.QuizDragMatch = function (sel, opts) {
    const el = $(sel); if (!el) return;
    declare(sel);
    const wrap = document.createElement("div");
    wrap.style.cssText = "display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:start";
    const tray = document.createElement("div");
    tray.style.cssText = "display:flex;flex-direction:column;gap:8px";
    const slotsWrap = document.createElement("div");
    slotsWrap.style.cssText = "display:flex;flex-direction:column;gap:8px";

    const order = opts.pairs.map((p, i) => i);
    for (let i = order.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); const t = order[i]; order[i] = order[j]; order[j] = t; }
    order.forEach(i => {
      const chip = document.createElement("div");
      chip.className = "dmchip";
      chip.dataset.term = String(i);
      chip.textContent = opts.pairs[i].l;
      chip.style.cssText = "padding:9px 12px;border:1px solid var(--line-2);border-radius:10px;background:var(--surface);cursor:grab;touch-action:none;user-select:none;font-weight:650";
      tray.appendChild(chip);
    });

    const slots = [];
    opts.pairs.forEach((p, i) => {
      const row = document.createElement("div");
      row.style.cssText = "display:flex;gap:8px;align-items:stretch";
      const target = document.createElement("div");
      target.className = "dmslot";
      target.dataset.correct = String(i);
      target.style.cssText = "min-width:110px;min-height:40px;border:2px dashed var(--line-2);border-radius:10px;display:flex;align-items:center;justify-content:center;padding:4px";
      const def = document.createElement("div");
      def.style.cssText = "flex:1;padding:9px 12px;border:1px solid var(--line);border-radius:10px;background:var(--surface-2);font-size:14px";
      def.textContent = p.r;
      row.appendChild(target); row.appendChild(def);
      slotsWrap.appendChild(row);
      slots.push(target);
    });

    wrap.appendChild(tray); wrap.appendChild(slotsWrap);
    el.appendChild(wrap);

    let dragChip = null, offsetX = 0, offsetY = 0;
    function onDown(e) {
      const chip = e.target.closest(".dmchip");
      if (!chip) return;
      dragChip = chip;
      const r = chip.getBoundingClientRect();
      offsetX = e.clientX - r.left; offsetY = e.clientY - r.top;
      chip.setPointerCapture(e.pointerId);
      chip.style.position = "fixed"; chip.style.zIndex = "1000"; chip.style.width = r.width + "px";
      chip.style.left = r.left + "px"; chip.style.top = r.top + "px"; chip.style.boxShadow = "var(--shadow-lg)";
      document.body.appendChild(chip);
    }
    function onMove(e) {
      if (!dragChip) return;
      dragChip.style.left = (e.clientX - offsetX) + "px";
      dragChip.style.top = (e.clientY - offsetY) + "px";
    }
    function onUp(e) {
      if (!dragChip) return;
      const chip = dragChip; dragChip = null;
      chip.style.position = ""; chip.style.zIndex = ""; chip.style.width = ""; chip.style.left = ""; chip.style.top = ""; chip.style.boxShadow = "";
      const under = document.elementFromPoint(e.clientX, e.clientY);
      const slot = under && under.closest(".dmslot");
      if (slot) {
        const existing = slot.querySelector(".dmchip");
        if (existing && existing !== chip) tray.appendChild(existing);
        slot.appendChild(chip);
      } else {
        tray.appendChild(chip);
      }
    }
    wrap.addEventListener("pointerdown", onDown);
    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);

    const bar = document.createElement("div"); bar.className = "row"; bar.style.marginTop = "10px";
    const check = document.createElement("button"); check.type = "button"; check.className = "btn"; check.textContent = "Comprobar";
    bar.appendChild(check);
    const out = document.createElement("div"); out.className = "out"; out.style.marginTop = "10px";
    check.addEventListener("click", () => {
      let ok = 0, done = 0;
      slots.forEach(s => {
        const chip = s.querySelector(".dmchip");
        if (chip) done++;
        if (chip && chip.dataset.term === s.dataset.correct) ok++;
      });
      if (done < slots.length) { out.innerHTML = '<div class="msg bad"><span class="ic">!</span>Coloca una palabra en cada definición antes de comprobar.</div>'; return; }
      const allOk = ok === slots.length;
      out.innerHTML = allOk
        ? '<div class="msg ok"><span class="ic">✓</span>¡Perfecto! Emparejaste correctamente los ' + ok + " elementos.</div>"
        : '<div class="msg bad"><span class="ic">✗</span>Acertaste ' + ok + " de " + slots.length + ". " + (opts.hint || "Revisa e inténtalo de nuevo.") + "</div>";
      record(sel, allOk);
    });
    el.appendChild(bar); el.appendChild(out);
  };
})();
</script>
'''


def esc(s):
    return html.escape(s, quote=False)


def js_str(s):
    return json.dumps(s, ensure_ascii=False)


def build_step(code, questions):
    lines = []
    lines.append('    <section class="step"><div class="step-body">')
    lines.append('      <span class="kicker">Evaluación · Tema %s</span>' % code)
    lines.append('      <h2>Pon a prueba lo aprendido</h2>')
    lines.append('      <p class="muted">Responde estas preguntas para comprobar lo que aprendiste en este tema.</p>')
    for idx, q in enumerate(questions, start=1):
        label = TYPE_LABEL_DISPLAY.get(q["type"], "")
        lines.append('      <div class="callout" style="flex-direction:column;align-items:stretch;gap:6px">')
        lines.append('        <div><b>Pregunta %d</b> <span class="hint">· %s</span></div>' % (idx, label))
        lines.append('        <p style="margin:0">%s</p>' % esc(q["stem"]))
        lines.append('        <div id="preg%d"></div>' % idx)
        lines.append('      </div>')
    lines.append('    </div></section>')
    return "\n".join(lines)


def build_invocations(questions):
    out = []
    for idx, q in enumerate(questions, start=1):
        sel = "#preg%d" % idx
        if q["type"] == "mc":
            opts = []
            for o in q["options"]:
                fb = "¡Correcto! Es la respuesta correcta." if o["ok"] else "No es correcto. Revisa el tema e inténtalo de nuevo."
                opts.append("{label:%s, ok:%s, fb:%s}" % (js_str(o["t"]), "true" if o["ok"] else "false", js_str(fb)))
            out.append("  QuizChoice(%s, { options: [%s] });" % (js_str(sel), ", ".join(opts)))
        elif q["type"] == "ms":
            opts = []
            for o in q["options"]:
                opts.append("{label:%s, ok:%s}" % (js_str(o["t"]), "true" if o["ok"] else "false"))
            hint = "Revisa cuáles opciones cumplen la definición y vuelve a intentarlo."
            out.append("  QuizMulti(%s, { options: [%s], hint: %s });" % (js_str(sel), ", ".join(opts), js_str(hint)))
        elif q["type"] == "cloze":
            bank = ", ".join(js_str(w) for w in q["bank"])
            answers = ", ".join(js_str(a) for a in q["answers"])
            hint = "Revisa el tema y vuelve a intentarlo."
            out.append("  QuizCloze(%s, { paragraph: %s, bank: [%s], answers: [%s], hint: %s });" % (
                js_str(sel), js_str(q["paragraph"]), bank, answers, js_str(hint)))
        elif q["type"] == "sort":
            cats = ", ".join("{id:%s, label:%s}" % (js_str(c), js_str(c)) for c in q["cats"])
            items = ", ".join("{label:%s, cat:%s}" % (js_str(it["t"]), js_str(it["cat"])) for it in q["items"])
            hint = "Revisa el tema y vuelve a intentarlo."
            out.append("  QuizSort(%s, { items: [%s], cats: [%s], hint: %s });" % (
                js_str(sel), items, cats, js_str(hint)))
        elif q["type"] == "match":
            pairs = ", ".join("{l:%s, r:%s}" % (js_str(p["l"]), js_str(p["r"])) for p in q["pairs"])
            hint = "Revisa el tema y vuelve a intentarlo."
            out.append("  QuizMatch(%s, { pairs: [%s], hint: %s });" % (
                js_str(sel), pairs, js_str(hint)))
        elif q["type"] == "order":
            items = ", ".join(js_str(it) for it in q["items"])
            hint = "Revisa el tema y vuelve a intentarlo."
            out.append("  QuizOrder(%s, { items: [%s], hint: %s });" % (
                js_str(sel), items, js_str(hint)))
        elif q["type"] == "dragmatch":
            pairs = ", ".join("{l:%s, r:%s}" % (js_str(p["l"]), js_str(p["r"])) for p in q["pairs"])
            hint = "Revisa el tema y vuelve a intentarlo."
            out.append("  QuizDragMatch(%s, { pairs: [%s], hint: %s });" % (
                js_str(sel), pairs, js_str(hint)))
    return "\n".join(out)


def load_topics_for_lesson(preguntas_dir, lesson_code):
    docx_path = os.path.join(preguntas_dir, "Lección %s - Preguntas.docx" % lesson_code)
    if not os.path.exists(docx_path):
        return None
    paragraphs = get_paragraphs(docx_path)
    return parse_topics(paragraphs)


def process_unit(unit_dir, force=False):
    act_dir = os.path.join(unit_dir, "Actividades")
    preguntas_dir = os.path.join(unit_dir, "Preguntas")
    files = sorted(glob.glob(os.path.join(act_dir, "*.html")))
    topics_cache = {}
    report = []
    for fp in files:
        base = os.path.basename(fp)
        m = re.match(r"^(\d+\.\d+)\.(\d+)\b", base)
        if not m:
            report.append((base, "SKIP: no matched code in filename"))
            continue
        lesson_code = m.group(1)
        code = "%s.%s" % (lesson_code, m.group(2))
        if lesson_code not in topics_cache:
            topics_cache[lesson_code] = load_topics_for_lesson(preguntas_dir, lesson_code)
        topics = topics_cache[lesson_code]
        if topics is None:
            report.append((base, "SKIP: no Preguntas docx for lesson %s" % lesson_code))
            continue
        topic = next((t for t in topics if t["code"] == code), None)
        if topic is None:
            report.append((base, "SKIP: no matching topic code %s in Preguntas docx" % code))
            continue
        questions = topic["questions"]
        if not questions:
            report.append((base, "SKIP: topic %s has no questions" % code))
            continue

        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()

        already = MARK_BEGIN in content
        if already and not force:
            report.append((base, "SKIP: already has questions injected"))
            continue
        if already and force:
            content = re.sub(re.escape(MARK_BEGIN) + r".*?" + re.escape(MARK_END), "", content, flags=re.S)
            content = re.sub(r"<script>\s*" + re.escape(WIDGETS_MARK) + r".*?</script>\s*", "", content, flags=re.S)
            content = re.sub(re.escape(INV_BEGIN) + r".*?" + re.escape(INV_END) + r"\n?", "", content, flags=re.S)

        step_html = build_step(code, questions)
        invocations = build_invocations(questions)

        wrapped_step = "%s\n%s\n%s" % (MARK_BEGIN, step_html, MARK_END)

        deck_anchor = "<script>\n/* Controlador de pasos (deck)"
        if deck_anchor not in content:
            report.append((base, "ERROR: deck.js anchor not found"))
            continue
        content = content.replace(deck_anchor, WIDGETS_BLOCK + "\n" + deck_anchor, 1)

        nav_re = re.compile(r'\n+([ \t]*)</div>\n\n([ \t]*)<div class="nav">')
        mnav = nav_re.search(content)
        if not mnav:
            report.append((base, "ERROR: nav anchor not found"))
            continue
        indent1, indent2 = mnav.group(1), mnav.group(2)
        replacement = "\n\n%s\n\n%s</div>\n\n%s<div class=\"nav\">" % (wrapped_step, indent1, indent2)
        content = content[:mnav.start()] + replacement + content[mnav.end():]

        deckinit_re = re.compile(r"([ \t]*)Deck\.init\(\"\.frame\"\);")
        mdi = deckinit_re.search(content)
        if not mdi:
            report.append((base, "ERROR: Deck.init call not found"))
            continue
        indent = mdi.group(1)
        wrapped_inv = "%s\n%s\n%s" % (INV_BEGIN, invocations, INV_END)
        content = deckinit_re.sub(lambda mm: (wrapped_inv + "\n" + indent + "Deck.init(\".frame\");"), content, count=1)

        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        report.append((base, "OK: injected %d questions (topic %s)" % (len(questions), code)))

    return report


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 inject_preguntas.py <carpeta_unidad> [--force]", file=sys.stderr)
        sys.exit(1)
    unit_dir = sys.argv[1]
    force = "--force" in sys.argv[2:]
    report = process_unit(unit_dir, force=force)
    for base, msg in report:
        print("%-70s %s" % (base, msg))
    n_ok = sum(1 for _, m in report if m.startswith("OK"))
    n_err = sum(1 for _, m in report if m.startswith("ERROR"))
    print("\nTotal: %d OK, %d ERROR, %d files" % (n_ok, n_err, len(report)))


if __name__ == "__main__":
    main()
