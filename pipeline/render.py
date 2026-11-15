"""Timeline, sottotitoli, compositing e encoding (Pillow -> FFmpeg).

Base di ogni scena:
  - clip generativa in <out>/clips/<ID>.mp4 se esiste (produzione), oppure
  - "animatic" disegnato: sfondo vettoriale + pose ritagliate dalla tavola
    approvata (solo controllo di tempi/grafica/audio, NON è il risultato finale).
Sopra la base vanno sempre gli overlay vettoriali di graphics.py.
"""
import json
import math
import re
import subprocess
from pathlib import Path

from PIL import Image

import graphics as g
from sprites import extract

FPS = 25
W, H = g.W, g.H
LEAD, TAIL = 0.5, 0.8  # silenzio prima/dopo la battuta in ogni scena

# Layout di default per il pilota (sovrascrivibile con scene["layout"])
DEFAULT_LAYOUT = {"S01": "walk_in", "S02": "walk_to_monitor", "S03": "diagram_cycle",
                  "S04": "hydronic", "S05": "closeup"}


# --------------------------------------------------------------------------
# Copione e timeline
# --------------------------------------------------------------------------
def parse_script(md: str) -> dict:
    """Sezioni '**00–10 s — titolo**' seguite da «testo»."""
    out = {}
    for m in re.finditer(r"\*\*(\d+)\s*[–-]\s*(\d+)\s*s[^*]*\*\*\s*\n«(.+?)»", md, re.S):
        out[f"{int(m.group(1)):02d}-{int(m.group(2)):02d}"] = " ".join(m.group(3).split())
    return out


def build_timeline(scenes, voice_durs):
    t, tl = 0.0, []
    for sc in scenes:
        vd = voice_durs[sc["id"]]
        dur = max(LEAD + vd + TAIL, float(sc.get("min_seconds", 3)))
        tl.append({**sc, "t0": round(t, 3), "dur": round(dur, 3), "speech_t0": round(t + LEAD, 3), "speech_dur": round(vd, 3)})
        t += dur
    return tl


def cue_time(sc, keyword: str) -> float:
    """Istante (relativo alla scena) in cui la voce pronuncia `keyword` (stima proporzionale ai caratteri)."""
    txt = sc["text"].lower()
    i = txt.find(keyword.lower())
    frac = 0 if i < 0 else i / max(1, len(txt))
    return LEAD + frac * sc["speech_dur"]


# --------------------------------------------------------------------------
# Sottotitoli SRT
# --------------------------------------------------------------------------
def _chunks(text, maxlen=84):
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for p in parts:
        while len(p) > maxlen:
            cut = max(p.rfind(", ", 0, maxlen), p.rfind(" ", 0, maxlen))
            cut = cut + 1 if cut > 0 else maxlen
            out.append(p[:cut].strip()); p = p[cut:].strip()
        if p:
            out.append(p)
    return out


def _wrap2(s, width=42):
    if len(s) <= width:
        return s
    mid = len(s) // 2
    cands = [i for i, c in enumerate(s) if c == " "]
    i = min(cands, key=lambda k: abs(k - mid)) if cands else mid
    return s[:i].strip() + "\n" + s[i:].strip()


def _ts(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def write_srt(tl, path: Path):
    n, lines = 1, []
    for sc in tl:
        chunks = _chunks(sc["text"])
        total = sum(len(c) for c in chunks)
        t = sc["speech_t0"]
        for c in chunks:
            d = sc["speech_dur"] * len(c) / total
            lines += [str(n), f"{_ts(t)} --> {_ts(t + d)}", _wrap2(c), ""]
            n += 1; t += d
    path.write_text("\n".join(lines), encoding="utf-8")


# --------------------------------------------------------------------------
# Audio
# --------------------------------------------------------------------------
def build_voiceover(tl, voice_dir: Path, out_wav: Path):
    parts = []
    for sc in tl:
        p = voice_dir / f"{sc['id']}.padded.wav"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(voice_dir / f"{sc['id']}.wav"),
                        "-af", f"adelay={int(LEAD * 1000)}:all=1,apad", "-t", f"{sc['dur']:.3f}",
                        "-ar", "48000", "-ac", "1", str(p)], check=True)
        parts.append(p)
    lst = voice_dir / "concat.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:a", "pcm_s16le", str(out_wav)], check=True)


