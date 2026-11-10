#!/usr/bin/env python3
"""kit.py — herramienta de producción de los videos por tema (CourseFramework).

Lee todo de course.config.js (temas, voces, nombre del curso). Solo usa la biblioteca estándar.
Comandos (desde la raíz del curso):
  (En Windows usa `python` en vez de `python3`.)
  python3 _video_kit/kit.py setup                  UNA VEZ por equipo: instala ffmpeg/ffprobe/venv en _video_kit/entorno/<sistema>/
  python3 _video_kit/kit.py doctor                 revisa herramientas y clave (no imprime la clave)
  python3 _video_kit/kit.py selftest               prueba de punta a punta sin créditos ni tocar Videos/
  python3 _video_kit/kit.py refresh                sincroniza el control con los temas existentes (Actividades/)
  python3 _video_kit/kit.py status                 avance por unidad
  python3 _video_kit/kit.py next [N]               los próximos N temas pendientes (por defecto 5)
  python3 _video_kit/kit.py teoria X.Y.Z           imprime la teoría del tema (desde el Word de Teoría)
  python3 _video_kit/kit.py scaffold X.Y.Z         crea Videos/Unidad N/_fuente_X.Y.Z/ desde la plantilla
  python3 _video_kit/kit.py narrate X.Y.Z          SCRIPT.md -> narration.mp3 (ElevenLabs) + transcripción + cues.txt + duraciones
  python3 _video_kit/kit.py snap X.Y.Z             fotogramas de revisión (sin enviar nada a terceros)
  python3 _video_kit/kit.py render X.Y.Z           lint + validate + render + audio completo + verificación + copia final + control
  python3 _video_kit/kit.py mark X.Y.Z ESTADO      cambia el estado a mano (pendiente|en_progreso|hecho|hecho_sin_marco)
"""
import argparse, datetime, html, json, os, platform, re, shutil, subprocess, sys, unicodedata, zipfile
from pathlib import Path

for _s in (sys.stdout, sys.stderr):   # Windows: la consola usa cp1252 y fallaría al imprimir tildes/símbolos
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

ROOT = Path(__file__).resolve().parent.parent
VIDEOS = Path(os.environ.get("VIDEO_ROOT", ROOT / "Videos"))
CONTROL = VIDEOS / "control_videos.json"
CONTROL_MD = VIDEOS / "CONTROL_VIDEOS.md"
KIT = ROOT / "_video_kit"
IS_WIN = os.name == "nt"
PLAT = f"{sys.platform}-{platform.machine().lower()}"          # darwin-arm64 | win32-amd64 | linux-x86_64
HOME_KIT = KIT / "entorno" / PLAT   # herramientas por sistema operativo (misma carpeta sincronizable sin choques entre equipos); se crean con `kit.py setup`
EXE = ".exe" if IS_WIN else ""
FFMPEG = str(HOME_KIT / "bin" / f"ffmpeg{EXE}")
FFPROBE = str(HOME_KIT / "bin" / f"ffprobe{EXE}")
def venv_python(): return HOME_KIT / "venv" / ("Scripts/python.exe" if IS_WIN else "bin/python")
HF = "hyperframes@0.6.70"          # versión validada en el piloto
INTRO, PAUSA, OUTRO = 3.0, 0.9, 4.6  # segundos: intro (≤3), pausa tras la narración, cierre


