/* setup.js — prepara el entorno una sola vez.   Uso:  node setup.js        */
const { spawnSync } = require("child_process");
const path = require("path");
const run = (cmd, args, opts = {}) => spawnSync(cmd, args, { stdio: "inherit", shell: true, ...opts }).status === 0;
const has = (cmd) => spawnSync(cmd, ["--version"], { shell: true, stdio: "ignore" }).status === 0;

console.log("== Verificando requisitos ==");
const major = parseInt(process.versions.node.split(".")[0], 10);
if (major < 18) { console.error("Se requiere Node.js 18 o superior."); process.exit(1); }
console.log("Node " + process.version + " OK");

const py = has("python") ? "python" : has("python3") ? "python3" : null;
if (!py) { console.error("No se encontró Python 3.9+ (https://www.python.org/downloads/)."); process.exit(1); }
console.log("Python: " + py + " OK");

console.log("\n== Instalando dependencias de Python (pymupdf) ==");
if (!run(py, ["-m", "pip", "install", "-r", "requirements.txt"])) process.exit(1);

console.log("\n== Instalando dependencias de Node (_tools) ==");
if (!run("npm", ["install", "--silent"], { cwd: path.join(__dirname, "_tools") })) process.exit(1);

console.log("\n== Preparando el kit de videos (ffmpeg, ffprobe; solo la primera vez) ==");
const fs = require("fs");
if (!run(py, ["_video_kit/kit.py", "setup"], { cwd: __dirname })) {
  console.warn("AVISO: el kit de videos no quedó listo. Reintenta con:  " + py + " _video_kit/kit.py setup");
}
const envFile = path.join(__dirname, ".env");
if (!fs.existsSync(envFile)) {
  fs.copyFileSync(path.join(__dirname, ".env.example"), envFile);
  console.log("\nSe creó .env a partir de .env.example.");
}
const hasKey = /^ELEVENLABS_API_KEY=(?!pega_aqui)\S+/m.test(fs.readFileSync(envFile, "utf8"));
if (!hasKey) console.log("PENDIENTE para /videos: abre .env y pega tu clave de ElevenLabs en ELEVENLABS_API_KEY=");

console.log("\nListo. Abre Claude Code en esta carpeta y ejecuta /init-course");
