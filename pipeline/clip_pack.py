#!/usr/bin/env python3
"""Pacchetto di clip riutilizzabili del personaggio (fondo verde -> scontornate).

Si genera una volta sola e si riusa in tutti i corsi: le clip vengono sovrapposte
alle slide nel terzo di schermo libero. Le pose rivolte a un lato si specchiano per l'altro.

  python3 pipeline/clip_pack.py keyframes   # immagini di partenza (si ferma per revisione)
  python3 pipeline/clip_pack.py clips       # video (dopo approvazione dei keyframe)
  python3 pipeline/clip_pack.py key         # scontorno -> WebM/MOV con trasparenza + anteprime
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import providers as pv  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "clip_pack"
SHEET = ROOT / "pilota" / "assets" / "avatar_3d_approvato.png"
STYLE_REF = ROOT / "output" / "pilota" / "keyframes" / "S05.png"  # resa 3D approvata nel pilota

CHAR = ("Use the FIRST image (character sheet) for the character: identical face, bald head with short dark hair on the sides, "
        "dark-blue rectangular glasses, salt-and-pepper beard, stocky adult build with normal proportions (not chibi), "
        "plain navy polo shirt without logo, dark grey work trousers with orange-trimmed cargo pockets, black belt, "
        "dark safety shoes with orange laces, black smartwatch. Use the SECOND image only for the 3D render style and lighting. ")
GREEN = (" Background: a perfectly uniform flat chroma-key green (#00B140) studio backdrop filling the whole frame, evenly lit, "
         "no floor line, no shadows on the background, no props, no text. Full body visible with some margin around him, "
         "centered. Pixar-like 3D render, soft front light, 16:9.")
MOTION_TAIL = (" The background stays uniform flat green for the whole clip, no shadows, no objects appear. Face, glasses and clothes "
               "stay identical, five-fingered hands. Static camera.")

POSES = {
    "cammina": {"secs": 10,
        "kf": "He is walking toward the right of the frame, seen in three-quarter side view, mid-stride.",
        "motion": "He walks in place toward the right with a natural relaxed walk cycle, arms swinging gently, as if crossing a stage."},
    "parla": {"secs": 10,
        "kf": "He stands facing the camera, relaxed, friendly expression, mouth slightly open as if talking.",
        "motion": "He talks to the camera in a friendly, conversational way with natural small hand gestures and slight nods, then smiles."},
    "indica": {"secs": 5,
        "kf": "He stands in three-quarter view turned toward the right side of the frame, smiling.",
        "motion": "He raises his right arm and points with the index finger toward the right side of the frame, looks there, then looks back at the camera."},
    "saluta": {"secs": 5,
        "kf": "He stands facing the camera with a warm smile.",
        "motion": "He raises his right hand and waves hello to the camera with a warm smile, then lowers it."},
    "conta": {"secs": 5,
        "kf": "He stands facing the camera, both hands in front of his chest.",
        "motion": "He counts on his fingers, raising one, two, then three fingers of his right hand toward the camera while talking."},
    "telefono": {"secs": 5,
        "kf": "He stands facing the camera holding a black smartphone in his right hand at chest height, the screen facing the camera, the screen is plain white and empty.",
        "motion": "He holds the smartphone up showing its screen to the camera, glances at it, then looks back at the camera and nods. The phone screen stays plain white and empty."},
    "pollice": {"secs": 5,
        "kf": "He stands facing the camera with a satisfied smile.",
        "motion": "He gives a confident thumbs up with his right hand and smiles broadly."},
    "attenzione": {"secs": 5,
        "kf": "He stands facing the camera with a serious, focused expression.",
        "motion": "With a serious expression he raises his right index finger as a warning, shakes his head slightly, then lowers his hand."},
}


def ledger():
    return pv.Ledger(OUT)


def cfg():
    c = json.loads((ROOT / "pilota" / "course.json").read_text())
    return {**c, "keyframe_resolution": "2K"}


def keyframes(ok_flag=False):
    led, c = ledger(), cfg()
    kdir = OUT / "keyframes"
    for name, p in POSES.items():
        kf = kdir / f"{name}.png"
        if not kf.exists():
            sc = {"id": name, "keyframe_prompt": CHAR + p["kf"] + GREEN}
            pv.generate_keyframe(sc, [SHEET, STYLE_REF], kf, led, c, "clip_pack")
            print("keyframe", name, "ok")
    if ok_flag:
        for name in POSES:
            (kdir / f"{name}.approvato").write_text("ok")


def clips():
    led, c = ledger(), cfg()
    for name, p in POSES.items():
        kf = OUT / "keyframes" / f"{name}.png"
        if not kf.with_suffix(".approvato").exists():
            print(f"[STOP] keyframe {name} non approvato"); continue
        dest = OUT / "clips_verdi" / f"{name}.mp4"
        if not dest.exists():
            sc = {"id": name, "motion_prompt": p["motion"] + MOTION_TAIL}
            pv.generate_clip(sc, kf, p["secs"], dest, led, {**c, "negative_prompt": c.get("negative_prompt", "") + ", background objects, shadows on wall, floor"}, "clip_pack")
            print("clip", name, "ok")


def key():
    """Scontorno del verde -> WebM VP9 con canale alfa (+ anteprima su grigio)."""
    src, dst, prev = OUT / "clips_verdi", OUT / "clips_alfa", OUT / "anteprime"
    dst.mkdir(parents=True, exist_ok=True); prev.mkdir(parents=True, exist_ok=True)
    flt = "chromakey=0x00B140:0.13:0.06,despill=type=green:mix=0.6:expand=0.1,format=yuva420p"
    for f in sorted(src.glob("*.mp4")):
        out = dst / (f.stem + ".webm")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(f), "-vf", f"fps=25,{flt}", "-c:v", "libvpx-vp9",
                        "-pix_fmt", "yuva420p", "-b:v", "3M", "-auto-alt-ref", "0", "-an", str(out)], check=True)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0x8a8f99:s=1920x1080:r=25",
                        "-c:v", "libvpx-vp9", "-i", str(out), "-filter_complex", "[1:v]scale=1920:-2[f];[0:v][f]overlay=(W-w)/2:(H-h)/2:shortest=1",
                        "-c:v", "libx264", "-crf", "22", "-pix_fmt", "yuv420p", str(prev / (f.stem + ".mp4"))], check=True)
        print("scontornata", f.stem)


def key_still(png: Path, dest: Path):
    """Prova di scontorno su un'immagine (per la revisione dei keyframe)."""
    flt = "chromakey=0x00B140:0.13:0.06,despill=type=green:mix=0.6:expand=0.1"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0x8a8f99:s=2752x1536", "-i", str(png),
                    "-filter_complex", f"[1:v]{flt}[k];[0:v][k]overlay=shortest=1", "-frames:v", "1", str(dest)], check=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    try:
        if cmd == "keyframes":
            keyframes("--ok" in sys.argv)
        elif cmd == "clips":
            clips()
        elif cmd == "key":
            key()
        else:
            print(__doc__)
    except pv.ApprovalRequired as e:
        print(e); sys.exit(2)
