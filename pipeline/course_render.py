#!/usr/bin/env python3
"""Montaggio di un videocorso "a slide" con il personaggio del pacchetto clip.

Ingressi (pacchetto del corso): Storyboard_Animazione.xlsx, Slide_Fotovoltaico.pptx (o simile),
Screenshot_App/, voce clonata ElevenLabs, clip scontornate in output/clip_pack/clips_alfa.

  python3 pipeline/course_render.py prepara   # slide -> immagini, evidenziazioni, clip personaggio
  python3 pipeline/course_render.py voce      # voce per scena (ElevenLabs)
  python3 pipeline/course_render.py capitoli [N ...]   # rendering dei capitoli (in parallelo)
  python3 pipeline/course_render.py corso     # unisce i capitoli, SRT completo, verifiche, report
"""
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
import render as rd  # noqa: E402  (SRT, probe)
from providers import ffprobe_duration  # noqa: E402

NOME_CORSO = os.environ.get("CORSO", "fotovoltaici")   # cartella in corsi/ (es. CORSO=gestione-finanziamenti)
CORSO = ROOT / "corsi" / NOME_CORSO
MAT = CORSO / "materiale"
OUT = ROOT / "output" / NOME_CORSO
SLIDE_DIR = OUT / "slide"
CLIPS = ROOT / "output" / "clip_pack" / "clips_alfa"
POSE_DIR = ROOT / "output" / "pose_personaggio"
CFG_CORSO = json.loads((CORSO / "course.json").read_text()) if (CORSO / "course.json").exists() else {}   # pose ritagliate, comuni a tutti i corsi
W, H, FPS = 1920, 1080, 25
LEAD, TAIL = 0.6, 0.9
WALK = 1.8              # secondi di camminata al cambio di lato
CHAR_H = 860            # altezza del personaggio in pixel
FEET_Y = 1058
EMU_W, EMU_H = 12191695, 6858000

# Regia "tutto schermo" (richiesta di Diego, 16/11/2026): la slide si ingrandisce a tutto schermo,
# l'avatar esce di lato, le parti spiegate vengono evidenziate (riquadri, cerchi, sottolineature), poi si torna.
REGIA_TUTTO_SCHERMO = os.environ.get("REGIA", "tutto_schermo") == "tutto_schermo"
FONT_BOLD = "/usr/share/fonts/truetype/open-sans/OpenSans-Bold.ttf"
ROSSO, VERDE, AMBRA = (214, 48, 39), (46, 150, 70), (181, 105, 0)

EMOJI = re.compile("[\U0001F000-\U0001FAFF☀-➿️‍⏰-⏿⬀-⯿]")


def clean_tts(t: str) -> str:
    t = EMOJI.sub("", t).replace("«", "").replace("»", "").replace("＋", "più ")
    return re.sub(r"\s+", " ", t).strip()


def clean_sub(t: str) -> str:
    t = EMOJI.sub("", t).replace("＋", "+")
    t = re.sub(r"«\s+", "«", t)
    return re.sub(r"\s+", " ", t).strip()


# --------------------------------------------------------------------------
# Lettura del pacchetto
# --------------------------------------------------------------------------
def storyboard():
    import openpyxl
    ws = openpyxl.load_workbook(MAT / "Storyboard_Animazione.xlsx", data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    hdr = rows[0]
    return [dict(zip(hdr, r)) for r in rows[1:] if isinstance(r[0], int)]


def slide_geometry():
    """Per ogni slide: rettangolo della figura principale e gruppi di evidenziazione (in pixel)."""
    import pptx
    p = pptx.Presentation(next(MAT.glob("Slide_*.pptx")))
    sx, sy = W / p.slide_width, H / p.slide_height
    geo = []
    for s in p.slides:
        box = lambda sh: (sh.left * sx, sh.top * sy, (sh.left + sh.width) * sx, (sh.top + sh.height) * sy)
        pic = next((box(sh) for sh in s.shapes if sh.shape_type == 13), None)
        ev, num, arrows = {}, {}, []
        for sh in s.shapes:
            m = re.match(r"(Evidenza|Numero) (\d+)$", sh.name)
            if m:
                (ev if m.group(1) == "Evidenza" else num)[int(m.group(2))] = box(sh)
            elif sh.name.startswith("Freccia"):
                arrows.append(box(sh))
        groups = {k: [v] for k, v in ev.items()}
        for k, v in num.items():
            groups.setdefault(k, []).append(v)
        for a in arrows:  # la freccia va con l'evidenza più vicina
            if groups:
                c = ((a[0] + a[2]) / 2, (a[1] + a[3]) / 2)
                k = min(groups, key=lambda g: math.dist(c, ((groups[g][0][0] + groups[g][0][2]) / 2, (groups[g][0][1] + groups[g][0][3]) / 2)))
                groups[k].append(a)
        side = "destra"
        for sh in s.shapes:
            if sh.name == "Spazio per il personaggio":
                side = "sinistra" if sh.left < p.slide_width * 0.2 else "destra"
        geo.append({"pic": pic, "groups": [groups[k] for k in sorted(groups)], "side": side})
    return geo


# --------------------------------------------------------------------------
# Preparazione: maschere delle evidenziazioni e pose ritagliate
# --------------------------------------------------------------------------
def slide_png():
    """Slide -> PNG 1920x1080 in due versioni: 'base' (senza evidenziazioni) e 'full'."""
    import pptx
    SLIDE_DIR.mkdir(parents=True, exist_ok=True)
    src = next(MAT.glob("Slide_*.pptx"))
    is_hl = lambda n: n.startswith(("Evidenza", "Numero ", "Freccia")) and n != "Numero della slide"
    for mode in ("base", "full"):
        if (SLIDE_DIR / mode).exists() and any((SLIDE_DIR / mode).glob("s-*.png")):
            continue
        p = pptx.Presentation(src)
        for sl in p.slides:
            for sh in list(sl.shapes):
                if sh.name.startswith("Etichetta dello spazio") or (mode == "base" and is_hl(sh.name)):
                    sh._element.getparent().remove(sh._element)
        p.save(SLIDE_DIR / f"{mode}.pptx")
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(SLIDE_DIR), str(SLIDE_DIR / f"{mode}.pptx")],
                       check=True, capture_output=True, timeout=600)
        (SLIDE_DIR / mode).mkdir(exist_ok=True)
        subprocess.run(["pdftoppm", "-r", "144", "-scale-to-x", str(W), "-scale-to-y", str(H), "-png",
                        str(SLIDE_DIR / f"{mode}.pdf"), str(SLIDE_DIR / mode / "s")], check=True)
        for f in (SLIDE_DIR / mode).glob("s-*.png"):  # pdftoppm non mette lo zero sotto le 10 pagine
            n = int(f.stem[2:])
            if f.name != f"s-{n:02d}.png":
                f.rename(f.with_name(f"s-{n:02d}.png"))


