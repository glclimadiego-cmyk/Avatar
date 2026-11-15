"""Servizi esterni (TTS, image-to-video, keyframe) + registro costi/approvazioni.

Regola: nessuna chiamata a pagamento o invio di dati a terzi senza
- chiave presente nell'ambiente,
- voce corrispondente approvata in <out>/approvals.json (comando `approve`).
Ogni chiamata (riuscita o fallita) finisce in <out>/ledger.jsonl.
"""
import base64
import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Tariffe INDICATIVE (USD) da verificare sul listino prima di approvare.
# Fonti consultate il 2026-11-15 (siti terzi, non il listino ufficiale):
# Kling 2.5 Turbo Pro i2v su fal ~0.07 $/s; Kling 3.0 Turbo Pro ~0.14 $/s;
# ElevenLabs Multilingual v2: 0.05-0.17 $/1000 caratteri a seconda della fonte.
DEFAULT_RATES = {
    "fal_video_usd_per_s": 0.14,
    "fal_keyframe_usd_per_image": 0.04,
    "elevenlabs_usd_per_1k_chars": 0.17,
}


class ApprovalRequired(RuntimeError):
    pass


class Ledger:
    def __init__(self, out: Path):
        self.out = out
        out.mkdir(parents=True, exist_ok=True)
        self.path = out / "ledger.jsonl"
        self.approvals_path = out / "approvals.json"

    def log(self, **kw):
        kw.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="seconds"))
        with self.path.open("a") as f:
            f.write(json.dumps(kw, ensure_ascii=False) + "\n")

    def entries(self):
        if not self.path.exists():
            return []
        return [json.loads(l) for l in self.path.read_text().splitlines() if l.strip()]

    def approvals(self) -> dict:
        return json.loads(self.approvals_path.read_text()) if self.approvals_path.exists() else {}

    def approve(self, key: str, max_usd: float | None, note: str = ""):
        a = self.approvals()
        a[key] = {"approved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                  "max_usd": max_usd, "note": note}
        self.approvals_path.write_text(json.dumps(a, indent=2, ensure_ascii=False))
        self.log(stage="approval", key=key, max_usd=max_usd, note=note)

    def spent(self, key: str) -> float:
        return sum(e.get("est_cost_usd", 0) for e in self.entries() if e.get("approval") == key and e.get("status") == "ok")

    def require(self, key: str, est_cost: float, what: str):
        a = self.approvals().get(key)
        if not a:
            raise ApprovalRequired(
                f"[STOP] '{what}' richiede approvazione '{key}'. Costo stimato ~{est_cost:.2f} USD.\n"
                f"       Per autorizzare: python3 pipeline/make_course.py approve --out {self.out} --key {key} --max-usd <tetto>")
        cap = a.get("max_usd")
        if cap is not None and self.spent(key) + est_cost > cap + 1e-9:
            raise ApprovalRequired(f"[STOP] tetto di spesa '{key}' ({cap} USD) superato: già spesi {self.spent(key):.2f}, richiesti {est_cost:.2f}.")


def ffprobe_duration(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def _http(method, url, headers, body=None, timeout=120):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(), r.headers.get("Content-Type", "")


# --------------------------------------------------------------------------
# TTS
# --------------------------------------------------------------------------
def tts(provider: str, text: str, out_wav: Path, ledger: Ledger, cfg: dict) -> float:
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    if provider == "espeak":
        # Voce sintetica offline, gratuita, robotica: SOLO segnaposto per i tempi.
        subprocess.run(["espeak-ng", "-v", "it", "-s", str(cfg.get("espeak_speed", 150)), "-p", "40",
                        "-w", str(out_wav) + ".raw.wav", text], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(out_wav) + ".raw.wav", "-ar", "48000", "-ac", "1",
                        str(out_wav)], check=True)
        os.remove(str(out_wav) + ".raw.wav")
        ledger.log(stage="voice", service="espeak-ng (locale)", chars=len(text), est_cost_usd=0.0, status="ok")
        return ffprobe_duration(out_wav)

    if provider == "elevenlabs":
        key = os.environ.get("ELEVENLABS_API_KEY")
        voice = cfg.get("elevenlabs_voice_id")
        if not key or not voice:
            raise RuntimeError("ElevenLabs: servono ELEVENLABS_API_KEY nell'ambiente e 'elevenlabs_voice_id' in course.json")
        est = len(text) / 1000 * cfg["rates"]["elevenlabs_usd_per_1k_chars"]
        ledger.require("voice_paid", est, "voce ElevenLabs")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128"
        try:
            audio, _ = _http("POST", url, {"xi-api-key": key, "Accept": "audio/mpeg"},
                             {"text": text, "model_id": cfg.get("elevenlabs_model", "eleven_multilingual_v2"),
                              "language_code": "it"})
        except urllib.error.HTTPError as e:
            ledger.log(stage="voice", service="elevenlabs", approval="voice_paid", status="error", error=f"{e.code} {e.read()[:300]!r}")
            raise
        mp3 = out_wav.with_suffix(".mp3")
        mp3.write_bytes(audio)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-ar", "48000", "-ac", "1", str(out_wav)], check=True)
        ledger.log(stage="voice", service="elevenlabs", approval="voice_paid", chars=len(text), est_cost_usd=round(est, 4), status="ok")
        return ffprobe_duration(out_wav)

    raise ValueError(f"TTS sconosciuto: {provider}")


# --------------------------------------------------------------------------
# fal.ai (coda asincrona): keyframe (image edit) e image-to-video
# --------------------------------------------------------------------------
def _data_uri(p: Path) -> str:
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def _fal_run(model: str, payload: dict, poll_s=5, timeout_s=1200) -> dict:
    key = os.environ.get("FAL_KEY")
    if not key:
        raise RuntimeError("fal.ai: serve FAL_KEY nell'ambiente (e l'host queue.fal.run consentito nella rete)")
    h = {"Authorization": f"Key {key}"}
    raw, _ = _http("POST", f"https://queue.fal.run/{model}", h, payload)
    sub = json.loads(raw)
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        st = json.loads(_http("GET", sub["status_url"], h)[0])
        if st.get("status") == "COMPLETED":
            return json.loads(_http("GET", sub["response_url"], h)[0])
        if st.get("status") not in ("IN_QUEUE", "IN_PROGRESS"):
            raise RuntimeError(f"fal.ai stato inatteso: {st}")
        time.sleep(poll_s)
    raise TimeoutError("fal.ai: timeout generazione")


def _download(url: str, dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=300) as r:
        dest.write_bytes(r.read())


def last_frame(mp4: Path, dest: Path):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-sseof", "-0.1", "-i", str(mp4), "-frames:v", "1", "-update", "1", str(dest)], check=True)


def concat_clips(parts: list[Path], dest: Path):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if len(parts) == 1:
        dest.write_bytes(parts[0].read_bytes()); return
    lst = dest.with_suffix(".txt")
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-an",
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", str(dest)], check=True)


def generate_keyframe(scene: dict, refs: list[Path], dest: Path, ledger: Ledger, cfg: dict, approval: str):
    est = cfg["rates"]["fal_keyframe_usd_per_image"]
    ledger.require(approval, est, f"keyframe {scene['id']}")
    model = cfg.get("fal_keyframe_model", "fal-ai/nano-banana/edit")
    try:
        res = _fal_run(model, {"prompt": scene["keyframe_prompt"], "image_urls": [_data_uri(p) for p in refs],
                               "num_images": 1, "output_format": "png"})
        _download(res["images"][0]["url"], dest)
    except Exception as e:
        ledger.log(stage="keyframe", scene=scene["id"], service=f"fal:{model}", approval=approval, status="error", error=str(e)[:400])
        raise
    ledger.log(stage="keyframe", scene=scene["id"], service=f"fal:{model}", approval=approval, est_cost_usd=est, status="ok")


def generate_clip(scene: dict, keyframe: Path, seconds: int, dest: Path, ledger: Ledger, cfg: dict, approval: str):
    est = seconds * cfg["rates"]["fal_video_usd_per_s"]
    ledger.require(approval, est, f"clip {scene['id']} ({seconds}s)")
    model = cfg.get("fal_video_model", "fal-ai/kling-video/v2.5-turbo/pro/image-to-video")
    try:
        res = _fal_run(model, {"prompt": scene["motion_prompt"], "image_url": _data_uri(keyframe),
                               "duration": str(seconds), "negative_prompt": cfg.get("negative_prompt", "")})
        _download(res["video"]["url"], dest)
    except Exception as e:
        ledger.log(stage="clip", scene=scene["id"], service=f"fal:{model}", approval=approval, status="error", error=str(e)[:400])
        raise
    ledger.log(stage="clip", scene=scene["id"], service=f"fal:{model}", approval=approval, seconds=seconds, est_cost_usd=round(est, 3), status="ok")
