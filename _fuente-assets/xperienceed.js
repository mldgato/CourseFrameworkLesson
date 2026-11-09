/* ============================================================
   Integración con la plataforma Xperienceed (iframe + postMessage).
   Contrato:
     - Entrada:  { type:"html-task-start",  payload:{...estado guardado...} }
     - Salida:   { type:"html-task-result", payload:{ score:{max,raw}, list:[{id,title,correct,userResponse,attempt}] } }
   Puntaje por desempeño: max = ejercicios evaluables; raw = correctos.
   ============================================================ */
(function (w) {
  "use strict";
  var Xp = {
    meta: { id: "tarea-html", title: "Actividad" },
    items: {},            // id -> {answered, correct, attempts}
    step: 0,
    completed: false,
    _deck: null,
    _pending: null,
    _ready: false,

    init: function (meta) {
      if (meta) {
        if (meta.id) this.meta.id = meta.id;
        if (meta.title) this.meta.title = meta.title;
      }
      return this;
    },
    // Un ejercicio evaluable se declara (cuenta para el total aunque no se responda).
    declare: function (id) {
      if (!this.items[id]) this.items[id] = { answered: false, correct: false, attempts: 0 };
    },
    // Registra (o actualiza) el resultado de un ejercicio evaluable.
    record: function (id, correct) {
      this.declare(id);
      var it = this.items[id];
      it.answered = true;
      it.correct = !!correct;
      it.attempts++;
    },
    setStep: function (n) { this.step = n; },

    // El deck se registra al terminar de construirse.
    attachDeck: function (api) {
      this._deck = api;
      this._ready = true;
      if (this._pending) { this._applyRestore(this._pending); this._pending = null; }
    },

    _score: function () {
      var ids = Object.keys(this.items);
      if (!ids.length) return { max: 1, raw: this.completed ? 1 : 0 };
      var raw = 0, self = this;
      ids.forEach(function (k) { if (self.items[k].correct) raw++; });
      return { max: ids.length, raw: raw };
    },

    finalizar: function () {
      if (this.completed) return;
      this.completed = true;
      var s = this._score();
      var result = {
        type: "html-task-result",
        payload: {
          score: { max: s.max, raw: s.raw },
          list: [{
            id: this.meta.id,
            title: this.meta.title,
            correct: (s.max > 0 && s.raw === s.max) ? "true" : "false",
            userResponse: "completed",
            attempt: 1
          }]
        }
      };
      try { w.parent.postMessage(JSON.stringify(result), "*"); } catch (e) {}
      if (this._deck && this._deck.onFinished) this._deck.onFinished(s);
      this._banner(s);
    },

    _applyRestore: function (p) {
      if (!p) return;
      var st = (p.step !== undefined) ? p.step : (p.screen !== undefined ? p.screen : null);
      if (st !== null && this._deck && typeof this._deck.go === "function") this._deck.go(st);
      if (p.items && typeof p.items === "object") { for (var k in p.items) this.items[k] = p.items[k]; }
      if (p.completed || p.moduleCompleted) {
        this.completed = true;
        if (this._deck && this._deck.markDone) this._deck.markDone();
      }
    },

    _banner: function (s) {
      var el = document.getElementById("xp-banner");
      if (!el) {
        el = document.createElement("div");
        el.id = "xp-banner"; el.className = "xp-banner";
        document.body.appendChild(el);
      }
      var txt = "Actividad completada";
      if (s && s.max > 0) txt += " · " + s.raw + " / " + s.max + " correctas";
      el.textContent = "✓ " + txt;
      el.style.display = "block";
      setTimeout(function () { el.style.display = "none"; }, 4000);
    }
  };

  // Escuchar html-task-start desde el primer momento (antes de que el deck exista).
  w.addEventListener("message", function (e) {
    var data = e.data;
    if (typeof data === "string") { try { data = JSON.parse(data); } catch (err) { return; } }
    if (!data || data.type !== "html-task-start") return;
    var payload = data.payload || {};
    if (Xp._ready) Xp._applyRestore(payload); else Xp._pending = payload;
  });

  w.Xp = Xp;
})(window);
