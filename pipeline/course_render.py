#!/usr/bin/env python3
"""Montaggio di un videocorso "a slide" con il personaggio del pacchetto clip.

Ingressi (pacchetto del corso): Storyboard_Animazione.xlsx, Slide_Fotovoltaico.pptx (o simile),
Screenshot_App/, voce clonata ElevenLabs, clip scontornate in output/clip_pack/clips_alfa.

  python3 pipeline/course_render.py prepara   # slide -> immagini, evidenziazioni, clip personaggio
  python3 pipeline/course_render.py voce      # voce per scena (ElevenLabs)
  python3 pipeline/course_render.py capitoli [N ...]   # rendering dei capitoli (in parallelo)
  python3 pipeline/course_render.py corso     # unisce i capitoli, SRT completo, verifiche, report
"""
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
POSE_DIR = ROOT / "output" / "pose_personaggio"   # pose ritagliate, comuni a tutti i corsi
W, H, FPS = 1920, 1080, 25
LEAD, TAIL = 0.6, 0.9
WALK = 1.8              # secondi di camminata al cambio di lato
CHAR_H = 860            # altezza del personaggio in pixel
FEET_Y = 1058
EMU_W, EMU_H = 12191695, 6858000

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
        wav = vdir / f"{n:02d}.wav"
        tag = vdir / f"{n:02d}.tag"
        key = f"{cfg['elevenlabs_voice_id']}:{cfg['elevenlabs_model']}:{hash(txt)}"
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
        side = (s["Lato del personaggio"] or geo[n - 1]["side"]).strip().lower()
        walk = WALK if (prev_side is None or side != prev_side) else 0.0
        sec = None
        for col in ("Elementi da evidenziare", "Zoom e transizioni"):
            m = SECONDARIA.search(s.get(col) or "")
            if m:
                sec = m.group(1).strip()
        # pause per mostrare le operazioni: più evidenziazioni o una seconda schermata = più tempo
        extra = min(2.5, 0.5 * len(geo[n - 1]["groups"])) + (1.2 if sec else 0.0)
        dur = round(max(LEAD + vd + TAIL + extra, walk + 3.0), 3)
        mov = s["Movimento del personaggio"] or ""
        tl.append({"n": n, "cap": int(str(s["Capitolo"]).split("—")[0].strip()), "cap_titolo": str(s["Capitolo"]),
                   "titolo": s["Titolo della slide"], "t0": round(t, 3), "dur": dur, "speech_t0": round(t + LEAD, 3),
                   "speech_dur": round(vd, 3), "text": clean_sub(s["Testo pronunciato"]), "side": side,
                   "prev_side": prev_side, "walk": walk, "gesti": gesti(mov), "mov": mov,
                   "zoom": "zoom" in (s["Zoom e transizioni"] or "").lower(), "secondaria": sec,
                   "avviso": bool(re.search(r"errore|avviso|allarme|rosso|impedisce", (s["Elementi da evidenziare"] or "") + " " + (s["Zoom e transizioni"] or ""), re.I)),
                   "geo": geo[n - 1]})
        prev_side = side
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


def char_plan(sc, is_last):
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
def secondary_layer(n, name, pic):
    """Immagine della slide con la schermata secondaria al posto di quella principale (pc) o card telefono."""
    f = find_shot(name)
    base = slide_img(n, "base").copy()
    shot = Image.open(f).convert("RGB")
    if name.startswith("pc-") and pic:
        x0, y0, x1, y1 = [int(v) for v in pic]
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


def scene_frame(sc, t, segs, is_first_of_chapter, is_last_of_chapter, is_last):
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
        lay = secondary_layer(n, sec, tuple(geo["pic"]) if geo["pic"] else None)
        img = Image.blend(img, lay, k) if k < 1 else lay
        show_hl = t < sec_t + 0.5
    else:
        show_hl = True
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
        card = phone_card(sec)
        k = ease((t - sec_t) / 0.5)
        x = int((W * 0.70 if sc["side"] == "destra" else W * 0.30) - (card.width if sc["side"] == "destra" else 0))
        y = int(H - card.height - 40 + (1 - k) * 200)
        if k < 1:
            card = card.copy(); card.putalpha(card.getchannel("A").point(lambda v: int(v * k)))
        frame.alpha_composite(card, (x, y))
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
    elif cmd == "corso":
        corso()
    else:
        print(__doc__)