def prepara():
    slide_png()
    geo = slide_geometry()
    (OUT / "geometria.json").write_text(json.dumps(geo, indent=1))
    mdir = SLIDE_DIR / "maschere"
    mdir.mkdir(parents=True, exist_ok=True)
    for i, g in enumerate(geo, 1):
        base = np.asarray(Image.open(SLIDE_DIR / "base" / f"s-{i:02d}.png").convert("RGB")).astype(np.int16)
        full = np.asarray(Image.open(SLIDE_DIR / "full" / f"s-{i:02d}.png").convert("RGB")).astype(np.int16)
        diff = (np.abs(full - base).max(axis=2) > 10)
        if not g["groups"]:
            continue
        # ogni pixel diverso va al riquadro più piccolo che lo contiene (con margine)
        owner = np.full(diff.shape, -1, np.int16)
        best_area = np.full(diff.shape, np.inf)
        for gi, shapes in enumerate(g["groups"]):
            for (x0, y0, x1, y1) in shapes:
                pad = 7
                xa, ya, xb, yb = max(0, int(x0 - pad)), max(0, int(y0 - pad)), min(W, int(x1 + pad)), min(H, int(y1 + pad))
                area = (xb - xa) * (yb - ya)
                sub = best_area[ya:yb, xa:xb]
                upd = area < sub
                sub[upd] = area
                owner[ya:yb, xa:xb][upd] = gi
        for gi in range(len(g["groups"])):
            m = Image.fromarray(((owner == gi) & diff).astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
            m.save(mdir / f"s-{i:02d}-g{gi}.png")
    # pose: ritaglio del personaggio e scala unica
    for clip in sorted(CLIPS.glob("*.webm")):
        d = POSE_DIR / clip.stem
        if d.exists() and any(d.iterdir()):
            continue
        d.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", str(clip), "-vf", "fps=25",
                        str(d / "f%04d.png")], check=True)
        frames = sorted(d.glob("f*.png"))
        bb = None
        for f in frames[::5]:
            b = Image.open(f).getchannel("A").point(lambda v: 255 if v > 40 else 0).getbbox()
            if b:
                bb = b if bb is None else (min(bb[0], b[0]), min(bb[1], b[1]), max(bb[2], b[2]), max(bb[3], b[3]))
        x0, y0, x1, y1 = bb
        x0, x1 = max(0, x0 - 20), x1 + 20
        y0 = max(0, y0 - 10)
        meta = {"bbox": [x0, y0, x1, y1]}
        (d / "meta.json").write_text(json.dumps(meta))
    # scala comune: altezza del personaggio in "parla"
    ref = json.loads((POSE_DIR / "parla" / "meta.json").read_text())["bbox"]
    scale = CHAR_H / (ref[3] - ref[1])
    for d in POSE_DIR.iterdir():
        meta = json.loads((d / "meta.json").read_text())
        if meta.get("scale") == scale:
            continue
        x0, y0, x1, y1 = meta["bbox"]
        for f in sorted(d.glob("f*.png")):
            im = Image.open(f).crop((x0, y0, x1, y1))
            im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
            im.save(d / ("c" + f.name[1:]))
            f.unlink()
        # piedi: ultima riga con alfa nella posa ferma, per appoggiare tutti allo stesso suolo
        a = np.asarray(Image.open(sorted(d.glob("c*.png"))[0]).getchannel("A"))
        rows = np.nonzero(a.max(axis=1) > 60)[0]
        meta.update({"scale": scale, "feet": int(rows.max()), "n": len(list(d.glob("c*.png")))})
        (d / "meta.json").write_text(json.dumps(meta))
    print("preparazione completata")


# --------------------------------------------------------------------------
# Voce
# --------------------------------------------------------------------------
def voce():
    cfg = json.loads((CORSO / "course.json").read_text())
    vdir = OUT / "voce"
    vdir.mkdir(parents=True, exist_ok=True)
    log = (OUT / "ledger.jsonl").open("a")
    for s in storyboard():
        n = s["Scena"]
        txt = clean_tts(s["Testo pronunciato"])
        for sigla, voce_ in cfg.get("pronuncia", {}).items():   # es. SdI -> "esse di i" (solo nella voce)
            txt = re.sub(rf"\b{re.escape(sigla)}\b", voce_, txt)
        wav = vdir / f"{n:02d}.wav"
        tag = vdir / f"{n:02d}.tag"
        key = f"{cfg['elevenlabs_voice_id']}:{cfg['elevenlabs_model']}:{hashlib.sha1(txt.encode()).hexdigest()[:12]}"
        if wav.exists() and tag.exists() and tag.read_text() == key:
            continue
        body = {"text": txt, "model_id": cfg["elevenlabs_model"], "voice_settings": cfg["elevenlabs_voice_settings"]}
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{cfg['elevenlabs_voice_id']}?output_format=mp3_44100_192",
            data=json.dumps(body).encode(), method="POST",
            headers={"xi-api-key": os.environ.get("ELEVENLABS_API_KEY", "proxy-injected"), "Content-Type": "application/json", "Accept": "audio/mpeg"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=180) as r:
                    (vdir / f"{n:02d}.mp3").write_bytes(r.read())
                break
            except urllib.error.HTTPError as e:
                err = f"{e.code} {e.read()[:200]!r}"
                if attempt == 2:
                    log.write(json.dumps({"stage": "voce", "scena": n, "status": "error", "error": err}) + "\n")
                    raise
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(vdir / f"{n:02d}.mp3"), "-ar", "48000", "-ac", "1", str(wav)], check=True)
        tag.write_text(key)
        log.write(json.dumps({"stage": "voce", "scena": n, "service": "elevenlabs (abbonamento)", "chars": len(txt), "status": "ok"}) + "\n")
        print("voce scena", n)


