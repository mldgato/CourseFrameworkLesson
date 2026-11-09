/* Smoke test headless (jsdom) genérico: carga la actividad, interactúa con
   TODOS los widgets visibles (incluida la nueva sección de preguntas),
   va al último paso, pulsa Finalizar y comprueba que no haya errores de
   consola ni de "error" del window, y que llegue un html-task-result válido. */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const file = process.argv[2];

async function main() {
  const html = fs.readFileSync(file, "utf8");
  const dom = new JSDOM(html, { runScripts: "dangerously", resources: "usable", url: "http://localhost/activity.html" });
  const { window } = dom;

  await new Promise(res => {
    if (window.document.readyState === "complete") return res();
    window.addEventListener("load", res);
  });
  await new Promise(res => setTimeout(res, 30));

  const errors = [];
  window.addEventListener("error", e => errors.push(e.message));

  const messages = [];
  window.addEventListener("message", e => messages.push(e.data));

  const doc = window.document;
  const report = { file: path.basename(file), errors, steps: doc.querySelectorAll(".step").length };

  // Interactuar con cada contenedor id^="preg" (preguntas inyectadas).
  const pregDivs = Array.from(doc.querySelectorAll('[id^="preg"]'));
  report.pregCount = pregDivs.length;
  pregDivs.forEach(div => {
    const selects = div.querySelectorAll("select");
    if (selects.length) {
      selects.forEach(s => { if (s.options.length > 1) s.value = s.options[1].value; s.dispatchEvent(new window.Event("change", { bubbles: true })); });
    } else {
      const chips = div.querySelectorAll("button.chip");
      if (chips.length) chips[0].dispatchEvent(new window.Event("click", { bubbles: true }));
    }
    const btns = Array.from(div.querySelectorAll("button"));
    const check = btns.find(b => b.textContent.trim() === "Comprobar");
    if (check) check.dispatchEvent(new window.Event("click", { bubbles: true }));
  });

  // Ir al último paso y pulsar Finalizar.
  const deckApi = window.Xp && window.Xp._deck;
  if (deckApi) deckApi.go(report.steps - 1);
  await new Promise(res => setTimeout(res, 20));
  const finishBtn = doc.querySelector(".btn.finish");
  report.finishVisible = finishBtn ? finishBtn.style.display !== "none" : false;
  if (finishBtn) finishBtn.dispatchEvent(new window.Event("click", { bubbles: true }));
  await new Promise(res => setTimeout(res, 20));

  const resultMsg = messages.find(m => {
    try { const d = typeof m === "string" ? JSON.parse(m) : m; return d && d.type === "html-task-result"; } catch (e) { return false; }
  });
  report.htmlTaskResult = resultMsg ? (typeof resultMsg === "string" ? JSON.parse(resultMsg) : resultMsg) : null;

  // Restauración.
  window.postMessage(JSON.stringify({ type: "html-task-start", payload: { screen: 1 } }), "*");
  await new Promise(res => setTimeout(res, 20));
  report.restoredStep = window.Xp ? window.Xp.step : null;

  console.log(JSON.stringify(report));
  window.close();
}

main().catch(e => { console.error("FATAL", file, e); process.exit(1); });
