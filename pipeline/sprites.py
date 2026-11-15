"""Ritaglio delle pose dalla tavola approvata (sfondo bianco -> trasparente).

Serve SOLO per l'animatic di controllo (timing, grafica, audio, sottotitoli).
Nella produzione finale il personaggio arriva dalle clip image-to-video.
"""
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

# Riquadri (x0, y0, x1, y1) sulla tavola 1535x1024 'avatar_3d_approvato.png'
POSES = {
    "front": (448, 8, 712, 700),
    "present": (712, 8, 1052, 700),
    "side": (1066, 8, 1232, 700),
    "back": (1240, 8, 1512, 700),
}


def _cutout(img: Image.Image, thr: int = 236) -> Image.Image:
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    h, w, _ = a.shape
    near_white = (a.min(axis=2) >= thr) & ((a.max(axis=2) - a.min(axis=2)) < 18)
    # componenti connesse di "quasi bianco": bordo -> sfondo; isole grandi (tra le gambe) -> sfondo
    bg = np.zeros((h, w), bool)
    seen = np.zeros((h, w), bool)
    for sy in range(h):
        for sx in range(w):
            if not near_white[sy, sx] or seen[sy, sx]:
                continue
            comp, q, edge = [], deque([(sy, sx)]), False
            seen[sy, sx] = True
            while q:
                y, x = q.popleft(); comp.append((y, x))
                if y in (0, h - 1) or x in (0, w - 1):
                    edge = True
                for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < h and 0 <= nx < w and near_white[ny, nx] and not seen[ny, nx]:
                        seen[ny, nx] = True; q.append((ny, nx))
            if edge or len(comp) > 600:
                ys, xs = zip(*comp); bg[list(ys), list(xs)] = True
    alpha = Image.fromarray(np.where(bg, 0, 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    out = img.convert("RGBA"); out.putalpha(alpha)
    return out.crop(out.getbbox())


def extract(sheet_path: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    sheet = Image.open(sheet_path)
    paths = {}
    for name, box in POSES.items():
        p = out_dir / f"pose_{name}.png"
        if not p.exists():
            _cutout(sheet.crop(box)).save(p)
        paths[name] = p
    return paths


if __name__ == "__main__":
    import sys
    print(extract(Path(sys.argv[1]), Path(sys.argv[2])))
