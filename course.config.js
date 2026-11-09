/* course.config.js
   Llena los campos de esta sección. El resto lo completa el skill /init-course
   leyendo el PDF del examen.                                                   */

module.exports = {

  /* ── Llena estos campos manualmente ─────────────────────────── */
  id:            "",            // código corto sin espacios (se usa en IDs)
  name:          "",            // nombre completo del curso
  certification: "",            // certificación objetivo
  courseName:    "",            // nombre corto para encabezados

  palette: {
    navy:  "1F3864",
    steel: "2E5496",
    grey:  "595959",
    light: "EAF0F8",
  },

  platform: {
    product:  "",
    courseId: "",
  },

  voices: {
    default: "Jorge",
    ids: {
      "Jorge": "7GCLDRn3tm42Ra1CZCPL",
      "Liz":   "F3pPb09f6SpwgQJHax6h",
    },
  },

  scenario: {
    name:        "",   // /init-course sugiere uno; puedes cambiarlo
    description: "",
  },

  /* ── Lo llena /init-course automáticamente ───────────────────── */
  units: [],
};