def load_config():
    """Lee course.config.js con Node (es la fuente de verdad del curso)."""
    cfg = ROOT / "course.config.js"
    node = shutil.which("node")
    if not (cfg.exists() and node): return {}
    r = subprocess.run([node, "-e", "console.log(JSON.stringify(require(process.argv[1])))", str(cfg)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    try: return json.loads(r.stdout)
    except Exception: return {}


CONFIG = load_config()
_v = CONFIG.get("voices", {})
DEFAULT_VOICE_NAME = _v.get("default") or "Daniel"
DEFAULT_VOICE = (_v.get("ids") or {}).get(DEFAULT_VOICE_NAME) or "onwK4e9ZLuTAKqWW03F9"   # respaldo: Daniel (voz predefinida)
COURSE_NAME = CONFIG.get("courseName") or CONFIG.get("name") or "Curso"


def voice_id(name_or_id):
    """Acepta el nombre de una voz de course.config.js (p. ej. Liz) o un ID de ElevenLabs."""
    ids = _v.get("ids") or {}
    for k, v in ids.items():
        if k.lower() == str(name_or_id).lower(): return k, v
    for k, v in ids.items():
        if v == name_or_id: return k, v
    return None, name_or_id
ESTADOS = ["pendiente", "en_progreso", "hecho", "hecho_sin_marco"]


def nfc(s): return unicodedata.normalize("NFC", s)
def die(msg): print("ERROR:", msg); sys.exit(1)
def tid_key(t): return tuple(int(x) for x in t.split("."))


# ------------------------------------------------------------------ entorno
def load_key():
    for name in (".env", ".ENV"):
        p = ROOT / name
        if p.exists():
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line.startswith("ELEVENLABS_API_KEY="):
                    v = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if v and not v.startswith("pega_aqui"): return v   # ignora el valor de ejemplo de .env.example
    v = os.environ.get("ELEVENLABS_API_KEY", "")
    return "" if v.startswith("pega_aqui") else v


def tool_env():
    e = os.environ.copy()
    e["PATH"] = str(HOME_KIT / "bin") + os.pathsep + e.get("PATH", "")
    e["PYTHONUTF8"] = "1"; e["PYTHONIOENCODING"] = "utf-8"   # Windows: evita cp1252 al leer SCRIPT.md y otros textos
    if Path("/etc/ssl/cert.pem").exists():              # macOS: el Python de python.org no trae CA y falla SSL sin esto
        e["SSL_CERT_FILE"] = "/etc/ssl/cert.pem"; e["REQUESTS_CA_BUNDLE"] = "/etc/ssl/cert.pem"
    k = load_key()
    if k: e["ELEVENLABS_API_KEY"] = k
    return e


def run(cmd, cwd=None, log=None, check=True):
    """Ejecuta un comando con el entorno del kit. Si log, guarda la salida en ese archivo."""
    p = subprocess.run(cmd, cwd=cwd, env=tool_env(), text=True, encoding="utf-8", errors="replace", capture_output=True)
    out = (p.stdout or "") + (p.stderr or "")
    if log: Path(log).write_text(out, encoding="utf-8")
    if check and p.returncode != 0:
        print(out[-2500:]); die(f"falló: {' '.join(map(str, cmd))[:160]}")
    return p.returncode, out


def probe_duration(path):
    _, out = run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)])
    return float(out.strip().splitlines()[-1])


def mean_volume(path, a, b):
    _, out = run([FFMPEG, "-hide_banner", "-ss", str(a), "-to", str(b), "-i", str(path), "-vn", "-af", "volumedetect", "-f", "null", "-"], check=False)
    m = re.search(r"mean_volume:\s*(-?[\d.]+|-inf)", out)
    return float(m.group(1)) if m and m.group(1) != "-inf" else -99.0


# ------------------------------------------------------------------ control
def discover_topics():
    """Un tema = cada tema de course.config.js (units > lessons > topics). Si el config no los trae,
    se descubren por las actividades 'X.Y.Z Título.html' de cada carpeta Unidad*/Actividades."""
    topics = {}
    for u in CONFIG.get("units") or []:
        for l in u.get("lessons") or []:
            for tp in l.get("topics") or []:
                tid = str(tp["id"])
                titulo = re.sub(r'[\\/:*?"<>|]', "", tp["title"]).strip()
                topics[tid] = {"id": tid, "unidad": int(u["id"]), "leccion": str(l["id"]),
                               "titulo": titulo, "archivo": f"{tid} {titulo}", "estado": "pendiente"}
    for ud in sorted(ROOT.glob("Unidad*")):
        m = re.match(r"Unidad (\d+)", nfc(ud.name))
        act = ud / "Actividades"
        if not (m and act.is_dir()): continue
        for f in act.iterdir():
            mm = re.match(r"^(\d+\.\d+\.\d+) (.+)\.html$", nfc(f.name))
            if mm and mm.group(1) not in topics:
                tid, titulo = mm.group(1), mm.group(2)
                topics[tid] = {"id": tid, "unidad": int(m.group(1)), "leccion": ".".join(tid.split(".")[:2]),
                               "titulo": titulo, "archivo": f"{tid} {titulo}", "estado": "pendiente"}
    return [topics[k] for k in sorted(topics, key=tid_key)]


def load():
    if not CONTROL.exists(): cmd_refresh(None)   # se crea solo desde course.config.js
    return json.loads(CONTROL.read_text(encoding="utf-8"))


