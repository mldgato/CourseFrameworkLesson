/* Copia el contenido de un archivo de texto al portapapeles (Windows, Mac y Linux).
   Uso: node _tools/copy_to_clipboard.js "ruta/al/archivo.html"                     */
const { spawnSync } = require("child_process");
const fs = require("fs");

const file = process.argv[2];
if (!file || !fs.existsSync(file)) {
  console.error("Uso: node _tools/copy_to_clipboard.js <archivo>");
  process.exit(1);
}
const text = fs.readFileSync(file, "utf8");

let r;
if (process.platform === "win32") {
  // PowerShell respeta UTF-8 (clip.exe daña tildes y emojis)
  r = spawnSync("powershell", ["-NoProfile", "-Command",
    "[Console]::InputEncoding=[Text.Encoding]::UTF8; Set-Clipboard -Value ([Console]::In.ReadToEnd())"],
    { input: text, encoding: "utf8" });
} else if (process.platform === "darwin") {
  r = spawnSync("pbcopy", [], { input: text, encoding: "utf8" });
} else {
  r = spawnSync("xclip", ["-selection", "clipboard"], { input: text, encoding: "utf8" });
}
if (r.status !== 0) { console.error("No se pudo copiar al portapapeles:", r.stderr || r.error); process.exit(1); }
console.log(`Copiado al portapapeles: ${file} (${text.length} caracteres)`);