# --------------------------------------------------------------------------
# Timeline
# --------------------------------------------------------------------------
GESTI = [
    ("saluta", r"\bsaluta"),
    ("telefono", r"telefono"),
    ("conta", r"\bconta|dita|alza un dito|un dito|tre dita"),
    ("pollice", r"pollice in su|pollice\b"),
    ("attenzione", r"seri[oa]|scuote|avvertimento|attenzion|alza l.indice|fermarsi|batte l.indice"),
    ("indica", r"indica|punta|preme|tocca|segue con il braccio|scorre|mostra|mima|pesa|scatta|scrive"),
]


def gesti(mov: str):
    mov = mov.lower()
    found = []
    for name, rx in GESTI:
        m = re.search(rx, mov)
        if m:
            found.append((m.start(), name))
    out = [n for _, n in sorted(found)]
    seq = []
    for g in out:
        if g not in seq:
            seq.append(g)
    return seq[:3] or ["indica"]


SECONDARIA = re.compile(r"\((pc-\d+[^)]*|tel-\d+[^)]*)\)")


def timeline():
    sb = storyboard()
    geo = json.loads((OUT / "geometria.json").read_text())
    tl, t = [], 0.0
    prev_side = None
    for s in sb:
        n = s["Scena"]
        vd = ffprobe_duration(OUT / "voce" / f"{n:02d}.wav")
        fname = str(s.get("Schermata o schema (file)") or "")
        clip = fname[5:] if fname.startswith("clip:") else None
        side = "" if clip else (s["Lato del personaggio"] or geo[n - 1]["side"]).strip().lower()
        walk = 0.0 if clip else (WALK if (prev_side is None or side != prev_side) else 0.0)
        sec = None
        for col in ("Elementi da evidenziare", "Zoom e transizioni"):
            testo = s.get(col) or ""
            m = SECONDARIA.findall(testo)
            if m:  # l'ultima citata è quella che entra a metà o a fine scena (prima può esserci quella d'apertura)
                sec = m[-1].strip()
                nude = re.findall(r"\b((?:pc|tel)-\d+[\w-]*)", testo)  # anche scritta senza parentesi («transizione a pc-16-…»)
                if nude and nude[-1] not in sec:
                    sec = nude[-1]
        # pause per mostrare le operazioni: più evidenziazioni o una seconda schermata = più tempo
        extra = min(2.5, 0.5 * len(geo[n - 1]["groups"])) + (1.2 if sec else 0.0)
        dur = round(max(LEAD + vd + TAIL + extra, walk + 3.0), 3)
        mov = s["Movimento del personaggio"] or ""
        tl.append({"n": n, "cap": int(str(s["Capitolo"]).split("—")[0].strip()), "cap_titolo": str(s["Capitolo"]),
                   "titolo": s["Titolo della slide"], "t0": round(t, 3), "dur": dur, "speech_t0": round(t + LEAD, 3),
                   "speech_dur": round(vd, 3), "text": clean_sub(s["Testo pronunciato"]), "side": side,
                   "prev_side": prev_side, "walk": walk, "gesti": gesti(mov), "mov": mov,
                   "zoom": "zoom" in (s["Zoom e transizioni"] or "").lower() and n not in CFG_CORSO.get("scene_senza_zoom", []), "secondaria": sec,
                   "file": s.get("Schermata o schema (file)"), "clip": clip,
                   "senza_zoom": n in CFG_CORSO.get("scene_senza_zoom", []),
                   "avviso": bool(re.search(r"errore|avviso|allarme|rosso|impedisce", (s["Elementi da evidenziare"] or "") + " " + (s["Zoom e transizioni"] or ""), re.I)),
                   "geo": geo[n - 1]})
        prev_side = side or None   # dopo una scena 3D il personaggio rientra camminando
        t += dur
    (OUT / "timeline.json").write_text(json.dumps(tl, indent=1, ensure_ascii=False))
    return tl


# --------------------------------------------------------------------------
# Personaggio
# --------------------------------------------------------------------------
@lru_cache(maxsize=4096)
def pose_frame(pose: str, idx: int, flip: bool):
    meta = pose_meta(pose)
    idx = max(0, min(meta["n"] - 1, idx))
    im = Image.open(POSE_DIR / pose / f"c{idx + 1:04d}.png").convert("RGBA")
    return im.transpose(Image.FLIP_LEFT_RIGHT) if flip else im


@lru_cache(maxsize=16)
def pose_meta(pose):
    return json.loads((POSE_DIR / pose / "meta.json").read_text())


def side_x(side):
    return int(W * (0.85 if side == "destra" else 0.15))