def save(data):
    CONTROL.parent.mkdir(parents=True, exist_ok=True)
    CONTROL.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    write_md(data)


def find(data, tid):
    for t in data["temas"]:
        if t["id"] == tid: return t
    cmd_refresh(None)   # quizá el config cambió: reintenta una vez
    fresh = load()["temas"]
    for t in fresh:
        if t["id"] == tid:
            data["temas"] = fresh; return t
    die(f"el tema {tid} no existe en course.config.js (¿corriste /init-course?)")


def cmd_refresh(_a):
    found = discover_topics()
    if CONTROL.exists():
        data = load(); cur = {t["id"]: t for t in data["temas"]}
    else:
        data = {"formato": 1, "nota": "Fuente de verdad del avance de videos. Se edita con kit.py; CONTROL_VIDEOS.md se regenera solo.", "temas": []}
        cur = {}
    added = 0
    merged = []
    for t in found:
        if t["id"] in cur:
            old = cur[t["id"]]; old.update({k: t[k] for k in ("unidad", "leccion", "titulo", "archivo")}); merged.append(old)
        else:
            merged.append(t); added += 1
    data["temas"] = merged
    save(data)
    print(f"control actualizado: {len(merged)} temas ({added} nuevos) -> {CONTROL}")


def write_md(data):
    L = ["# Control de videos por tema", "",
         "Generado por `_video_kit/kit.py` a partir de `control_videos.json` (NO editar a mano; usa `kit.py mark`).", "",
         "Leyenda: `[x]` hecho (con intro y cierre) · `[~]` hecho SIN intro/cierre (pendiente de re-render) · `[>]` en progreso · `[ ]` pendiente", ""]
    tot = len(data["temas"]); done = sum(t["estado"] == "hecho" for t in data["temas"])
    part = sum(t["estado"] == "hecho_sin_marco" for t in data["temas"])
    L += [f"**Avance: {done}/{tot} hechos** ({part} hecho(s) sin intro/cierre).", "", "| Unidad | Hechos | Total |", "|---|---|---|"]
    for u in sorted({t["unidad"] for t in data["temas"]}):
        ts = [t for t in data["temas"] if t["unidad"] == u]
        L.append(f"| {u} | {sum(t['estado'] == 'hecho' for t in ts)} | {len(ts)} |")
    sym = {"hecho": "[x]", "hecho_sin_marco": "[~]", "en_progreso": "[>]", "pendiente": "[ ]"}
    for u in sorted({t["unidad"] for t in data["temas"]}):
        L += ["", f"## Unidad {u}", "", "| | Tema | Duración | Voz | Fecha | Notas |", "|---|---|---|---|---|---|"]
        for t in [t for t in data["temas"] if t["unidad"] == u]:
            d = f"{int(t['duracion_s']) // 60}:{int(t['duracion_s']) % 60:02d}" if t.get("duracion_s") else ""
            L.append(f"| {sym[t['estado']]} | {t['archivo']} | {d} | {t.get('voz', '')} | {t.get('fecha', '')} | {t.get('nota', '')} |")
    CONTROL_MD.write_text("\n".join(L) + "\n", encoding="utf-8")


def cmd_status(_a):
    data = load(); tot = len(data["temas"])
    for u in sorted({t["unidad"] for t in data["temas"]}):
        ts = [t for t in data["temas"] if t["unidad"] == u]
        c = {e: sum(t["estado"] == e for t in ts) for e in ESTADOS}
        print(f"Unidad {u}: {len(ts):2d} temas | hecho {c['hecho']} | sin marco {c['hecho_sin_marco']} | en progreso {c['en_progreso']} | pendiente {c['pendiente']}")
    print(f"TOTAL: {sum(t['estado'] == 'hecho' for t in data['temas'])}/{tot} hechos")


def cmd_next(a):
    data = load(); n = 0
    for t in data["temas"]:
        if t["estado"] in ("pendiente", "en_progreso"):
            print(f"{t['id']:8s} [{t['estado']}] {t['titulo']}"); n += 1
            if n >= a.n: break
    if n == 0: print("No quedan temas pendientes.")


def cmd_mark(a):
    data = load(); t = find(data, a.id)
    if a.estado not in ESTADOS: die(f"estado inválido; usa: {', '.join(ESTADOS)}")
    t["estado"] = a.estado
    if a.nota: t["nota"] = a.nota
    save(data); print(f"{a.id} -> {a.estado}")


