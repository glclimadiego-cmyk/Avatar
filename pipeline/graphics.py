"""Grafica tecnica controllata (vettoriale, disegnata via codice).

Tutte le scritte e i dettagli tecnici del video nascono qui, MAI nelle clip
generative: così il testo è sempre corretto e modificabile.
"""
import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1920, 1080
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

NAVY = (22, 46, 120)
BLUE = (40, 120, 220)
LIGHTBLUE = (120, 190, 245)
RED = (220, 50, 40)
ORANGE = (240, 140, 30)
GREEN = (40, 160, 70)
YELLOW = (245, 200, 30)
INK = (25, 30, 40)
WHITE = (255, 255, 255)


@lru_cache(maxsize=64)
def font(size: int, bold: bool = True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def text_c(d: ImageDraw.ImageDraw, xy, s, size, fill=INK, bold=True, anchor="mm", **kw):
    d.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor, **kw)


def arrow(d, p0, p1, fill, width=8, head=22):
    d.line([p0, p1], fill=fill, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    a1, a2 = ang + math.radians(150), ang - math.radians(150)
    d.polygon([p1, (p1[0] + head * math.cos(a1), p1[1] + head * math.sin(a1)),
               (p1[0] + head * math.cos(a2), p1[1] + head * math.sin(a2))], fill=fill)


# --------------------------------------------------------------------------
# Sfondo: centrale termica stilizzata (nessun marchio, nessuna scritta)
# --------------------------------------------------------------------------
@lru_cache(maxsize=4)
def boiler_room(with_monitor: bool = True) -> Image.Image:
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):  # parete con gradiente caldo
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(205 - 60 * k), int(200 - 62 * k), int(190 - 60 * k)))
    floor_y = 860
    for y in range(floor_y, H):
        k = (y - floor_y) / (H - floor_y)
        d.line([(0, y), (W, y)], fill=(int(150 + 40 * k), int(152 + 40 * k), int(158 + 40 * k)))
    for i in range(-6, 14):  # fughe pavimento in prospettiva
        d.line([(W / 2 + i * 60, floor_y), (W / 2 + i * 260, H)], fill=(140, 142, 150), width=2)
    # tubazioni mandata (rosso) / ritorno (blu)
    for y, c in ((120, RED), (175, BLUE)):
        d.rectangle([0, y, W, y + 34], fill=c)
        d.rectangle([0, y + 4, W, y + 10], fill=tuple(min(255, v + 60) for v in c))
    for x, c in ((140, RED), (205, BLUE), (1180, RED), (1245, BLUE)):
        d.rectangle([x, 120, x + 34, floor_y - 40], fill=c)
        d.rectangle([x + 5, 120, x + 11, floor_y - 40], fill=tuple(min(255, v + 60) for v in c))
    # accumulo inerziale (cilindro inox)
    x0, x1, top, bot = 470, 820, 260, 850
    for x in range(x0, x1):
        k = (x - x0) / (x1 - x0)
        shade = int(150 + 90 * math.sin(math.pi * (0.15 + 0.7 * k)))
        d.line([(x, top + 30), (x, bot)], fill=(shade, shade + 3, shade + 8))
    d.ellipse([x0, top, x1, top + 60], fill=(215, 218, 225), outline=(150, 152, 160), width=3)
    for yy in (420, 640):
        d.rectangle([x0, yy, x1, yy + 6], fill=(150, 152, 160))
    # quadro elettrico
    d.rounded_rectangle([900, 330, 1110, 600], radius=8, fill=(225, 226, 222), outline=(160, 160, 160), width=3)
    for i, c in enumerate(((60, 180, 90), (230, 60, 50), (240, 180, 40))):
        d.ellipse([930 + i * 55, 520, 960 + i * 55, 550], fill=c)
    d.rectangle([930, 370, 1080, 450], fill=(70, 140, 160))
    # valvole/manometri sui tubi verticali
    for x in (140, 205, 1180, 1245):
        d.ellipse([x - 12, 520, x + 46, 578], fill=(200, 160, 40), outline=(120, 90, 20), width=3)
    if with_monitor:
        d.rectangle([1560, 640, 1600, floor_y + 20], fill=(110, 112, 120))
        d.rectangle([1490, floor_y + 10, 1670, floor_y + 30], fill=(90, 92, 100))
        d.rounded_rectangle([1250, 230, 1900, 650], radius=14, fill=(35, 38, 45))
    return im.filter(ImageFilter.GaussianBlur(1.2))  # profondità di campo leggera


MONITOR_SCREEN = (1268, 248, 1882, 632)