def fasi(sc):
    """Fase tutto schermo della scena: (inizio_ingresso, inizio_uscita) o None."""
    if not REGIA_TUTTO_SCHERMO or not sc["geo"]["pic"] or sc.get("clip") or sc.get("senza_zoom"):
        return None
    D = sc["dur"]
    a = max(sc["walk"], LEAD) + 1.2
    b = LEAD + sc["speech_dur"] * 0.80
    sec = sc.get("secondaria")
    if sec:  # la schermata secondaria arriva a vista normale
        b = min(b, LEAD + sc["speech_dur"] * 0.62 - 0.9)
    b = min(b, D - 2.6)
    return (a, b) if b - a >= 3.5 else None


def char_plan(sc, is_last):
    if sc.get("clip"):
        return []
    f = fasi(sc)
    if f:
        return char_plan_regia(sc, is_last, f)
    return char_plan_base(sc, is_last)


def char_plan_regia(sc, is_last, f):
    """Avatar presente prima e dopo il tutto schermo: un gesto per parte."""
    D = sc["dur"]; x = side_x(sc["side"]); a, b = f
    segs, t = [], 0.0
    if sc["walk"] > 0:
        x_from = W + 260 if sc["prev_side"] is None else side_x(sc["prev_side"])
        segs.append((0.0, sc["walk"], "cammina", x < x_from, x_from, x)); t = sc["walk"]
    g = list(sc["gesti"])
    first = g[0] if g else "indica"
    flip = lambda name: (name == "indica" and sc["side"] == "destra") or (name == "telefono" and sc["side"] == "sinistra")
    segs.append((t, b, first, flip(first), x, x))          # durante il tutto schermo l'avatar non si vede
    tail_walk = 2.2 if is_last else 0.0
    second = g[-1] if len(g) > 1 else ("pollice" if "pollice" in g else "parla")
    end_g = min(D - tail_walk, b + 0.7 + 5.0)
    segs.append((b, end_g, second, flip(second), x, x))
    if end_g < D - tail_walk:
        segs.append((end_g, D - tail_walk, "parla", False, x, x))
    if tail_walk:
        segs.append((D - tail_walk, D, "cammina", True, x, -300))
    return segs


def char_plan_base(sc, is_last):
    """Segmenti (inizio, fine, posa, specchiata, x0, x1) relativi alla scena."""
    D = sc["dur"]
    x = side_x(sc["side"])
    segs, t = [], 0.0
    if sc["walk"] > 0:
        x_from = W + 260 if sc["prev_side"] is None else side_x(sc["prev_side"])
        segs.append((0.0, sc["walk"], "cammina", x < x_from, x_from, x))
        t = sc["walk"]
    g = list(sc["gesti"])
    tail_walk = 2.2 if is_last else 0.0
    avail = D - t - tail_walk
    gesture_len = 5.0
    while g and len(g) * (gesture_len + 0.6) > avail + 0.6:
        g.pop()
    if not g and avail > 2.5:
        g = [sc["gesti"][0]]
        gesture_len = max(2.0, min(5.0, avail - 0.4))
    slot = avail / max(1, len(g))
    for gi, name in enumerate(g):
        s0 = t + gi * slot
        talk_before = min(0.6, max(0.0, slot - gesture_len)) if gi else 0.0
        if talk_before:
            segs.append((s0, s0 + talk_before, "parla", False, x, x))
        gs = s0 + talk_before
        ge = min(gs + gesture_len, s0 + slot)
        # indica punta verso destra del fotogramma: se il personaggio è a destra, la schermata è a sinistra -> specchio
        flip = (name == "indica" and sc["side"] == "destra") or (name == "telefono" and sc["side"] == "sinistra")
        segs.append((gs, ge, name, flip, x, x))
        if ge < s0 + slot:
            segs.append((ge, s0 + slot, "parla", False, x, x))
    if tail_walk:
        segs.append((D - tail_walk, D, "cammina", True, x, -300))
    if not segs or segs[-1][1] < D - 1e-3:
        segs.append((segs[-1][1] if segs else 0.0, D, "parla", False, x, x))
    # tratti lunghi di sola "parla": ogni ~10 s torna a indicare la schermata
    out = []
    for seg in segs:
        s0, s1, pose, flip, xa, xb = seg
        while pose == "parla" and s1 - s0 > 12.0:
            out.append((s0, s0 + 4.5, "parla", False, xa, xa))
            out.append((s0 + 4.5, s0 + 9.5, "indica", sc["side"] == "destra", xa, xa))
            s0 += 9.5
        out.append((s0, s1, pose, flip, xa, xb))
    return out


def pose_index(pose, local_t, seg_len):
    n = pose_meta(pose)["n"]
    f = int(local_t * FPS)
    if pose in ("parla", "cammina"):  # ciclo avanti-indietro senza salti
        period = 2 * (n - 1)
        f %= period
        return f if f < n else period - f
    return min(f, n - 1)


def draw_character(frame, sc, segs, t):
    if not segs:
        return
    def render_seg(seg, alpha=1.0):
        s0, s1, pose, flip, xa, xb = seg
        k = (t - s0) / max(1e-6, s1 - s0)
        x = xa + (xb - xa) * min(1, max(0, k))
        im = pose_frame(pose, pose_index(pose, t - s0, s1 - s0), flip)
        if alpha < 1:
            im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
        feet = pose_meta(pose)["feet"]
        frame.alpha_composite(im, (int(x - im.width / 2), int(FEET_Y - feet)))
    cur = next((s for s in segs if s[0] <= t < s[1]), segs[-1])
    i = segs.index(cur)
    xf = 0.2  # dissolvenza incrociata tra pose
    if i > 0 and t - cur[0] < xf and segs[i - 1][2] != cur[2]:
        a = (t - cur[0]) / xf
        prev = segs[i - 1]
        render_seg((prev[0], prev[1] + xf, prev[2], prev[3], prev[5], prev[5]), 1 - a)
        render_seg(cur, a)
    else:
        render_seg(cur)


# --------------------------------------------------------------------------
# Slide, evidenziazioni, zoom, schermate secondarie
# --------------------------------------------------------------------------
@lru_cache(maxsize=8)
def slide_img(n, kind):
    return Image.open(SLIDE_DIR / kind / f"s-{n:02d}.png").convert("RGB")