# ------------------------------------------------------------------ teoría (Word -> texto)
def lesson_docx(tid):
    lec = ".".join(tid.split(".")[:2])
    for ud in ROOT.glob("Unidad*"):
        for sub in ud.iterdir():
            if nfc(sub.name) == "Teoría":
                for f in sub.iterdir():
                    if nfc(f.name).startswith(f"Lección {lec} ") and f.suffix == ".docx": return f
    return None


def docx_paragraphs(path):
    x = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8")
    for p in re.findall(r"<w:p[ >].*?</w:p>", x, flags=re.S):
        st = re.search(r'<w:pStyle w:val="([^"]+)"', p)
        t = html.unescape("".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", p)))
        if t.strip(): yield (st.group(1) if st else ""), t.strip()


def topic_theory(tid):
    out, inside = [], False
    docx = lesson_docx(tid)
    if docx is None:
        return (f"# {tid}\n\nNo existe todavía el Word de teoría de esta lección (corre /word-content {tid}). "
                "Escribe el guion con el PDF del examen y course.config.js.\n")
    for st, t in docx_paragraphs(docx):
        if st == "Heading1":
            if inside: break
            inside = re.sub(r"\s+", " ", t).startswith(tid + " ")
            if inside: out.append("# " + re.sub(r"\s+", " ", t)); continue
        if inside:
            out.append(("## " if st == "Heading2" else "### " if st == "Heading3" else "- " if st == "ListParagraph" else "") + t)
    if not out: return f"# {tid}\n\nNo encontré el tema {tid} dentro del Word de teoría ({docx.name}). Escribe el guion con el PDF del examen y course.config.js.\n"
    return "\n\n".join(out) + "\n"


def cmd_teoria(a): print(topic_theory(a.id))


# ------------------------------------------------------------------ carpeta de trabajo
def workdir(t): return VIDEOS / f"Unidad {t['unidad']}" / f"_fuente_{t['id']}"


def sync_timing(index, narr):
    end = round(INTRO + narr + PAUSA, 2); total = round(end + OUTRO, 2); narr = round(narr, 2)
    s = index.read_text(encoding="utf-8")
    for name, val in (("INTRO", INTRO), ("NARR ", narr), ("END  ", end), ("TOTAL", total)):
        s = re.sub(rf"(const {name}\s*=\s*)[^;]+(;)", lambda m: f"{m.group(1)}{val}{m.group(2)}", s)
    s = re.sub(r'(id="root" data-composition-id="main" data-start="0" data-duration=")[^"]+(")', lambda m: f"{m.group(1)}{total}{m.group(2)}", s)
    s = re.sub(r'(<audio id="narr" data-start=")[^"]*(" data-duration=")[^"]+(")', lambda m: f"{m.group(1)}{INTRO}{m.group(2)}{narr}{m.group(3)}", s)
    index.write_text(s, encoding="utf-8")
    return narr, end, total


def cmd_scaffold(a):
    data = load(); t = find(data, a.id); wd = workdir(t)
    kept = {}
    if wd.exists():
        has_mp3 = (wd / "narration.mp3").exists()
        if a.keep_narration:
            if not has_mp3: die("no hay narration.mp3 que conservar")
            tmp = wd.parent / f".keep_{t['id']}"; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir()
            for name in ("narration.mp3", "SCRIPT.md", "voz.txt", "cues.txt", "edit"):
                if (wd / name).exists(): shutil.move(str(wd / name), str(tmp / name)); kept[name] = tmp / name
            if (wd / "index.html").exists(): shutil.move(str(wd / "index.html"), str(tmp / "index.legacy.html")); kept["index.legacy.html"] = tmp / "index.legacy.html"
            shutil.rmtree(wd)
        elif has_mp3:
            die("la carpeta tiene narration.mp3 (cuesta créditos rehacerla). Para rehacer las escenas conservándola usa --keep-narration")
        elif not a.force:
            die(f"{wd} ya existe (usa --force para recrear; se pierde lo escrito)")
        else:
            shutil.rmtree(wd)
    shutil.copytree(KIT / "template", wd)
    for name, src in kept.items(): shutil.move(str(src), str(wd / name))
    if kept: shutil.rmtree(wd.parent / f".keep_{t['id']}", ignore_errors=True)
    idx = wd / "index.html"
    s = idx.read_text(encoding="utf-8")
    logo = next((ROOT / n for n in ("LogoCurso.png", "LogoCurso.jpg", "LogoCurso.svg") if (ROOT / n).exists()), None)
    if logo:
        shutil.copy2(logo, wd / "assets" / logo.name)
        intro_media = f'<img id="intro-logo" src="assets/{logo.name}" alt="{html.escape(COURSE_NAME)}" />'
    else:   # sin logo: la intro muestra el nombre del curso como texto
        intro_media = f'<div id="intro-logo" style="font-size:120px;font-weight:800;color:#0b2238;text-align:center">{html.escape(COURSE_NAME)}</div>'
    s = re.sub(r'<img id="intro-logo"[^>]*/>', lambda m: intro_media, s)
    for k, v in (("{{ID}}", t["id"]), ("{{TITULO}}", html.escape(t["titulo"])), ("{{CURSO}}", html.escape(COURSE_NAME)), ("{{INTRO}}", str(INTRO)),
                 ("{{NARR}}", "0"), ("{{END}}", "0"), ("{{TOTAL}}", "0")):
        s = s.replace(k, v)
    idx.write_text(s, encoding="utf-8")
    (wd / "meta.json").write_text(json.dumps({"id": f"video-{t['id']}", "name": f"video-{t['id']}"}), encoding="utf-8")
    (wd / "teoria.md").write_text(topic_theory(t["id"]), encoding="utf-8")
    if not (wd / "SCRIPT.md").exists(): (wd / "SCRIPT.md").write_text("[warmly] ESCRIBE AQUI EL GUION (solo narración, con etiquetas de tono [..]; sin encabezados ni notas).\n", encoding="utf-8")
    t["estado"] = "en_progreso"; save(data)
    print(f"creado {wd}\n  teoria.md  <- teoría del tema\n  SCRIPT.md  <- escribe el guion aprobado aquí\n  index.html <- plantilla con intro y cierre ya integrados")
    if kept: print("  conservados: " + ", ".join(kept) + "\n  (index.legacy.html = escenas antiguas para copiar; luego: kit.py narrate " + t["id"] + " --reuse)")


# ------------------------------------------------------------------ narración
def cmd_narrate(a):
    data = load(); t = find(data, a.id); wd = workdir(t)
    if not wd.exists(): die("primero: kit.py scaffold " + a.id)
    script = wd / "SCRIPT.md"; mp3 = wd / "narration.mp3"
    text = script.read_text(encoding="utf-8")
    if "ESCRIBE AQUI EL GUION" in text and not a.silent: die("SCRIPT.md aún es el marcador; escribe el guion aprobado")
    if any(l.lstrip().startswith("#") for l in text.splitlines()): die("SCRIPT.md debe tener SOLO narración (sin líneas que empiecen con #)")
    if a.reuse:
        if not mp3.exists(): die("--reuse necesita un narration.mp3 existente")
        voz = (wd / "voz.txt").read_text(encoding="utf-8") if (wd / "voz.txt").exists() else (t.get("voz") or f"{DEFAULT_VOICE_NAME} ({DEFAULT_VOICE})")
    else:
        if mp3.exists() and not a.force:
            die("narration.mp3 ya existe. Regenerarla GASTA créditos de ElevenLabs; usa --reuse para conservarla o --force para regenerarla")
        if mp3.exists(): mp3.unlink(); (wd / "edit" / "transcripts" / "narration.json").unlink(missing_ok=True)
        if a.silent:
            run([FFMPEG, "-y", "-f", "lavfi", "-i", f"sine=frequency=300:duration={a.silent}", "-af", "volume=0.5", "-c:a", "libmp3lame", "-q:a", "5", str(mp3)])
            voz = "tono de prueba (prueba técnica)"
        else:
            if not load_key(): die("no hay ELEVENLABS_API_KEY. Copia .env.example a .env (en la raíz del proyecto) y pon tu clave de ElevenLabs")
            nm, vid = voice_id(a.voice)
            a.voice = vid; a.voice_name = nm or a.voice_name
            print(f"enviando {len(text.strip())} caracteres a ElevenLabs eleven_v3 (≈ ese número de créditos)…")
            run([str(venv_python()), str(KIT / "tools/tts_v3.py"), "--voice", a.voice, "--stability", str(a.stability),
                 "--script", str(script), "--out", str(mp3)], cwd=wd)
            voz = f"{a.voice_name} ({a.voice})"
    narr = probe_duration(mp3)
    if not a.silent:
        run([str(venv_python()), str(KIT / "tools/transcribe.py"), str(mp3), "--edit-dir", str(wd / "edit"), "--language", "es"], cwd=wd)
        write_cues(wd)
    narr, end, total = sync_timing(wd / "index.html", narr)
    (wd / "voz.txt").write_text(voz, encoding="utf-8")
    print(f"narración: {narr}s | intro {INTRO}s | cierre empieza en {end}s | total {total}s  (marcas de contenido: at(t) con t de cues.txt)")
    if not (2 * 60 <= narr <= 3 * 60 + 5): print("AVISO: la narración está fuera del rango 2–3 min acordado")


def write_cues(wd):
    d = json.loads((wd / "edit/transcripts/narration.json").read_text(encoding="utf-8"))
    w = [x for x in d["words"] if x.get("type") == "word"]
    sents, cur = [], []
    for x in w:
        cur.append(x)
        if x["text"].rstrip().endswith((".", "?", "!", ":")): sents.append(cur); cur = []
    if cur: sents.append(cur)
    L = ["# cues.txt — tiempos de la NARRACIÓN (segundos). En el HTML usa at(t): at() suma la intro.", "", "## Oraciones (inicio-fin)"]
    L += [f"{s[0]['start']:7.2f}-{s[-1]['end']:7.2f}  {' '.join(x['text'] for x in s)}" for s in sents]
    L += ["", "## Palabras (inicio:palabra)", " ".join(f"{x['start']:.1f}:{x['text']}" for x in w)]
    (wd / "cues.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ revisión y render
def hf(wd, *args, log=None, check=True):
    return run([shutil.which("npx") or "npx", "--yes", HF, *args], cwd=wd, log=log, check=check)   # which: en Windows es npx.cmd


def cmd_snap(a):
    data = load(); t = find(data, a.id); wd = workdir(t)
    narr = probe_duration(wd / "narration.mp3"); sync_timing(wd / "index.html", narr)
    at = a.at or ",".join(f"{x:.1f}" for x in [1.2, INTRO + 5] + [INTRO + narr * f for f in (0.2, 0.35, 0.5, 0.65, 0.8, 0.95)] + [INTRO + narr + PAUSA + 2.2])
    _, out = hf(wd, "snapshot", "--at", at, "--describe", "false")  # --describe false: no enviar imágenes a Gemini
    print(out[-900:]); print(f"Revisa {wd}/snapshots/contact-sheet-*.jpg y los frame-*.png")


def cmd_render(a):
    data = load(); t = find(data, a.id); wd = workdir(t)
    mp3 = wd / "narration.mp3"
    if not mp3.exists(): die("falta narration.mp3 (kit.py narrate)")
    narr = probe_duration(mp3); narr, end, total = sync_timing(wd / "index.html", narr)
    (wd / "out").mkdir(exist_ok=True)
    rc, out = hf(wd, "lint", check=False)
    if not re.search(r"\b0 errors?(\(s\))?", out): print(out[-2000:]); die("lint con errores")
    if not a.no_validate:
        rc, out = hf(wd, "validate", check=False)
        if "No console errors" not in out: print(out[-2000:]); die("validate reportó errores de consola")
    print(f"render {a.quality} de {total}s (≈{int(total * 30)} fotogramas; tarda unos minutos)…")
    hf(wd, "render", "--fps", "30", "--quality", a.quality, "--output", "out/render.mp4", log=wd / "out/render.log")
    final = wd / "out/final.mp4"
    # El mezclador de HyperFrames recorta el audio (~10 s del final); se descarta y se pone la narración original, desplazada por la intro.
    run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", str(wd / "out/render.mp4"), "-i", str(mp3), "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
         "-af", f"adelay={int(INTRO * 1000)}:all=1,apad=whole_dur={total}", "-t", str(total), "-movflags", "+faststart", str(final)])
    # verificación
    dur = probe_duration(final); problems = []
    if abs(dur - total) > 0.3: problems.append(f"duración {dur:.2f}s != esperada {total}s")
    tail = mean_volume(final, INTRO + narr - 4, INTRO + narr - 0.5)
    if tail < -45: problems.append(f"el final de la narración está en silencio ({tail} dB)")
    head = mean_volume(final, INTRO + 0.5, INTRO + 4)
    if head < -45: problems.append(f"el inicio de la narración está en silencio ({head} dB)")
    intro_v = mean_volume(final, 0.2, INTRO - 0.3)
    if intro_v > -50 and not a.allow_intro_audio: problems.append("hay audio durante la intro (debería ser silencio)")
    print(f"verificación: duración {dur:.2f}s (esperada {total}s) | volumen inicio {head} dB | final narración {tail} dB")
    if problems: die("; ".join(problems))
    dest = VIDEOS / f"Unidad {t['unidad']}" / f"{t['archivo']}.mp4"
    shutil.copy2(final, dest)
    voz = (wd / "voz.txt").read_text(encoding="utf-8") if (wd / "voz.txt").exists() else ""
    t.update({"estado": "hecho", "video": str(dest.relative_to(ROOT)) if str(dest).startswith(str(ROOT)) else str(dest), "duracion_s": round(dur, 1),
              "voz": voz, "fecha": datetime.date.today().isoformat(), "intro_cierre": True})
    save(data); print(f"LISTO: {dest}")