# --------------------------------------------------------------------------
# Personaggio (animatic)
# --------------------------------------------------------------------------
class Actor:
    def __init__(self, sprite_dir: Path, sheet: Path):
        self.paths = extract(sheet, sprite_dir)
        self.src = {k: Image.open(v).convert("RGBA") for k, v in self.paths.items()}
        self.cache = {}

    def get(self, pose, height):
        k = (pose, int(height))
        if k not in self.cache:
            s = self.src[pose]
            self.cache[k] = s.resize((int(s.width * height / s.height), int(height)), Image.LANCZOS)
        return self.cache[k]

    def draw(self, frame, pose, cx, feet_y, height, bob=0.0, alpha=1.0, flip=False):
        sp = self.get(pose, height)
        if flip:
            sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
        if alpha < 1:
            sp = sp.copy(); sp.putalpha(sp.getchannel("A").point(lambda v: int(v * alpha)))
        frame.alpha_composite(sp, (int(cx - sp.width / 2), int(feet_y - sp.height - bob)))

    def shadow(self, frame, cx, feet_y, w):
        sh = Image.new("RGBA", (int(w), 40), (0, 0, 0, 0))
        from PIL import ImageDraw, ImageFilter
        ImageDraw.Draw(sh).ellipse([0, 5, w, 35], fill=(0, 0, 0, 90))
        sh = sh.filter(ImageFilter.GaussianBlur(6))
        frame.alpha_composite(sh, (int(cx - w / 2), int(feet_y - 22)))


def walk_bob(t, step_hz=1.9):
    return 9 * abs(math.sin(math.pi * step_hz * t))


def crossfade_pose(actor, frame, t, t_switch, a, b, **kw):
    k = g.ease((t - t_switch) / 0.3)
    if k <= 0:
        actor.draw(frame, a, **kw)
    elif k >= 1:
        actor.draw(frame, b, **kw)
    else:
        actor.draw(frame, a, alpha=1 - k, **kw); actor.draw(frame, b, alpha=k, **kw)


def camera(frame: Image.Image, zoom: float, cx: float, cy: float) -> Image.Image:
    """Zoom digitale centrato in (cx, cy) – simula carrellate/push-in."""
    if abs(zoom - 1) < 1e-3:
        return frame
    w, h = W / zoom, H / zoom
    x0 = min(max(cx - w / 2, 0), W - w); y0 = min(max(cy - h / 2, 0), H - h)
    return frame.crop((int(x0), int(y0), int(x0 + w), int(y0 + h))).resize((W, H), Image.BILINEAR)


# --------------------------------------------------------------------------
# Layout delle scene
# --------------------------------------------------------------------------
FLOOR = 1010
FULL_H = 760