@lru_cache(maxsize=64)
def mask_img(n, gi):
    return Image.open(SLIDE_DIR / "maschere" / f"s-{n:02d}-g{gi}.png").convert("L")


def find_shot(name):
    for d in (MAT / "Screenshot_App", MAT / "Asset_Grafici"):
        for f in d.glob(name + "*.png"):
            return f
    return None


@lru_cache(maxsize=8)
def secondary_layer(n, name, pic, side="destra"):
    """Immagine della slide con la schermata secondaria al posto di quella principale (pc) o card telefono."""
    f = find_shot(name)
    base = slide_img(n, "base").copy()
    shot = Image.open(f).convert("RGB")
    if name.startswith("pc-") and pic:
        x0, y0, x1, y1 = [int(v) for v in pic]
        if (y1 - y0) > (x1 - x0):
            # slide del telefono -> "transizione alla scheda sul computer": la schermata occupa i due terzi liberi
            # i due terzi liberi sono dalla parte opposta al personaggio
            x0, x1 = (int(W * 0.33), int(W * 0.97)) if side == "sinistra" else (int(W * 0.03), int(W * 0.67))
            y0, y1 = int(H * 0.20), int(H * 0.93)
            bgc = base.getpixel((x0 + 5, int(H * 0.97)))
            ImageDraw.Draw(base).rectangle([x0 - 10, int(H * 0.18), x1 + 10, H], fill=bgc)
        bw, bh = x1 - x0, y1 - y0
        s = min(bw / shot.width, bh / shot.height)
        sh = shot.resize((int(shot.width * s), int(shot.height * s)), Image.LANCZOS)
        d = ImageDraw.Draw(base)
        d.rectangle([x0, y0, x1, y1], fill=(255, 255, 255))
        base.paste(sh, (x0 + (bw - sh.width) // 2, y0 + (bh - sh.height) // 2))
        d.rectangle([x0 - 3, y0 - 3, x1 + 3, y1 + 3], outline=(181, 105, 0), width=4)
    return base


def phone_card(name, height=520):
    shot = Image.open(find_shot(name)).convert("RGB")
    s = (height - 28) / shot.height
    sh = shot.resize((int(shot.width * s), int(shot.height * s)), Image.LANCZOS)
    card = Image.new("RGBA", (sh.width + 28, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([0, 0, card.width - 1, height - 1], radius=36, fill=(25, 25, 28, 255))
    m = Image.new("L", sh.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, sh.width - 1, sh.height - 1], radius=24, fill=255)
    card.paste(sh, (14, 14), m)
    sha = Image.new("RGBA", (card.width + 40, card.height + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sha).rounded_rectangle([20, 26, card.width + 20, card.height + 26], radius=36, fill=(0, 0, 0, 90))
    sha = sha.filter(ImageFilter.GaussianBlur(10))
    sha.alpha_composite(card, (20, 20))
    return sha


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


@lru_cache(maxsize=8)
def clip_meta(name):
    d = OUT / "clip_frames" / name
    return len(list(d.glob("f*.jpg"))) if d.exists() else 0


def clip_frame(name, idx):
    return Image.open(OUT / "clip_frames" / name / f"f{idx + 1:04d}.jpg").convert("RGB")


def scene_frame_clip(sc, t, is_first, is_last_ch):
    """Scena 3D generata (apertura/chiusura). Se la clip non c'è ancora: slide segnaposto."""
    D = sc["dur"]
    nf = clip_meta(sc["clip"])
    if nf:
        stretch = min(1.5, max(1.0, D * FPS / nf))      # rallenta fino a 1,5x, poi tiene l'ultimo fotogramma
        fr = clip_frame(sc["clip"], min(nf - 1, int(t * FPS / stretch)))
    else:
        fr = slide_img(sc["n"], "base")
    fr = fr.convert("RGBA")
    if sc["clip"].endswith("apertura"):   # titolo dell'episodio in basso a sinistra
        k = ease((t - 0.6) / 0.5) - ease((t - 5.5) / 0.6)
        if k > 0:
            from PIL import ImageFont
            f1, f2 = ImageFont.truetype(FONT_BOLD, 46), ImageFont.truetype(FONT_BOLD, 28)
            ep = sc["cap_titolo"].split("—")[0].strip()
            t1, t2 = str(sc["cap_titolo"].split("—", 1)[1]).strip(), f"Corso Pompe di calore · Episodio {ep}"
            w = int(max(f1.getlength(t1), f2.getlength(t2))) + 80
            band = Image.new("RGBA", (w, 150), (0, 0, 0, 0))
            d = ImageDraw.Draw(band)
            d.rounded_rectangle([0, 0, w - 1, 149], radius=18, fill=(251, 248, 241, 235))
            d.rectangle([0, 14, 9, 135], fill=AMBRA + (255,))
            d.text((34, 46), t2, font=f2, fill=(122, 106, 82), anchor="lm")
            d.text((34, 100), t1, font=f1, fill=(150, 82, 0), anchor="lm")
            if k < 1:
                band.putalpha(band.getchannel("A").point(lambda x, f=k: int(x * f)))
            fr.alpha_composite(band, (60, H - 210))
    out = fr.convert("RGB")
    fade = 1.0
    if is_first:
        fade = min(fade, t / 0.5)
    if is_last_ch:
        fade = min(fade, (D - t) / 0.8)
    if fade < 1:
        out = Image.blend(Image.new("RGB", (W, H)), out, max(0.0, fade))
    return out


def estrai_clip():
    """Fotogrammi delle clip 3D (output/<corso>/clips/<nome>.mp4) in JPG 1920x1080."""
    for f in sorted((OUT / "clips").glob("*.mp4")):
        d = OUT / "clip_frames" / f.stem
        if d.exists() and any(d.glob("f*.jpg")):
            continue
        d.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
                        "-q:v", "3", str(d / "f%04d.jpg")], check=True)
        print("clip", f.stem)


def scene_frame(sc, t, segs, is_first_of_chapter, is_last_of_chapter, is_last):
    if sc.get("clip"):
        return scene_frame_clip(sc, t, is_first_of_chapter, is_last_of_chapter)
    n = sc["n"]
    geo = sc["geo"]
    groups = geo["groups"]
    ng = len(groups)
    D = sc["dur"]
    sp0 = LEAD
    # tempi delle evidenziazioni: distribuite sul parlato
    times = [sp0 + sc["speech_dur"] * (0.12 + 0.6 * (i / max(1, ng - 1) if ng > 1 else 0.1)) for i in range(ng)]
    sec = sc.get("secondaria")
    sec_t = sp0 + sc["speech_dur"] * (0.62 if sec else 9)
    img = slide_img(n, "base")
    if sec and sec.startswith("pc-") and t >= sec_t:
        k = ease((t - sec_t) / 0.5)
        lay = secondary_layer(n, sec, tuple(geo["pic"]) if geo["pic"] else None, sc["side"])
        img = Image.blend(img, lay, k) if k < 1 else lay
        show_hl = t < sec_t + 0.5
    else:
        show_hl = True
    f = fasi(sc)
    if f:
        return scene_frame_regia(sc, t, segs, f, img, is_first_of_chapter, is_last_of_chapter,
                                 hl=not (sec and sec.startswith("pc-") and t >= sec_t))
    if ng and show_hl:
        img = img.copy()
        full = slide_img(n, "full")
        for gi, tg in enumerate(times):
            if t >= tg:
                a = ease((t - tg) / 0.35)
                if sec and t >= sec_t:
                    a *= 1 - ease((t - sec_t) / 0.5)
                pulse = 1.0 if t - tg > 1.2 else 0.75 + 0.25 * math.cos((t - tg) * 10)
                m = mask_img(n, gi)
                if a * pulse < 0.999:
                    m = m.point(lambda v, f=a * pulse: int(v * f))
                img.paste(full, (0, 0), m)
    # zoom lento sulla zona evidenziata
    if sc["zoom"] and ng:
        xs = [(b[0] + b[2]) / 2 for gr in groups for b in gr]
        ys = [(b[1] + b[3]) / 2 for gr in groups for b in gr]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        cx, cy = (cx + W / 2) / 2, (cy + H * 0.55) / 2   # zoom moderato, senza tagliare il titolo
        z = 1 + 0.09 * ease((t - times[0]) / 2.0) - 0.09 * ease((t - (D - 1.2)) / 1.0)
        if z > 1.001:
            w, h = W / z, H / z
            x0 = min(max(cx - w / 2, 0), W - w)
            y0 = 0  # lo zoom parte dal bordo alto: il titolo della slide resta sempre intero
            img = img.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.BILINEAR)
    frame = img.convert("RGBA")
    # schermata del telefono che entra accanto (es. scena 3)
    if sec and sec.startswith("tel-") and t >= sec_t:
        k = ease((t - sec_t) / 0.5)
        dx = 0
        for nome in [x.strip() for x in sec.split(",") if x.strip()]:
            card = phone_card(nome)
            x = int((W * 0.70 - card.width - dx) if sc["side"] == "destra" else (W * 0.30 + dx))
            y = int(H - card.height - 40 + (1 - k) * 200)
            if k < 1:
                card = card.copy(); card.putalpha(card.getchannel("A").point(lambda v: int(v * k)))
            frame.alpha_composite(card, (x, y))
            dx += card.width + 24
    draw_character(frame, sc, segs, t)
    fr = frame.convert("RGB")
    fade = 1.0
    if is_first_of_chapter:
        fade = min(fade, t / 0.5)
    if is_last_of_chapter:
        fade = min(fade, (D - t) / 0.6)
    if fade < 1:
        fr = Image.blend(Image.new("RGB", (W, H)), fr, max(0.0, fade))
    return fr


# --------------------------------------------------------------------------
# Regia "tutto schermo"
# --------------------------------------------------------------------------
@lru_cache(maxsize=1)
def evidenze_json():
    f = MAT / "Asset_Grafici" / "evidenze.json"
    return json.loads(f.read_text()) if f.exists() else {}


def target_rect(pic):
    """Rettangolo della slide da portare a tutto schermo (16:9 attorno alla schermata/schema)."""
    x0, y0, x1, y1 = pic
    pad = W * 0.012
    x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    w, h = x1 - x0, y1 - y0
    if w / h < W / H:
        w2 = h * W / H; cx = (x0 + x1) / 2; x0, x1 = cx - w2 / 2, cx + w2 / 2
    else:
        h2 = w * H / W; cy = (y0 + y1) / 2; y0, y1 = cy - h2 / 2, cy + h2 / 2
    # dentro la slide
    dx = max(0, -x0) - max(0, x1 - W); dy = max(0, -y0) - max(0, y1 - H)
    x0, x1, y0, y1 = x0 + dx, x1 + dx, y0 + dy, y1 + dy
    if x1 - x0 > W or y1 - y0 > H:
        return (0, 0, W, H)
    return (x0, y0, x1, y1)


def marcatori(sc):
    """Riquadri da evidenziare (coordinate della slide), nell'ordine della spiegazione."""
    geo = sc["geo"]
    boxes = []
    for gr in geo["groups"]:
        b = gr[0]   # il primo è l'«Evidenza» (o il numero se c'è solo quello)
        boxes.append(b)
    if not boxes and geo["pic"]:
        name = Path(str(sc.get("file") or "")).stem
        ev = evidenze_json().get(name, {}).get("evidenze", [])
        x0, y0, x1, y1 = geo["pic"]
        for e in ev[:6]:
            boxes.append((x0 + e["x"] * (x1 - x0), y0 + e["y"] * (y1 - y0), x0 + (e["x"] + e["w"]) * (x1 - x0), y0 + (e["y"] + e["h"]) * (y1 - y0)))
    return boxes


def lerp(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


@lru_cache(maxsize=64)
def title_band(text, width=None):
    from PIL import ImageFont
    f = ImageFont.truetype(FONT_BOLD, 38)
    tw = int(f.getlength(text))
    band = Image.new("RGBA", (tw + 70, 74), (0, 0, 0, 0))
    d = ImageDraw.Draw(band)
    d.rounded_rectangle([0, 0, band.width - 1, 73], radius=16, fill=(251, 248, 241, 235))
    d.rectangle([0, 10, 8, 63], fill=AMBRA + (255,))
    d.text((30, 37), text, font=f, fill=(150, 82, 0), anchor="lm")
    return band


def draw_marker(ov, box, k, color, current):
    """Disegna un evidenziatore che si 'traccia' (k = 0..1): sottolineatura, cerchio o riquadro."""
    d = ImageDraw.Draw(ov)
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    alpha = 255 if current else 150
    col = color + (alpha,)
    lw = 7 if current else 5
    if w / max(h, 1) > 6:                        # riga lunga e bassa: sottolineatura
        yy = y1 + 8
        d.line([(x0, yy), (x0 + w * k, yy)], fill=col, width=lw + 2)
    elif w < W * 0.10 and h < H * 0.12:          # elemento piccolo: cerchio
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        rx, ry = w / 2 + 26, h / 2 + 22
        d.arc([cx - rx, cy - ry, cx + rx, cy + ry], start=-90, end=-90 + 360 * k, fill=col, width=lw)
    else:                                        # riquadro che si disegna lungo il perimetro
        m = 10
        pts = [(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m), (x0 - m, y0 - m)]
        per = 2 * (w + h + 4 * m); L = per * k
        for p0, p1 in zip(pts, pts[1:]):
            seg = math.dist(p0, p1)
            if L <= 0:
                break
            q = min(1, L / seg)
            d.line([p0, (p0[0] + (p1[0] - p0[0]) * q, p0[1] + (p1[1] - p0[1]) * q)], fill=col, width=lw)
            L -= seg


def scene_frame_regia(sc, t, segs, f, img, is_first, is_last_ch, hl=True):
    n, D = sc["n"], sc["dur"]
    a, b = f
    TR = 0.75
    v = ease((t - a) / TR) * (1 - ease((t - b) / TR))      # 0 = vista normale, 1 = tutto schermo
    groups = sc["geo"]["groups"]
    # dopo il ritorno: compaiono anche le evidenziazioni disegnate nella slide
    if groups and t > b and hl:  # non sopra la schermata secondaria del computer
        img = img.copy()
        full = slide_img(n, "full")
        k = ease((t - b - 0.3) / 0.5)
        for gi in range(len(groups)):
            m = mask_img(n, gi)
            img.paste(full, (0, 0), m if k >= 1 else m.point(lambda x, kk=k: int(x * kk)))
    rect = target_rect(sc["geo"]["pic"])
    R = lerp((0, 0, W, H), rect, v)
    if v > 0.001:
        img = img.crop(tuple(int(x) for x in R)).resize((W, H), Image.BICUBIC if v > 0.98 else Image.BILINEAR)
    frame = img.convert("RGBA")
    sx, sy = W / (R[2] - R[0]), H / (R[3] - R[1])
    to_scr = lambda bx: ((bx[0] - R[0]) * sx, (bx[1] - R[1]) * sy, (bx[2] - R[0]) * sx, (bx[3] - R[1]) * sy)
    pic = sc["geo"]["pic"]
    if v > 0.01 and (pic[3] - pic[1]) > (pic[2] - pic[0]):
        # telefono a tutto schermo: intorno solo sfondo, niente testo della slide tagliato a metà
        bgc = slide_img(n, "base").getpixel((int(W * 0.5), int(H * 0.985)))
        cover = Image.new("RGBA", (W, H), tuple(bgc[:3]) + (int(255 * v),))
        px = to_scr(pic)
        ImageDraw.Draw(cover).rounded_rectangle([px[0] - 30, px[1] - 30, px[2] + 30, px[3] + 30], radius=40, fill=(0, 0, 0, 0))
        frame.alpha_composite(cover)
    # evidenziatori durante il tutto schermo
    boxes = marcatori(sc)
    if boxes and v > 0.95:
        t0, t1 = a + TR + 0.4, b - 0.9
        times = [t0 + (t1 - t0) * (i / max(1, len(boxes) - 1) if len(boxes) > 1 else 0.0) for i in range(len(boxes))]
        shown = [i for i, ti in enumerate(times) if t >= ti]
        if shown:
            cur = shown[-1]
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            # luce sulla parte spiegata: il resto si scurisce leggermente
            sb = to_scr(boxes[cur])
            dim = Image.new("RGBA", (W, H), (20, 16, 10, 70))
            ImageDraw.Draw(dim).rounded_rectangle([sb[0] - 18, sb[1] - 18, sb[2] + 18, sb[3] + 18], radius=14, fill=(0, 0, 0, 0))
            k_dim = ease((t - times[cur]) / 0.4)
            frame.alpha_composite(dim if k_dim >= 1 else Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 0)), dim, k_dim))
            for i in shown:
                color = ROSSO
                if sc["avviso"]:
                    color = ROSSO
                elif "pollice" in sc["gesti"] and i == len(boxes) - 1:
                    color = VERDE
                draw_marker(ov, to_scr(boxes[i]), ease((t - times[i]) / 0.6), color, i == cur)
            frame.alpha_composite(ov)
    vb = max(0.0, (v - 0.85) / 0.15)   # titolo solo a tutto schermo (durante il movimento si vede quello della slide)
    if vb > 0:
        band = title_band(clean_sub(str(sc["titolo"])).strip())
        if vb < 1:
            band = band.copy(); band.putalpha(band.getchannel("A").point(lambda x, f=vb: int(x * f)))
        frame.alpha_composite(band, (40, 28))
    # telefono secondario accanto all'avatar (vista normale)
    sec = sc.get("secondaria")
    sec_t = LEAD + sc["speech_dur"] * 0.62
    if sec and sec.startswith("tel-") and t >= max(sec_t, b + TR):
        k = ease((t - max(sec_t, b + TR)) / 0.5)
        dx = 0
        for nome in [x.strip() for x in sec.split(",") if x.strip()]:  # anche più telefoni affiancati
            card = phone_card(nome)
            x = int((W * 0.70 - card.width - dx) if sc["side"] == "destra" else (W * 0.30 + dx))
            y = int(H - card.height - 40 + (1 - k) * 200)
            if k < 1:
                card = card.copy(); card.putalpha(card.getchannel("A").point(lambda v: int(v * k)))
            frame.alpha_composite(card, (x, y))
            dx += card.width + 24
    # avatar: esce di lato mentre la slide si ingrandisce, rientra al ritorno
    if v < 0.98:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw_character(layer, sc, segs, t)
        if v > 0:
            off = int(v * 650) * (1 if sc["side"] == "destra" else -1)
            layer = layer.transform(layer.size, Image.AFFINE, (1, 0, -off, 0, 1, 0))
            layer.putalpha(layer.getchannel("A").point(lambda x: int(x * (1 - v))))
        frame.alpha_composite(layer)
    fr = frame.convert("RGB")
    fade = 1.0
    if is_first:
        fade = min(fade, t / 0.5)
    if is_last_ch:
        fade = min(fade, (D - t) / 0.6)
    if fade < 1:
        fr = Image.blend(Image.new("RGB", (W, H)), fr, max(0.0, fade))
    return fr