def chrome_found():
    pf, pf86, local = (os.environ.get(k, "") for k in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"))
    tail = Path("Google") / "Chrome" / "Application" / "chrome.exe"
    cands = [Path("/Applications/Google Chrome.app")] + [Path(b) / tail for b in (pf, pf86, local) if b]
    return any(Path(c).exists() for c in cands) or any(shutil.which(x) for x in ("google-chrome", "chromium", "chrome"))


def cmd_doctor(_a):
    ok = True
    print(f"sistema: {PLAT} | python {platform.python_version()}")
    for n, p in (("ffmpeg", FFMPEG), ("ffprobe", FFPROBE)):
        print(f"{n}:", "OK" if Path(p).exists() else "FALTA (python _video_kit/kit.py setup)"); ok &= Path(p).exists()
    v = venv_python(); print("venv requests:", "OK" if v.exists() else "FALTA (python _video_kit/kit.py setup)"); ok &= v.exists()
    print("ELEVENLABS_API_KEY:", "encontrada" if load_key() else "NO encontrada: copia .env.example a .env en la raíz del proyecto y pon tu clave"); ok &= bool(load_key())
    print("Chrome:", "OK" if chrome_found() else "FALTA (instala Google Chrome)"); print("node:", shutil.which("node") or "FALTA (instala Node.js 22 o superior)")
    ok &= bool(shutil.which("node") and shutil.which("npx"))
    print("course.config.js:", f"OK ({len(discover_topics())} temas)" if discover_topics() else "sin temas: corre /init-course")
    sys.exit(0 if ok else 1)


def cmd_setup(_a):
    """Crea (una vez por equipo/sistema, idempotente) ffmpeg, ffprobe y el venv dentro de _video_kit/entorno/<sistema>/."""
    npm = shutil.which("npm")
    if not (shutil.which("node") and npm): die("Falta Node.js 22 o superior (https://nodejs.org). Instálalo y vuelve a correr este comando.")
    (HOME_KIT / "bin").mkdir(parents=True, exist_ok=True)
    if not (Path(FFMPEG).exists() and Path(FFPROBE).exists()):
        print("descargando ffmpeg/ffprobe estáticos con npm (temporal)…")
        tmp = HOME_KIT / "_npm"; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir(parents=True)
        (tmp / "package.json").write_text('{"name":"tmp","private":true}', encoding="utf-8")
        run([npm, "i", "ffmpeg-static", "ffprobe-static"], cwd=tmp, log=tmp / "npm.log")
        m = platform.machine().lower(); arch = "arm64" if m in ("arm64", "aarch64") else "x64"
        osd = {"darwin": "darwin", "win32": "win32"}.get(sys.platform, "linux")
        shutil.copy2(tmp / "node_modules/ffmpeg-static" / f"ffmpeg{EXE}", FFMPEG)
        shutil.copy2(tmp / "node_modules/ffprobe-static/bin" / osd / arch / f"ffprobe{EXE}", FFPROBE)
        for f in (FFMPEG, FFPROBE): os.chmod(f, 0o755)
        shutil.rmtree(tmp, ignore_errors=True)      # node_modules ya no hace falta
    v = venv_python()
    if not (v.exists() and run([str(v), "-c", "import requests"], check=False)[0] == 0):
        print("creando venv con requests…")
        shutil.rmtree(HOME_KIT / "venv", ignore_errors=True)
        run([sys.executable, "-m", "venv", str(HOME_KIT / "venv")]); run([str(v), "-m", "pip", "install", "-q", "requests"])
    print("LISTO. Herramientas en", HOME_KIT); cmd_doctor(None)


def cmd_selftest(_a):
    """Prueba técnica de punta a punta en un directorio temporal: NO toca Videos/, NO usa ElevenLabs, NO gasta créditos."""
    import tempfile
    global VIDEOS, CONTROL, CONTROL_MD
    tmp = Path(tempfile.mkdtemp(prefix="videokit_selftest_"))
    VIDEOS, CONTROL, CONTROL_MD = tmp, tmp / "control_videos.json", tmp / "CONTROL_VIDEOS.md"
    try:
        cmd_refresh(None); data = load()
        if not data["temas"]:   # curso aún sin /init-course: tema sintético para probar la maquinaria
            data["temas"] = [{"id": "9.9.9", "unidad": 9, "leccion": "9.9", "titulo": "Prueba tecnica", "archivo": "9.9.9 Prueba tecnica", "estado": "pendiente"}]
            save(data)
        tid = data["temas"][-1]["id"]
        cmd_scaffold(argparse.Namespace(id=tid, force=False, keep_narration=False))
        cmd_narrate(argparse.Namespace(id=tid, voice=DEFAULT_VOICE, voice_name=DEFAULT_VOICE_NAME, stability=0.5, force=False, silent=10, reuse=False))
        cmd_render(argparse.Namespace(id=tid, quality="draft", no_validate=False, allow_intro_audio=True))
        t = find(load(), tid); assert t["estado"] == "hecho" and Path(str(tmp / f"Unidad {t['unidad']}" / f"{t['archivo']}.mp4")).exists()
        print(f"SELFTEST OK: intro + contenido + cierre + audio verificados con el tema {tid} (video de prueba descartado).")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    s.add_parser("doctor").set_defaults(f=cmd_doctor)
    s.add_parser("setup").set_defaults(f=cmd_setup)
    s.add_parser("selftest").set_defaults(f=cmd_selftest)
    s.add_parser("refresh").set_defaults(f=cmd_refresh)
    s.add_parser("status").set_defaults(f=cmd_status)
    x = s.add_parser("next"); x.add_argument("n", nargs="?", type=int, default=5); x.set_defaults(f=cmd_next)
    x = s.add_parser("teoria"); x.add_argument("id"); x.set_defaults(f=cmd_teoria)
    x = s.add_parser("scaffold"); x.add_argument("id"); x.add_argument("--force", action="store_true")
    x.add_argument("--keep-narration", action="store_true", help="rehace las escenas conservando narration.mp3, SCRIPT.md y transcripción"); x.set_defaults(f=cmd_scaffold)
    x = s.add_parser("narrate"); x.add_argument("id"); x.add_argument("--voice", default=DEFAULT_VOICE, help="nombre (Jorge, Liz…) de course.config.js o un ID de ElevenLabs"); x.add_argument("--voice-name", default=DEFAULT_VOICE_NAME)
    x.add_argument("--stability", type=float, default=0.5); x.add_argument("--force", action="store_true")
    x.add_argument("--reuse", action="store_true", help="usa el narration.mp3 existente (sin ElevenLabs): solo transcribe si falta, genera cues y sincroniza tiempos")
    x.add_argument("--silent", type=float, help="PRUEBA TÉCNICA: audio de tono de N s, sin ElevenLabs ni créditos"); x.set_defaults(f=cmd_narrate)
    x = s.add_parser("snap"); x.add_argument("id"); x.add_argument("--at"); x.set_defaults(f=cmd_snap)
    x = s.add_parser("render"); x.add_argument("id"); x.add_argument("--quality", default="standard", choices=["draft", "standard", "high"])
    x.add_argument("--no-validate", action="store_true"); x.add_argument("--allow-intro-audio", action="store_true"); x.set_defaults(f=cmd_render)
    x = s.add_parser("mark"); x.add_argument("id"); x.add_argument("estado"); x.add_argument("--nota"); x.set_defaults(f=cmd_mark)
    a = p.parse_args(); a.f(a)


if __name__ == "__main__":
    main()