def outdoor_unit(d, x, y, w, h, t=0.0):
    """Unità esterna aria-acqua generica (senza marchio)."""
    d.rounded_rectangle([x, y, x + w, y + h], radius=int(h * 0.06), fill=(235, 238, 242), outline=(130, 135, 145), width=3)
    r = int(h * 0.38)
    cx, cy = x + int(w * 0.38), y + h // 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(60, 66, 76), outline=(30, 34, 40), width=3)
    for k in range(3):  # ventola che gira
        a = t * 6 + k * 2 * math.pi / 3
        d.polygon([(cx, cy), (cx + r * 0.9 * math.cos(a - 0.35), cy + r * 0.9 * math.sin(a - 0.35)),
                   (cx + r * 0.9 * math.cos(a + 0.35), cy + r * 0.9 * math.sin(a + 0.35))], fill=(150, 156, 166))
    for i in range(-r, r + 1, max(6, r // 7)):
        d.line([(cx - r, cy + i), (cx + r, cy + i)], fill=(90, 96, 106), width=1)
    for i in range(6):
        yy = y + int(h * 0.2) + i * int(h * 0.1)
        d.line([(x + int(w * 0.78), yy), (x + int(w * 0.94), yy)], fill=(150, 155, 165), width=3)


def house_wall(d, x, y0, y1):
    d.rectangle([x, y0, x + 26, y1], fill=(170, 120, 90))
    for yy in range(y0, y1, 28):
        d.line([(x, yy), (x + 26, yy)], fill=(140, 95, 70), width=2)


def radiator(d, x, y, w, h, heat=1.0):
    n = max(4, w // 26)
    for i in range(n):
        xx = x + i * (w / n)
        d.rounded_rectangle([xx + 3, y, xx + w / n - 3, y + h], radius=8, fill=(240, 240, 240), outline=(170, 170, 170), width=2)
    for i in range(3):  # onde di calore
        xx = x + w * (0.25 + 0.25 * i)
        pts = [(xx + 6 * math.sin(heat * 3 + k / 2), y - 10 - k * 4) for k in range(9)]
        d.line(pts, fill=(235, 90, 50), width=3)


# --------------------------------------------------------------------------
# Contenuto monitor (S02): pompa di calore aria-acqua ALL'ESTERNO dell'edificio
# --------------------------------------------------------------------------
def monitor_outdoor(t: float, appear: float = 1.0) -> Image.Image:
    x0, y0, x1, y1 = MONITOR_SCREEN
    w, h = x1 - x0, y1 - y0
    im = Image.new("RGB", (w, h), (232, 242, 252))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 62], fill=NAVY)
    text_c(d, (w // 2, 32), "Pompa di calore aria-acqua", 30, fill=WHITE)
    # esterno (sinistra) | parete | interno (destra)
    d.rectangle([0, 62, 300, h], fill=(214, 232, 250))
    text_c(d, (150, 92), "ESTERNO", 20, fill=(70, 110, 160))
    text_c(d, (470, 92), "INTERNO", 20, fill=(150, 90, 60))
    house_wall(d, 300, 62, h)
    outdoor_unit(d, 40, 150, 220, 160, t)
    text_c(d, (150, 340), "Unità esterna", 22)
    # aria che entra (energia ambiente)
    for i in range(3):
        k = (t * 0.8 + i / 3) % 1
        xa = -40 + int(k * 90)
        arrow(d, (xa, 180 + i * 45), (xa + 40, 180 + i * 45), LIGHTBLUE, width=5, head=14)
    text_c(d, (150, 372), "aria esterna = fonte di energia", 16, bold=False)
    # tubi acqua attraverso la parete
    d.line([(260, 270), (440, 270), (440, 228)], fill=RED, width=10)
    d.line([(260, 296), (520, 296), (520, 228)], fill=BLUE, width=10)
    radiator(d, 400, 170, 160, 60, heat=t)
    text_c(d, (470, 345), "Impianto di riscaldamento", 18)
    if appear < 1:
        veil = Image.new("RGB", im.size, (35, 38, 45))
        im = Image.blend(veil, im, ease(appear))
    return im


# --------------------------------------------------------------------------
# S03: ciclo frigorifero in 4 fasi
# --------------------------------------------------------------------------
PHASES = [
    ("Evaporatore", "il refrigerante evapora", "assorbendo calore dall'aria", BLUE),
    ("Compressore", "aumenta pressione", "e temperatura", ORANGE),
    ("Condensatore", "cede il calore", "all'acqua dell'impianto", RED),
    ("Valvola di espansione", "abbassa la pressione", "e chiude il ciclo", (110, 80, 200)),
]


CYC = (700, 1300, 330, 730)  # L, R, T, B


def _loop_path():
    # rettangolo antiorario visto come: basso (evap) -> destra (compr) -> alto (cond) -> sinistra (valvola)
    L, R, T, B = CYC
    return [(L, B), (R, B), (R, T), (L, T), (L, B)]


def _point_on(path, s):
    segs = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
    lens = [math.dist(a, b) for a, b in segs]
    s = (s % 1) * sum(lens)
    for (a, b), ln in zip(segs, lens):
        if s <= ln:
            k = s / ln
            return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k)
        s -= ln
    return path[-1]


def cycle_diagram(t: float, active: int, appear: float = 1.0) -> Image.Image:
    im = Image.new("RGB", (W, H), (240, 246, 252))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 110], fill=NAVY)
    text_c(d, (W // 2, 56), "Il ciclo frigorifero della pompa di calore", 46, fill=WHITE)
    L, R, T, B = CYC
    mx, my = (L + R) // 2, (T + B) // 2
    # stato del refrigerante: azzurro = miscela fredda BP, blu = vapore BP,
    # rosso = gas caldo AP, arancio = liquido AP
    for seg, col in ((((L, B), (mx, B)), LIGHTBLUE), (((mx, B), (R, B)), BLUE), (((R, B), (R, my)), BLUE),
                     (((R, my), (R, T)), RED), (((R, T), (mx, T)), RED), (((mx, T), (L, T)), ORANGE),
                     (((L, T), (L, my)), ORANGE), (((L, my), (L, B)), LIGHTBLUE)):
        d.line(seg, fill=col, width=14)
    path = _loop_path()
    for i in range(16):
        x, y = _point_on(path, t * 0.12 + i / 16)
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=WHITE, outline=INK, width=2)
    text_c(d, (mx, T + 70), "ALTA PRESSIONE", 22, fill=RED)
    text_c(d, (mx, B - 70), "BASSA PRESSIONE", 22, fill=BLUE)
    boxes = [(mx, B), (R, my), (mx, T), (L, my)]
    for i, ((name, l1, l2, col), (cx, cy)) in enumerate(zip(PHASES, boxes)):
        on = i == active
        bw, bh = (390, 110) if on else (350, 90)
        d.rounded_rectangle([cx - bw // 2, cy - bh // 2, cx + bw // 2, cy + bh // 2], radius=18,
                            fill=col if on else WHITE, outline=col, width=5)
        text_c(d, (cx, cy), f"{i + 1}. {name}", 26 if on else 23, fill=WHITE if on else col)
    if 0 <= active < 4:  # didascalia della fase attiva
        name, l1, l2, col = PHASES[active]
        d.rounded_rectangle([40, 450, 500, 610], radius=20, fill=WHITE, outline=col, width=4)
        text_c(d, (270, 490), f"Fase {active + 1}", 24, fill=col)
        text_c(d, (270, 535), l1, 26, fill=INK)
        text_c(d, (270, 572), l2, 26, fill=INK)
    for i in range(3):  # aria esterna -> evaporatore
        k = (t * 0.7 + i / 3) % 1
        yy = 960 - int(k * 120)
        arrow(d, (mx - 120 + i * 120, yy + 40), (mx - 120 + i * 120, yy), LIGHTBLUE, 7, 18)
    text_c(d, (mx + 220, 920), "calore dall'aria esterna", 26, fill=BLUE, anchor="lm")
    for i in range(3):  # condensatore -> acqua impianto
        k = (t * 0.7 + i / 3) % 1
        yy = 260 - int(k * 100)
        arrow(d, (mx - 120 + i * 120, yy + 40), (mx - 120 + i * 120, yy), RED, 7, 18)
    text_c(d, (mx + 220, 200), "calore all'acqua dell'impianto", 26, fill=RED, anchor="lm")
    bx = R + 330  # energia elettrica al compressore
    d.polygon([(bx, 470), (bx - 40, 560), (bx - 8, 560), (bx - 28, 640), (bx + 30, 535), (bx - 2, 535), (bx + 18, 470)], fill=YELLOW, outline=INK)
    arrow(d, (bx - 45, 555), (R + 210, 555), YELLOW, 8, 20)
    text_c(d, (bx, 680), "energia elettrica", 24, fill=(150, 110, 0))
    if appear < 1:
        im = Image.blend(Image.new("RGB", im.size, (240, 246, 252)), im, ease(appear))
    return im


# --------------------------------------------------------------------------
# S04: circuito idronico + bilancio energetico (qualitativo)
# --------------------------------------------------------------------------
def hydronic_panel(t: float, appear: float = 1.0, grow: float = 1.0, size=(980, 840)) -> Image.Image:
    w, h = size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=26, fill=(248, 250, 253, 255), outline=NAVY, width=4)
    d.rounded_rectangle([0, 0, w - 1, 70], radius=26, fill=NAVY)
    d.rectangle([0, 40, w - 1, 70], fill=NAVY)
    text_c(d, (w // 2, 36), "Dalla pompa di calore all'impianto", 32, fill=WHITE)
    # esterno | parete | interno
    d.rectangle([4, 74, 250, 470], fill=(214, 232, 250))
    text_c(d, (127, 100), "ESTERNO", 18, fill=(70, 110, 160))
    house_wall(d, 250, 74, 470)
    outdoor_unit(d, 24, 160, 200, 140, t)
    text_c(d, (127, 330), "pompa di calore", 18)
    text_c(d, (127, 354), "(es. monoblocco)", 16, bold=False)
    # mandata / ritorno con flusso animato
    sup = [(224, 200), (720, 200), (720, 176)]
    ret = [(224, 260), (780, 260), (780, 176)]
    d.line(sup, fill=RED, width=12)
    d.line(ret, fill=BLUE, width=12)
    d.line([(560, 200), (560, 400)], fill=RED, width=10)
    d.line([(600, 260), (600, 400)], fill=BLUE, width=10)
    for i in range(6):
        k = (t * 0.35 + i / 6) % 1
        x = 224 + k * 480
        d.ellipse([x - 7, 193, x + 7, 207], fill=WHITE)
        x = 704 - k * 480
        d.ellipse([x - 7, 253, x + 7, 267], fill=WHITE)
    text_c(d, (420, 178), "mandata", 18, fill=RED)
    text_c(d, (420, 290), "ritorno", 18, fill=BLUE)
    radiator(d, 660, 130, 180, 46, heat=t)
    text_c(d, (860, 153), "radiatori", 18, anchor="lm")
    # pannelli radianti a pavimento
    for i in range(7):
        y = 400 + i * 10
        d.line([(440, y), (900, y)], fill=(230, 110, 70) if i % 2 == 0 else (110, 150, 220), width=5)
    text_c(d, (670, 490), "pannelli radianti a pavimento", 18)
    # bilancio energetico qualitativo (nessun valore numerico inventato)
    by = 560
    text_c(d, (w // 2, by), "Bilancio energetico", 26, fill=NAVY)
    g = ease(grow)
    e_w, a_w = int(210 * g), int(360 * g)
    y0 = by + 40
    d.rounded_rectangle([60, y0, 60 + max(e_w, 2), y0 + 60], radius=10, fill=YELLOW)
    text_c(d, (60 + 105, y0 + 30), "elettrica", 20)
    text_c(d, (300, y0 + 30), "+", 40)
    d.rounded_rectangle([330, y0, 330 + max(a_w, 2), y0 + 60], radius=10, fill=GREEN)
    text_c(d, (330 + 180, y0 + 30), "dall'aria", 20, fill=WHITE)
    text_c(d, (60 + 285, y0 + 100), "=", 40)
    d.rounded_rectangle([60, y0 + 130, 60 + max(270 * g + a_w, 2), y0 + 190], radius=10, fill=RED)
    text_c(d, (60 + int(270 * g + a_w) // 2, y0 + 160), "calore fornito all'edificio", 20, fill=WHITE)
    text_c(d, (w // 2, h - 22), "Schema qualitativo: le proporzioni dipendono dalle condizioni di lavoro", 15, bold=False, fill=(80, 80, 90))
    if appear < 1:
        a = im.getchannel("A").point(lambda v: int(v * ease(appear)))
        im.putalpha(a)
    return im


# --------------------------------------------------------------------------
# Elementi comuni
# --------------------------------------------------------------------------
def title_card(lines, sub=None, size=(1200, 200)) -> Image.Image:
    w, h = size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=30, fill=(*NAVY, 235))
    for i, s in enumerate(lines):
        text_c(d, (w // 2, 64 + i * 64), s, 48, fill=WHITE)
    if sub:
        hw = int(font(28).getlength(sub)) // 2 + 30
        d.rounded_rectangle([w // 2 - hw, h - 64, w // 2 + hw, h - 14], radius=24, fill=YELLOW)
        text_c(d, (w // 2, h - 39), sub, 28)
    return im


def draft_badge(text: str) -> Image.Image:
    f = font(22)
    tw = int(f.getlength(text)) + 30
    im = Image.new("RGBA", (tw, 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, tw - 1, 39], radius=10, fill=(200, 30, 30, 210))
    d.text((15, 20), text, font=f, fill=WHITE, anchor="lm")
    return im
