/* Widgets de evaluación conceptual (sin SQL): elección y clasificación.
   Reportan su resultado a Xperienceed (window.Xp) usando el selector como id. */
(function () {
  "use strict";
  const esc = s => String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  const $ = (s, r) => (r || document).querySelector(s);
  const declare = id => { if (window.Xp) window.Xp.declare(id); };
  const record = (id, ok) => { if (window.Xp) window.Xp.record(id, ok); };

  /* Elección simple. opts:{options:[{label,ok,fb}]} */
  window.QuizChoice = function (sel, opts) {
    const el = $(sel); if (!el) return;
    declare(sel);
    const box = document.createElement("div"); box.className = "row";
    const out = document.createElement("div"); out.className = "out"; out.style.marginTop = "10px";
    opts.options.forEach(o => {
      const b = document.createElement("button"); b.type = "button"; b.className = "chip"; b.innerHTML = o.label;
      b.addEventListener("click", () => {
        Array.from(box.children).forEach(x => x.classList.remove("sel")); b.classList.add("sel");
        out.innerHTML = '<div class="msg ' + (o.ok ? "ok" : "bad") + '"><span class="ic">' + (o.ok ? "✓" : "✗") + "</span>" + o.fb + "</div>";
        record(sel, o.ok);
      });
      box.appendChild(b);
    });
    el.appendChild(box); el.appendChild(out);
  };

  /* Clasificación. opts:{items:[{label,cat}], cats:[{id,label}], hint} */
  window.QuizSort = function (sel, opts) {
    const el = $(sel); if (!el) return;
    declare(sel);
    const state = {};
    const wrap = document.createElement("div");
    wrap.style.cssText = "display:flex;flex-direction:column;gap:8px";
    opts.items.forEach((it, i) => {
      const row = document.createElement("div");
      row.style.cssText = "display:flex;gap:8px;align-items:center;flex-wrap:wrap";
      const tag = document.createElement("span");
      tag.innerHTML = it.label; tag.style.cssText = "flex:1;min-width:150px;font-weight:600";
      row.appendChild(tag);
      opts.cats.forEach(cat => {
        const b = document.createElement("button"); b.type = "button"; b.className = "chip"; b.textContent = cat.label;
        b.style.padding = "5px 12px";
        b.addEventListener("click", () => {
          state[i] = cat.id;
          Array.from(row.querySelectorAll("button")).forEach(x => x.classList.remove("sel"));
          b.classList.add("sel");
        });
        row.appendChild(b);
      });
      wrap.appendChild(row);
    });
    const bar = document.createElement("div"); bar.className = "row"; bar.style.marginTop = "6px";
    const check = document.createElement("button"); check.type = "button"; check.className = "btn"; check.textContent = "Comprobar";
    bar.appendChild(check);
    const out = document.createElement("div"); out.className = "out"; out.style.marginTop = "10px";
    check.addEventListener("click", () => {
      let ok = 0, done = 0;
      opts.items.forEach((it, i) => {
        if (state[i] != null) done++;
        if (state[i] === it.cat) ok++;
      });
      if (done < opts.items.length) { out.innerHTML = '<div class="msg bad"><span class="ic">!</span>Clasifica todos los elementos antes de comprobar.</div>'; return; }
      const allOk = ok === opts.items.length;
      out.innerHTML = allOk
        ? '<div class="msg ok"><span class="ic">✓</span>¡Perfecto! Clasificaste correctamente los ' + ok + " elementos.</div>"
        : '<div class="msg bad"><span class="ic">✗</span>Acertaste ' + ok + " de " + opts.items.length + ". " + (opts.hint || "Revisa e inténtalo de nuevo.") + "</div>";
      record(sel, allOk);
    });
    el.appendChild(wrap); el.appendChild(bar); el.appendChild(out);
  };

  /* Selección múltiple (varias correctas), con botón Comprobar. opts:{options:[{label,ok}], hint} */
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

  /* Completar huecos con banco de palabras (un <select> por hueco). opts:{paragraph, bank, answers, hint} */
  window.QuizCloze = function (sel, opts) {
    const el = $(sel); if (!el) return;
    declare(sel);
    const p = document.createElement("p");
    const parts = String(opts.paragraph).split(/\{(\d+)\}/);
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

  /* Emparejar elementos (un <select> por elemento izquierdo, opciones = lado derecho). opts:{pairs:[{l,r}], hint} */
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

  /* Ordenar secuencia arrastrando y soltando (Pointer Events: funciona con
     mouse y con touch). opts:{items:[...en el ORDEN CORRECTO...], hint}.
     Se muestran barajados; el alumno los reordena arrastrando. La corrección
     se evalúa leyendo el orden ACTUAL de los elementos en el DOM al comprobar. */
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

  /* Emparejar arrastrando: palabras (izquierda) se arrastran hacia su
     definición (derecha), usando Pointer Events. opts:{pairs:[{l,r}], hint}.
     l = palabra que se arrastra; r = definición fija (el destino). */
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