def scene_frame(sc, t, actor: Actor, base: Image.Image | None):
    """t = secondi dall'inizio scena. base = fotogramma della clip generativa (se c'è)."""
    lay = sc.get("layout") or DEFAULT_LAYOUT.get(sc["id"], "talk")
    D = sc["dur"]
    if base is not None:
        fr = base.convert("RGBA")
        draw_actor = False
    else:
        fr = g.boiler_room(True).convert("RGBA")
        draw_actor = True

    def monitor(content):
        if base is None:
            fr.paste(content, g.MONITOR_SCREEN[:2])
        else:  # nella clip il monitor non è tracciabile: riquadro grafico sovrapposto
            c = content.resize((int(content.width * 0.9), int(content.height * 0.9)))
            fr.paste(c, (W - c.width - 40, 60))

    if lay == "walk_in":
        t_stop = 0.45 * D
        monitor(g.monitor_outdoor(t, appear=0.0))
        x = -250 + (760 + 250) * g.ease(min(t / t_stop, 1)) if t < t_stop else 760
        if draw_actor:
            actor.shadow(fr, x, FLOOR, 260)
            if t < t_stop:
                actor.draw(fr, "side", x, FLOOR, FULL_H, bob=walk_bob(t))
            else:
                crossfade_pose(actor, fr, t, t_stop, "side", "present", cx=x, feet_y=FLOOR, height=FULL_H)
        k = g.ease((t - 0.6) / 0.6) - g.ease((t - (D - 1.2)) / 0.6)
        if k > 0:
            card = g.title_card(["La pompa di calore"], sub="Come funziona", size=(900, 200))
            card.putalpha(card.getchannel("A").point(lambda v: int(v * k)))
            fr.alpha_composite(card, (W // 2 - 450, 70))
        fr = camera(fr, 1.0 + 0.06 * g.ease(t / D), 760, 600)

    elif lay == "walk_to_monitor":
        t_stop = 0.35 * D
        monitor(g.monitor_outdoor(t, appear=(t - 0.2 * D) / 0.15 / D))
        x = 760 + (1080 - 760) * g.ease(min(t / t_stop, 1))
        if draw_actor:
            actor.shadow(fr, x, FLOOR, 260)
            if t < t_stop:
                actor.draw(fr, "side", x, FLOOR, FULL_H, bob=walk_bob(t))
            else:
                crossfade_pose(actor, fr, t, t_stop, "side", "present", cx=x, feet_y=FLOOR, height=FULL_H)
        fr = camera(fr, 1.12, 700 + 600 * g.ease(t / D), 560)  # carrellata laterale

    elif lay == "diagram_cycle":
        cues = [cue_time(sc, k) for k in sc.get("cues", ["evapora", "compressore", "condensatore", "valvola"])]
        active = max([i for i, c in enumerate(cues) if t >= c - 0.15] or [0])
        diag = g.cycle_diagram(t, active, appear=(t - 1.0) / 0.6).convert("RGBA")
        intro = 1.4 if sc.get("base", "clip") == "clip" else -1
        if t < intro + 0.4:  # alternanza: personaggio che "introduce" lo schema
            room = fr
            if draw_actor:
                actor.draw(room, "present", 1080, FLOOR, FULL_H)
            room = camera(room, 1.25, 1250, 560)
            k = g.ease((t - intro) / 0.4)
            fr = Image.blend(room.convert("RGB"), diag.convert("RGB"), k).convert("RGBA")
        else:
            fr = diag
            if draw_actor:  # riquadro con il personaggio
                actor.draw(fr, "present", 270, 1075, 420)

    elif lay == "hydronic":
        if draw_actor:
            actor.draw(fr, "present", 330, FLOOR + 640, 1500)  # piano americano: taglio sotto le ginocchia
        panel = g.hydronic_panel(t, appear=(t - 0.6) / 0.8, grow=(t - cue_time(sc, sc.get("cue_balance", "energia elettrica"))) / 2.0)
        fr.alpha_composite(panel, (W - panel.width - 50, 160))

    elif lay == "closeup":
        if draw_actor:
            actor.draw(fr, "present", 960, FLOOR + 1560, 2400)  # mezzo busto
        fr = camera(fr, 1.0 + 0.05 * g.ease(t / D), 960, 400)
        k = g.ease((t - 0.35 * D) / 0.6)
        if k > 0:
            card = g.title_card(["Prossimi episodi"], sub="Dimensionamento · Installazione · Efficienza", size=(1100, 200))
            card = card.resize((880, 160))
            card.putalpha(card.getchannel("A").point(lambda v: int(v * k)))
            fr.alpha_composite(card, (W // 2 - 440, 860))

    else:  # 'talk' generico
        if draw_actor:
            actor.draw(fr, "present", 760, FLOOR, FULL_H)

    fr = fr.convert("RGB")
    fade = min(1.0, t / 0.4) if sc.get("_first") else 1.0
    if sc.get("_last"):
        fade = min(fade, (D - t) / 0.6)
    if fade < 1:
        fr = Image.blend(Image.new("RGB", (W, H)), fr, max(0.0, fade))
    return fr


# --------------------------------------------------------------------------
# Lettura clip generative
# --------------------------------------------------------------------------
class ClipReader:
    def __init__(self, path: Path):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-vf",
                                   f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={FPS}",
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.last = None

    def next(self):
        buf = self.p.stdout.read(W * H * 3)
        if len(buf) == W * H * 3:
            self.last = Image.frombytes("RGB", (W, H), buf)
        return self.last  # se la clip è più corta della battuta, tiene l'ultimo fotogramma


# --------------------------------------------------------------------------
# Render finale
# --------------------------------------------------------------------------
def render(tl, out_mp4: Path, wav: Path, srt: Path, actor: Actor, clips_dir: Path, badge: str | None,
           only: set | None = None, max_seconds: float | None = None):
    sel = [sc for sc in tl if not only or sc["id"] in only]
    sel[0]["_first"] = True; sel[-1]["_last"] = True
    a0 = sel[0]["t0"]
    total = sum(sc["dur"] for sc in sel)
    if max_seconds:
        total = min(total, max_seconds)
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-ss", f"{a0:.3f}", "-t", f"{total:.3f}", "-i", str(wav)]
    if srt and not only:
        cmd += ["-i", str(srt), "-map", "0:v", "-map", "1:a", "-map", "2:s", "-c:s", "mov_text", "-metadata:s:s:0", "language=ita"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-t", f"{total:.3f}", str(out_mp4)]
    enc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    bad = g.draft_badge(badge) if badge else None
    written = 0
    for sc in sel:
        clip = clips_dir / f"{sc['id']}.mp4"
        reader = ClipReader(clip) if clip.exists() and sc.get("base", "clip") == "clip" else None
        n = int(round(sc["dur"] * FPS))
        for i in range(n):
            if written >= total * FPS:
                break
            base = reader.next() if reader else None
            fr = scene_frame(sc, i / FPS, actor, base)
            if bad is not None:
                fr = fr.convert("RGBA"); fr.alpha_composite(bad, (W - bad.width - 24, H - bad.height - 24)); fr = fr.convert("RGB")
            enc.stdin.write(fr.tobytes())
            written += 1
    enc.stdin.close()
    if enc.wait() != 0:
        raise RuntimeError("ffmpeg encoding fallito")
    return written


def probe(p: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration,size:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
                        "-of", "json", str(p)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def contact_sheet(mp4: Path, times, dest: Path):
    thumbs = []
    for i, t in enumerate(times):
        f = dest.parent / f"_thumb{i}.png"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(mp4), "-frames:v", "1",
                        "-vf", "scale=640:360", str(f)], check=True)
        thumbs.append(Image.open(f).copy()); f.unlink()
    cols = 3
    rows = math.ceil(len(thumbs) / cols)
    sheet = Image.new("RGB", (cols * 640, rows * 360), (0, 0, 0))
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i % cols) * 640, (i // cols) * 360))
    sheet.save(dest)