# --------------------------------------------------------------------------
# Rendering di un capitolo
# --------------------------------------------------------------------------
def render_capitolo(cap):
    tl = json.loads((OUT / "timeline.json").read_text())
    scenes = [s for s in tl if s["cap"] == cap]
    last_n = tl[-1]["n"]
    cdir = OUT / "capitoli"
    cdir.mkdir(parents=True, exist_ok=True)
    # audio del capitolo
    vdir = OUT / "voce"
    parts = []
    for s in scenes:
        p = vdir / f"{s['n']:02d}.padded.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(vdir / f"{s['n']:02d}.wav"), "-af", f"adelay={int(LEAD * 1000)}:all=1,apad",
                        "-t", f"{s['dur']:.3f}", "-ar", "48000", "-ac", "1", str(p)], check=True)
        parts.append(p)
    lst = cdir / f"cap{cap:02d}_audio.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    wav = cdir / f"cap{cap:02d}.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "pcm_s16le", str(wav)], check=True)
    # sottotitoli del capitolo (tempi relativi al capitolo)
    c0 = scenes[0]["t0"]
    rel = [{**s, "t0": s["t0"] - c0, "speech_t0": s["speech_t0"] - c0} for s in scenes]
    srt = cdir / f"capitolo_{cap:02d}.srt"
    rd.write_srt(rel, srt)
    total = sum(s["dur"] for s in scenes)
    mp4 = cdir / f"capitolo_{cap:02d}.mp4"
    enc = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-i", str(wav), "-i", str(srt), "-map", "0:v", "-map", "1:a", "-map", "2:s",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-profile:v", "high",
                            "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-c:s", "mov_text", "-metadata:s:s:0", "language=ita",
                            "-movflags", "+faststart", "-t", f"{total:.3f}", str(mp4)], stdin=subprocess.PIPE)
    for j, s in enumerate(scenes):
        segs = char_plan(s, s["n"] == last_n)
        nfr = int(round(s["dur"] * FPS))
        for i in range(nfr):
            fr = scene_frame(s, i / FPS, segs, j == 0, j == len(scenes) - 1, s["n"] == last_n)
            enc.stdin.write(fr.tobytes())
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError(f"encoding capitolo {cap} fallito")
    return str(mp4)


