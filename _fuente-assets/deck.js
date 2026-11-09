/* Controlador de pasos (deck) sin scroll de página + integración Xperienceed.
   Estructura: .deck > .step ; [data-dots] [data-steplabel] [data-count] [data-prev] [data-next].
   En el último paso muestra el botón "Finalizar actividad" (envía el resultado vía Xp). */
(function (global) {
  "use strict";
  function init(rootSel) {
    const root = (rootSel ? document.querySelector(rootSel) : document) || document;
    const steps = Array.from(root.querySelectorAll(".step"));
    if (!steps.length) return null;
    const dotsWrap = root.querySelector("[data-dots]");
    const label = root.querySelector("[data-steplabel]");
    const count = root.querySelector("[data-count]");
    const prev = root.querySelector("[data-prev]");
    const next = root.querySelector("[data-next]");
    let i = 0;

    // Botón "Finalizar actividad" (solo visible en el último paso).
    let finishBtn = null;
    if (next && next.parentNode) {
      finishBtn = document.createElement("button");
      finishBtn.type = "button";
      finishBtn.className = "btn finish";
      finishBtn.textContent = "Finalizar actividad";
      finishBtn.style.display = "none";
      next.parentNode.insertBefore(finishBtn, next.nextSibling);
      finishBtn.addEventListener("click", function () {
        if (global.Xp) global.Xp.finalizar();
      });
    }
    function markDone() {
      if (finishBtn) { finishBtn.disabled = true; finishBtn.textContent = "Completado ✓"; }
    }

    let dots = [];
    if (dotsWrap) {
      steps.forEach((_, idx) => {
        const d = document.createElement("button");
        d.className = "dot"; d.type = "button";
        d.setAttribute("aria-label", "Ir al paso " + (idx + 1));
        d.addEventListener("click", () => go(idx));
        dotsWrap.appendChild(d);
      });
      dots = Array.from(dotsWrap.children);
    }

    function go(n) {
      i = Math.max(0, Math.min(steps.length - 1, n));
      const last = i === steps.length - 1;
      steps.forEach((s, idx) => s.classList.toggle("active", idx === i));
      dots.forEach((d, idx) => { d.classList.toggle("on", idx === i); d.classList.toggle("done", idx < i); });
      if (label) label.textContent = "Paso " + (i + 1) + " de " + steps.length;
      if (count) count.textContent = (i + 1) + " / " + steps.length;
      if (prev) prev.disabled = i === 0;
      if (next) next.style.display = last ? "none" : "";
      if (finishBtn) finishBtn.style.display = last ? "" : "none";
      const active = steps[i]; if (active) active.scrollTop = 0;
      if (global.Xp) global.Xp.setStep(i);
    }

    if (prev) prev.addEventListener("click", () => go(i - 1));
    if (next) next.addEventListener("click", () => { if (i < steps.length - 1) go(i + 1); });
    document.addEventListener("keydown", e => {
      if (e.target && /^(TEXTAREA|INPUT)$/.test(e.target.tagName)) return;
      if (e.key === "ArrowRight") go(i + 1);
      if (e.key === "ArrowLeft") go(i - 1);
    });
    go(0);

    // Registrar el deck en Xp (para restaurar paso/estado y marcar completado).
    if (global.Xp) global.Xp.attachDeck({ go: go, markDone: markDone, onFinished: markDone });

    return { go, current: () => i };
  }
  global.Deck = { init };
})(window);