def capitoli(which=None):
    tl = timeline()
    caps = sorted({s["cap"] for s in tl})
    if which:
        caps = [c for c in caps if c in which]
    with ProcessPoolExecutor(max_workers=3) as ex:
        for r in ex.map(render_capitolo, caps):
            print("pronto", r)


def corso():
    tl = json.loads((OUT / "timeline.json").read_text())
    cdir = OUT / "capitoli"
    caps = sorted({s["cap"] for s in tl})
    lst = cdir / "concat.txt"
    lst.write_text("".join(f"file '{(cdir / f'capitolo_{c:02d}.mp4').resolve()}'\n" for c in caps))
    srt = OUT / f"corso_{NOME_CORSO}.srt"
    rd.write_srt(tl, srt)
    tmp = OUT / "_corso_senza_sub.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-map", "0:v", "-map", "0:a",
                    "-c", "copy", str(tmp)], check=True)
    mp4 = OUT / f"corso_{NOME_CORSO}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-i", str(srt), "-map", "0:v", "-map", "0:a", "-map", "1:s",
                    "-c", "copy", "-c:s", "mov_text", "-metadata:s:s:0", "language=ita", "-movflags", "+faststart", str(mp4)], check=True)
    tmp.unlink()
    print("corso", mp4)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "prepara":
        prepara()
    elif cmd == "voce":
        voce()
    elif cmd == "timeline":
        tl = timeline(); print(len(tl), "scene,", round(sum(s["dur"] for s in tl) / 60, 2), "min")
    elif cmd == "capitoli":
        capitoli([int(x) for x in sys.argv[2:]] or None)
    elif cmd == "clip":
        estrai_clip()
    elif cmd == "corso":
        corso()
    else:
        print(__doc__)
