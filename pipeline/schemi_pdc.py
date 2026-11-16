#!/usr/bin/env python3
"""Schemi tecnici del corso «Pompe di calore» (episodi 02-06), disegnati da codice.

Ogni schema: PNG 2580x1677 (stesso formato degli schemi dei pacchetti) + riquadri da evidenziare
(in pixel dello schema), nell'ordine in cui vengono spiegati.
Le scritte nascono solo qui: niente testo inventato da modelli generativi.
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 2580, 1677
BG = (255, 252, 245)
INK = (43, 36, 24)
MUTED = (122, 106, 82)
AMBRA = (181, 105, 0)
AMBRA_L = (244, 227, 195)
CARD = (255, 255, 255)
BORDO = (232, 199, 122)
ROSSO = (205, 48, 40)
BLU = (42, 111, 201)
AZZURRO = (125, 185, 240)
VERDE = (46, 150, 70)
GRIGIO = (150, 150, 155)
FB = "/usr/share/fonts/truetype/open-sans/OpenSans-Bold.ttf"
FS = "/usr/share/fonts/truetype/open-sans/OpenSans-Semibold.ttf"
FR = "/usr/share/fonts/truetype/open-sans/OpenSans-Regular.ttf"
_fc = {}


def F(size, w="r"):
    k = (size, w)
    if k not in _fc:
        _fc[k] = ImageFont.truetype({"b": FB, "s": FS, "r": FR}[w], size)
    return _fc[k]


class S:
    def __init__(self):
        self.im = Image.new("RGB", (W, H), BG)
        self.d = ImageDraw.Draw(self.im)
        self.boxes = []

    def mark(self, x0, y0, x1, y1):
        self.boxes.append([int(x0), int(y0), int(x1), int(y1)])

    def text(self, xy, s, size=56, w="r", fill=INK, anchor="la", **kw):
        self.d.text(xy, s, font=F(size, w), fill=fill, anchor=anchor, **kw)

    def para(self, x, y, lines, size=50, w="r", fill=INK, gap=1.35):
        for i, l in enumerate(lines):
            self.text((x, y + i * size * gap), l, size, w, fill)
        return y + len(lines) * size * gap

    def card(self, x, y, w, h, fill=CARD, border=BORDO, r=36, width=6):
        self.d.rounded_rectangle([x, y, x + w, y + h], radius=r, fill=fill, outline=border, width=width)

    def arrow(self, p0, p1, fill=AMBRA, width=16, head=46):
        self.d.line([p0, p1], fill=fill, width=width)
        a = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        for s in (150, -150):
            pass
        pts = [p1, (p1[0] + head * math.cos(a + math.radians(150)), p1[1] + head * math.sin(a + math.radians(150))),
               (p1[0] + head * math.cos(a - math.radians(150)), p1[1] + head * math.sin(a - math.radians(150)))]
        self.d.polygon(pts, fill=fill)

    # ---------------- icone semplici ----------------
    def unita_esterna(self, x, y, w=380, h=280):
        d = self.d
        d.rounded_rectangle([x, y, x + w, y + h], radius=22, fill=(240, 242, 246), outline=(130, 135, 145), width=6)
        r = int(h * 0.36); cx, cy = x + int(w * 0.38), y + h // 2
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(70, 76, 86), outline=(40, 44, 50), width=5)
        for k in range(3):
            a = k * 2 * math.pi / 3 + 0.3
            d.polygon([(cx, cy), (cx + r * .9 * math.cos(a - .35), cy + r * .9 * math.sin(a - .35)), (cx + r * .9 * math.cos(a + .35), cy + r * .9 * math.sin(a + .35))], fill=(160, 166, 176))
        for i in range(6):
            yy = y + int(h * .22) + i * int(h * .1)
            d.line([(x + int(w * .78), yy), (x + int(w * .93), yy)], fill=(150, 155, 165), width=5)

    def split_interno(self, x, y, w=420, h=130):
        d = self.d
        d.rounded_rectangle([x, y, x + w, y + h], radius=40, fill=(250, 250, 252), outline=(140, 145, 155), width=6)
        for i in range(4):
            d.line([(x + 40, y + h - 30 + i * 0), (x + w - 40, y + h - 30)], fill=(170, 175, 185), width=6)
        d.ellipse([x + w - 60, y + 26, x + w - 40, y + 46], fill=VERDE)

    def casa(self, x, y, w=420, h=380, fill=(255, 255, 255)):
        d = self.d
        d.polygon([(x - 20, y + h * .42), (x + w / 2, y), (x + w + 20, y + h * .42)], fill=AMBRA)
        d.rectangle([x, y + h * .4, x + w, y + h], fill=fill, outline=AMBRA, width=8)
        d.rectangle([x + w * .4, y + h * .68, x + w * .6, y + h], fill=AMBRA_L, outline=AMBRA, width=5)
        d.rectangle([x + w * .12, y + h * .52, x + w * .3, y + h * .68], fill=(210, 230, 250), outline=AMBRA, width=5)
        d.rectangle([x + w * .7, y + h * .52, x + w * .88, y + h * .68], fill=(210, 230, 250), outline=AMBRA, width=5)

    def radiatore(self, x, y, w=300, h=150):
        n = 6
        for i in range(n):
            xx = x + i * w / n
            self.d.rounded_rectangle([xx + 5, y, xx + w / n - 5, y + h], radius=14, fill=(250, 250, 250), outline=(170, 170, 170), width=5)
        for i in range(3):
            xx = x + w * (.25 + .25 * i)
            self.d.line([(xx + 10 * math.sin(k / 2), y - 16 - k * 9) for k in range(9)], fill=ROSSO, width=6)

    def pavimento(self, x, y, w=420):
        for i in range(6):
            self.d.line([(x, y + i * 16), (x + w, y + i * 16)], fill=(230, 110, 70) if i % 2 == 0 else (110, 150, 220), width=8)

    def caldaia(self, x, y, w=220, h=320):
        self.d.rounded_rectangle([x, y, x + w, y + h], radius=20, fill=(248, 248, 250), outline=(140, 145, 155), width=6)
        cx, cy = x + w / 2, y + h * .58
        self.d.polygon([(cx, cy - 70), (cx + 40, cy + 10), (cx + 18, cy + 50), (cx - 18, cy + 50), (cx - 40, cy + 10)], fill=(240, 120, 40))
        self.d.polygon([(cx, cy - 20), (cx + 18, cy + 18), (cx, cy + 45), (cx - 18, cy + 18)], fill=(250, 200, 60))

    def fulmine(self, x, y, s=1.0, fill=(245, 200, 30)):
        p = [(0, 0), (-40, 90), (-8, 90), (-28, 170), (30, 65), (-2, 65), (18, 0)]
        self.d.polygon([(x + a * s, y + b * s) for a, b in p], fill=fill, outline=INK)

    def sole(self, x, y, r=60):
        for k in range(12):
            a = k * math.pi / 6
            self.d.line([(x + r * 1.25 * math.cos(a), y + r * 1.25 * math.sin(a)), (x + r * 1.7 * math.cos(a), y + r * 1.7 * math.sin(a))], fill=(245, 180, 30), width=10)
        self.d.ellipse([x - r, y - r, x + r, y + r], fill=(250, 200, 50))

    def ok(self, x, y, r=34):
        self.d.ellipse([x - r, y - r, x + r, y + r], fill=VERDE)
        self.d.line([(x - r * .45, y), (x - r * .1, y + r * .38), (x + r * .5, y - r * .38)], fill=(255, 255, 255), width=9)

    def no(self, x, y, r=34):
        self.d.ellipse([x - r, y - r, x + r, y + r], fill=ROSSO)
        k = r * .4
        self.d.line([(x - k, y - k), (x + k, y + k)], fill=(255, 255, 255), width=9)
        self.d.line([(x - k, y + k), (x + k, y - k)], fill=(255, 255, 255), width=9)

    def assi(self, x0, y0, x1, y1, lx, ly):
        self.d.line([(x0, y1), (x1, y1)], fill=INK, width=6)
        self.d.line([(x0, y1), (x0, y0)], fill=INK, width=6)
        self.text((x1, y1 + 78), lx, 36, "s", MUTED, anchor="ra")
        self.text((x0 - 20, y0 - 20), ly, 42, "s", MUTED, anchor="ls")


# ---------------------------------------------------------------------------
# Episodio 02
# ---------------------------------------------------------------------------
def ep02_tipi():
    s = S()
    rows = [("Aria", "Acqua", "radiatori, pavimento, acqua calda", "la più diffusa nelle case"),
            ("Aria", "Aria", "split nelle stanze", "d'estate raffresca"),
            ("Terreno o falda", "Acqua", "geotermica", "sonde o pozzi")]
    s.text((120, 80), "Prima parola: da dove prende il calore · Seconda: dove lo porta", 56, "s", MUTED)
    for i, (a, b, c, n) in enumerate(rows):
        y = 230 + i * 470
        s.card(120, y, 2340, 400)
        s.card(180, y + 70, 560, 260, fill=(232, 243, 253), border=AZZURRO)
        s.text((460, y + 200), a, 70 if len(a) > 8 else 78, "b", BLU, anchor="mm")
        s.arrow((780, y + 200), (980, y + 200), AMBRA, 22, 60)
        s.card(1020, y + 70, 500, 260, fill=(253, 236, 230), border=(240, 160, 140))
        s.text((1270, y + 200), b, 78, "b", ROSSO, anchor="mm")
        s.text((1590, y + 150), c, 50, "s", INK)
        s.text((1590, y + 230), n, 46, "r", MUTED)
        s.mark(160, y + 50, 2440, y + 350)
    return s


def ep02_terreno():
    s = S()
    x0, y0, x1, y1 = 300, 220, 2300, 1290
    s.assi(x0, y0, x1, y1, "mesi dell'anno", "temperatura")
    mesi = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
    pts_aria, pts_terra = [], []
    for i, m in enumerate(mesi):
        x = x0 + 80 + i * (x1 - x0 - 160) / 11
        s.text((x, y1 + 30), m, 38, "r", MUTED, anchor="ma")
        ta = -math.cos((i) / 11 * 2 * math.pi)  # -1 inverno, +1 estate
        pts_aria.append((x, (y0 + y1) / 2 - ta * 380))
        pts_terra.append((x, (y0 + y1) / 2 - 20))
    s.d.line(pts_aria, fill=BLU, width=14, joint="curve")
    s.d.line(pts_terra, fill=(140, 90, 40), width=14)
    peak = min(pts_aria, key=lambda p: p[1])
    s.text((peak[0], peak[1] - 40), "aria esterna", 54, "b", BLU, anchor="mb")
    s.text(((x0 + x1) / 2, pts_terra[0][1] + 30), "terreno, sotto pochi metri", 54, "b", (140, 90, 40), anchor="ma")
    s.mark(x0 + 40, peak[1] - 120, x1 - 40, pts_aria[0][1] + 60)
    s.mark(x0 + 40, pts_terra[0][1] - 60, x1 - 40, pts_terra[0][1] + 60)
    s.card(420, 1450, 1740, 160, fill=AMBRA_L, border=BORDO)
    s.text((1290, 1530), "Geotermica: resa più costante · costo e permessi maggiori", 56, "s", INK, anchor="mm")
    s.mark(420, 1450, 2160, 1610)
    return s


def ep02_mono_split():
    s = S()
    for k, (tit, sub) in enumerate((("Monoblocco", "verso casa solo tubi d'acqua"), ("Split", "unità esterna e interna"))):
        x = 120 + k * 1200
        s.card(x, 140, 1140, 1440)
        s.text((x + 570, 230), tit, 80, "b", AMBRA, anchor="mm")
        s.text((x + 570, 320), sub, 48, "r", MUTED, anchor="mm")
        s.d.rectangle([x + 540, 420, x + 580, 1250], fill=(170, 120, 90))   # parete
        s.text((x + 270, 1050), "fuori", 44, "s", MUTED, anchor="mm")
        s.text((x + 870, 1050), "dentro", 44, "s", MUTED, anchor="mm")
        s.unita_esterna(x + 80, 620, 400, 300)
        if k == 0:
            s.d.line([(x + 480, 720), (x + 900, 720), (x + 900, 640)], fill=ROSSO, width=18)
            s.d.line([(x + 480, 820), (x + 960, 820), (x + 960, 640)], fill=BLU, width=18)
            s.radiatore(x + 760, 480, 300, 150)
            s.text((x + 680, 900), "acqua", 48, "s", BLU, anchor="ma")
            s.card(x + 60, 1300, 1020, 200, fill=(232, 243, 253), border=AZZURRO)
            s.text((x + 570, 1400), "Attenzione al gelo sui tubi d'acqua", 48, "s", BLU, anchor="mm")
            s.mark(x + 60, 1300, x + 1080, 1500)
        else:
            s.d.line([(x + 480, 740), (x + 760, 740), (x + 760, 560)], fill=(120, 120, 130), width=12)
            s.d.line([(x + 480, 800), (x + 800, 800), (x + 800, 560)], fill=(120, 120, 130), width=12)
            s.split_interno(x + 640, 450, 420, 120)
            s.text((x + 640, 900), "refrigerante", 48, "s", MUTED, anchor="ma")
            s.card(x + 60, 1300, 1020, 200, fill=AMBRA_L, border=BORDO)
            s.text((x + 570, 1400), "Collegamenti frigoriferi: tecnico F-gas", 48, "s", INK, anchor="mm")
            s.mark(x + 60, 1300, x + 1080, 1500)
    s.boxes.insert(0, [120, 140, 1260, 1250]); s.boxes.insert(2, [1320, 140, 2460, 1250])
    return s


def ep02_ibrido():
    s = S()
    s.unita_esterna(200, 420, 420, 320)
    s.text((410, 800), "pompa di calore", 52, "s", INK, anchor="mm")
    s.caldaia(1050, 540, 260, 330)
    s.text((1340, 790), "caldaia a", 46, "s", INK, anchor="lm")
    s.text((1340, 850), "condensazione", 46, "s", INK, anchor="lm")
    s.card(820, 1050, 720, 230, fill=AMBRA_L, border=BORDO)
    s.text((1180, 1130), "Regolazione", 62, "b", AMBRA, anchor="mm")
    s.text((1180, 1210), "decide chi lavora", 46, "r", MUTED, anchor="mm")
    s.arrow((1000, 1050), (560, 760), AMBRA, 12, 40)
    s.arrow((1180, 1050), (1180, 890), AMBRA, 12, 40)
    s.radiatore(1900, 520, 360, 170)
    s.text((2080, 800), "impianto", 52, "s", INK, anchor="mm")
    s.d.line([(640, 520), (700, 470), (1860, 470)], fill=ROSSO, width=14)
    s.arrow((1700, 470), (1880, 560), ROSSO, 14, 44)
    s.arrow((1330, 700), (1880, 650), ROSSO, 14, 44)
    s.mark(180, 400, 660, 840); s.mark(1020, 520, 1680, 900); s.mark(820, 1050, 1540, 1280)
    s.card(300, 1380, 1980, 160, fill=CARD)
    s.text((1290, 1460), "La pompa di calore lavora quasi sempre · la caldaia quando fa molto freddo", 50, "s", INK, anchor="mm")
    return s


# ---------------------------------------------------------------------------
# Episodio 03
# ---------------------------------------------------------------------------
def ep03_cop():
    s = S()
    s.card(200, 360, 700, 700, fill=(255, 250, 225), border=(245, 200, 30))
    s.fulmine(560, 480, 2.0)
    s.text((550, 940), "1 kWh elettrico", 64, "b", INK, anchor="mm")
    s.arrow((960, 710), (1420, 710), AMBRA, 26, 70)
    s.card(1480, 260, 900, 900, fill=(253, 236, 230), border=(240, 160, 140))
    for k in range(4):
        s.d.rounded_rectangle([1560 + k * 200, 520, 1720 + k * 200, 920], radius=20, fill=ROSSO)
    s.text((1930, 400), "esempio: 4 kWh di calore", 64, "b", ROSSO, anchor="mm")
    s.text((1930, 1040), "COP = calore dato ÷ energia elettrica", 52, "s", INK, anchor="mm")
    s.mark(200, 360, 900, 1060); s.mark(1480, 260, 2380, 1160)
    s.card(300, 1290, 1980, 230, fill=AMBRA_L, border=BORDO)
    s.text((1290, 1360), "Vale in una condizione precisa:", 52, "s", INK, anchor="mm")
    s.text((1290, 1440), "temperatura dell'aria fuori e dell'acqua in uscita", 52, "s", INK, anchor="mm")
    s.mark(300, 1290, 2280, 1520)
    return s


def ep03_scop():
    s = S()
    x0, y0, x1, y1 = 300, 260, 2300, 1300
    s.assi(x0, y0, x1, y1, "mesi di riscaldamento", "COP del giorno")
    mesi = ["ott", "nov", "dic", "gen", "feb", "mar", "apr"]
    vals = [0.85, 0.6, 0.42, 0.35, 0.45, 0.65, 0.88]
    bw = (x1 - x0 - 200) / len(mesi)
    for i, (m, v) in enumerate(zip(mesi, vals)):
        x = x0 + 100 + i * bw
        top = y1 - v * (y1 - y0 - 80)
        s.d.rounded_rectangle([x + 30, top, x + bw - 30, y1 - 4], radius=16, fill=AZZURRO if v > 0.5 else BLU)
        s.text((x + bw / 2, y1 + 30), m, 42, "r", MUTED, anchor="ma")
    avg = y1 - (sum(vals) / len(vals)) * (y1 - y0 - 80)
    s.d.line([(x0, avg), (x1, avg)], fill=AMBRA, width=10)
    s.card(x1 - 960, y0 - 40, 940, 110, fill=CARD, border=AMBRA)
    s.text((x1 - 490, y0 + 15), "linea: SCOP, la media della stagione", 50, "b", AMBRA, anchor="mm")
    s.text((x0 + 40, 150), "Esempio illustrativo: nei mesi freddi il COP scende", 50, "s", MUTED, anchor="lm")
    s.mark(x0 + 100 + 2 * bw, y0 + 300, x0 + 100 + 5 * bw, y1); s.mark(x0, avg - 70, x1, avg + 30)
    s.card(400, 1430, 1780, 150, fill=AMBRA_L, border=BORDO)
    s.text((1290, 1505), "Cambia con la zona climatica e con la temperatura di mandata", 50, "s", INK, anchor="mm")
    s.mark(400, 1430, 2180, 1580)
    return s


def ep03_mandata():
    s = S()
    def colonna(x, titolo, t_acqua, alto, colore, nota):
        s.card(x, 160, 1080, 1380)
        s.text((x + 540, 240), titolo, 66, "b", AMBRA, anchor="mm")
        base = 1250
        s.d.rectangle([x + 200, base - 150, x + 380, base], fill=AZZURRO)
        s.text((x + 290, base + 40), "aria fuori", 44, "s", BLU, anchor="mm")
        s.d.rectangle([x + 700, base - alto, x + 880, base], fill=colore)
        s.text((x + 790, base + 40), t_acqua, 44, "s", colore, anchor="mm")
        s.d.line([(x + 470, base - 150), (x + 470, base - alto)], fill=INK, width=8)
        s.arrow((x + 470, base - alto + 60), (x + 470, base - alto), INK, 8, 30)
        s.arrow((x + 470, base - 210), (x + 470, base - 150), INK, 8, 30)
        s.text((x + 500, (2 * base - 150 - alto) / 2), "differenza", 44, "s", INK, anchor="lm")
        s.text((x + 540, 1440), nota, 48, "s", INK, anchor="mm")
        return (x + 150, base - alto - 40, x + 930, base)
    b1 = colonna(120, "Pavimento radiante", "acqua tiepida", 420, (240, 140, 60), "differenza piccola: rende di più")
    b2 = colonna(1380, "Radiatori", "acqua più calda", 820, ROSSO, "differenza grande: rende meno")
    s.mark(*b1); s.mark(*b2)
    return s


def ep03_curva():
    s = S()
    x0, y0, x1, y1 = 360, 220, 2280, 1300
    s.assi(x0, y0, x1, y1, "temperatura esterna: più fredda a sinistra, più mite a destra", "temperatura di mandata")
    pts = [(x0 + 60, y0 + 120), (x1 - 60, y1 - 160)]
    s.d.line(pts, fill=ROSSO, width=16)
    s.d.ellipse([pts[0][0] - 24, pts[0][1] - 24, pts[0][0] + 24, pts[0][1] + 24], fill=ROSSO)
    s.d.ellipse([pts[1][0] - 24, pts[1][1] - 24, pts[1][0] + 24, pts[1][1] + 24], fill=ROSSO)
    s.text((pts[0][0] + 50, pts[0][1] - 20), "fuori fa freddo: mandata più alta", 52, "s", INK, anchor="ls")
    s.text((pts[1][0] - 60, pts[1][1] + 40), "mezza stagione: mandata più bassa", 52, "s", INK, anchor="ra")
    s.mark(pts[0][0] - 50, pts[0][1] - 90, pts[0][0] + 950, pts[0][1] + 50)
    s.mark(pts[1][0] - 1000, pts[1][1] - 40, pts[1][0] + 50, pts[1][1] + 120)
    s.card(400, 1420, 1780, 160, fill=AMBRA_L, border=BORDO)
    s.text((1290, 1500), "Impostala il più bassa possibile, mantenendo il comfort", 52, "s", INK, anchor="mm")
    s.mark(400, 1420, 2180, 1580)
    return s


# ---------------------------------------------------------------------------
# Episodio 04
# ---------------------------------------------------------------------------
def ep04_casa():
    s = S()
    s.casa(820, 300, 900, 820)
    for (p0, p1, lab, side) in (((820, 860), (520, 860), "muri", "r"), ((1720, 860), (2020, 860), "serramenti", "l"),
                                ((1270, 330), (1270, 140), "tetto", "m"), ((1500, 1120), (1800, 1300), "ricambi d'aria", "l")):
        s.arrow(p0, p1, ROSSO, 18, 50)
        anchor = {"r": "rm", "l": "lm", "m": "mb"}[side]
        s.text((p1[0] + (-20 if side == "r" else 20 if side == "l" else 0), p1[1] - (20 if side == "m" else 0)), lab, 56, "b", ROSSO, anchor=anchor)
    s.text((120, 140), "Calore perso nella giornata", 50, "s", MUTED)
    s.text((120, 210), "più fredda di progetto", 50, "s", MUTED)
    s.mark(780, 260, 1760, 1140)
    s.card(300, 1400, 1980, 180, fill=AMBRA_L, border=BORDO)
    s.text((1290, 1490), "Si parte dal fabbisogno dell'edificio, non dalla vecchia caldaia", 52, "s", INK, anchor="mm")
    s.mark(300, 1400, 2280, 1580)
    return s


def _grafico_bivalenza(s, highlight_integrazione=False):
    x0, y0, x1, y1 = 320, 200, 2300, 1280
    s.assi(x0, y0, x1, y1, "temperatura esterna: più fredda a sinistra, più mite a destra", "potenza")
    pdc = [(x0 + 40, y0 + 620), (x1 - 40, y0 + 120)]      # la potenza della pdc cresce con l'aria più mite
    fab = [(x0 + 40, y0 + 140), (x1 - 40, y1 - 120)]      # il fabbisogno cala con l'aria più mite
    s.d.line(pdc, fill=BLU, width=16)
    s.d.line(fab, fill=ROSSO, width=16)
    s.text((x1 - 60, pdc[1][1] - 30), "potenza della pompa di calore", 50, "b", BLU, anchor="rs")
    s.text((x0 + 80, fab[0][1] - 40), "fabbisogno della casa", 50, "b", ROSSO, anchor="ls")
    # intersezione
    def inter(a, b):
        (x1a, y1a), (x2a, y2a) = a; (x1b, y1b), (x2b, y2b) = b
        ma = (y2a - y1a) / (x2a - x1a); mb = (y2b - y1b) / (x2b - x1b)
        x = (y1b - y1a + ma * x1a - mb * x1b) / (ma - mb)
        return x, y1a + ma * (x - x1a)
    bx, by = inter(pdc, fab)
    s.d.ellipse([bx - 28, by - 28, bx + 28, by + 28], fill=AMBRA)
    s.d.line([(bx, by), (bx, y1)], fill=AMBRA, width=6)
    s.text((bx, y1 + 14), "punto di bivalenza", 50, "b", AMBRA, anchor="ma")
    if highlight_integrazione:
        s.d.polygon([(x0 + 40, pdc[0][1]), (x0 + 40, fab[0][1]), (bx, by)], fill=(250, 215, 200))
        s.d.line(pdc, fill=BLU, width=16); s.d.line(fab, fill=ROSSO, width=16)
        s.text((x0 + 80, (pdc[0][1] + fab[0][1]) / 2 + 10), "serve integrazione", 50, "b", ROSSO, anchor="lm")
    return (bx, by), (x0, y0, x1, y1), pdc, fab


def ep04_potenza():
    s = S()
    (bx, by), (x0, y0, x1, y1), pdc, fab = _grafico_bivalenza(s)
    s.mark(x0 + 20, pdc[0][1] - 80, x0 + 600, pdc[0][1] + 60)
    s.card(420, 1450, 1740, 150, fill=AMBRA_L, border=BORDO)
    s.text((1290, 1525), "Guarda la potenza alla temperatura di progetto, non solo quella nominale", 48, "s", INK, anchor="mm")
    s.mark(420, 1450, 2160, 1600)
    return s


def ep04_bivalenza():
    s = S()
    (bx, by), (x0, y0, x1, y1), pdc, fab = _grafico_bivalenza(s, True)
    s.mark(bx - 90, by - 90, bx + 90, by + 90)
    s.mark(x0 + 20, fab[0][1] - 30, bx, pdc[0][1] + 40)
    s.card(420, 1450, 1740, 150, fill=AMBRA_L, border=BORDO)
    s.text((1290, 1525), "Sotto la bivalenza aiuta la resistenza elettrica o la caldaia (ibrido)", 48, "s", INK, anchor="mm")
    s.mark(420, 1450, 2160, 1600)
    return s


def ep04_taglia():
    s = S()
    for k, (tit, col, cicli, nota) in enumerate((("Troppo grande", ROSSO, True, "si accende e si spegne di continuo"),
                                                  ("Troppo piccola", BLU, False, "la resistenza lavora sempre"))):
        y = 160 + k * 720
        s.card(120, y, 2340, 640)
        s.text((200, y + 70), tit, 72, "b", col)
        s.text((200, y + 160), nota, 50, "r", MUTED)
        x0 = 1000
        if cicli:
            xs = x0
            for i in range(9):
                s.d.rectangle([xs, y + 260, xs + 70, y + 520], fill=col)
                xs += 150
            s.text((x0, y + 570), "acceso · spento · acceso · spento …", 44, "s", MUTED)
        else:
            s.d.rectangle([x0, y + 300, x0 + 1300, y + 520], fill=AZZURRO)
            s.d.rectangle([x0, y + 220, x0 + 1300, y + 300], fill=ROSSO)
            s.text((x0 + 650, y + 260), "resistenza elettrica", 44, "b", (255, 255, 255), anchor="mm")
            s.text((x0, y + 570), "pompa di calore sempre al massimo", 44, "s", MUTED)
        s.mark(120, y, 2460, y + 640)
    return s


def ep04_acs():
    s = S()
    s.d.rounded_rectangle([1050, 260, 1530, 1220], radius=120, fill=(232, 236, 242), outline=(140, 145, 155), width=8)
    s.d.rectangle([1060, 300, 1520, 640], fill=(250, 210, 200))
    s.text((1290, 1290), "accumulo", 56, "b", INK, anchor="mm")
    s.card(160, 360, 760, 560)
    s.text((540, 450), "Quante persone", 60, "b", AMBRA, anchor="mm")
    s.text((540, 540), "e come usano", 52, "s", INK, anchor="mm")
    s.text((540, 610), "l'acqua calda", 52, "s", INK, anchor="mm")
    for i in range(4):
        cx = 330 + i * 110
        s.d.ellipse([cx - 30, 700, cx + 30, 760], fill=AMBRA)
        s.d.rounded_rectangle([cx - 45, 770, cx + 45, 880], radius=30, fill=AMBRA)
    s.card(1660, 360, 760, 560, fill=(253, 236, 230), border=(240, 160, 140))
    s.text((2040, 450), "Ciclo antilegionella", 56, "b", ROSSO, anchor="mm")
    s.para(1740, 560, ["ogni tanto scalda", "l'accumulo a una", "temperatura più alta"], 50, "s", INK)
    s.mark(160, 360, 920, 920); s.mark(1030, 240, 1550, 1320); s.mark(1660, 360, 2420, 920)
    return s


# ---------------------------------------------------------------------------
# Episodio 05
# ---------------------------------------------------------------------------
def ep05_esterna():
    s = S()
    s.d.rectangle([150, 160, 230, 1500], fill=(170, 120, 90))
    s.text((190, 130), "parete", 44, "s", MUTED, anchor="mb")
    s.unita_esterna(520, 560, 620, 460)
    s.arrow((420, 790), (250, 790), AMBRA, 12, 36); s.arrow((300, 790), (500, 790), AMBRA, 12, 36)
    s.arrow((1160, 790), (1500, 790), AMBRA, 12, 36); s.arrow((1480, 790), (1160, 790), AMBRA, 12, 36)
    s.text((1180, 740), "spazi del costruttore", 46, "s", AMBRA, anchor="lb")
    for xx in (600, 1040):
        s.d.rectangle([xx, 1020, xx + 60, 1110], fill=(60, 60, 60))
    s.d.rectangle([480, 1110, 1180, 1170], fill=(160, 160, 160))
    s.text((830, 1230), "supporti antivibranti · base rialzata dove nevica", 46, "s", INK, anchor="ma")
    s.card(1700, 220, 760, 420, fill=(253, 236, 230), border=(240, 160, 140))
    s.no(1790, 320)
    s.text((1850, 320), "Niente nicchie chiuse", 50, "b", ROSSO, anchor="lm")
    s.para(1760, 410, ["riaspira l'aria fredda", "che ha appena espulso"], 46, "s", INK)
    s.card(1700, 760, 760, 420, fill=AMBRA_L, border=BORDO)
    s.text((1760, 860), "Rumore", 54, "b", AMBRA, anchor="lm")
    s.para(1760, 950, ["attenzione alle finestre", "dei vicini"], 46, "s", INK)
    s.mark(250, 520, 1500, 1060); s.mark(1700, 220, 2460, 640); s.mark(1700, 760, 2460, 1180); s.mark(480, 1000, 1180, 1290)
    return s


def ep05_condensa():
    s = S()
    for k, (ok_, tit, nota) in enumerate(((True, "Scarico collegato", "l'acqua dello sbrinamento va in uno scarico"),
                                           (False, "Su un passaggio", "di notte diventa ghiaccio"))):
        x = 120 + k * 1200
        s.card(x, 140, 1140, 1400)
        (s.ok if ok_ else s.no)(x + 120, 250, 44)
        s.text((x + 190, 250), tit, 64, "b", VERDE if ok_ else ROSSO, anchor="lm")
        s.unita_esterna(x + 330, 420, 480, 360)
        for i in range(5):
            s.d.ellipse([x + 540 + (i % 2) * 40, 820 + i * 50, x + 570 + (i % 2) * 40, 860 + i * 50], fill=AZZURRO)
        if ok_:
            s.d.line([(x + 570, 800), (x + 570, 1150), (x + 900, 1150)], fill=GRIGIO, width=22)
            s.d.rectangle([x + 880, 1120, x + 980, 1220], fill=(110, 110, 120))
        else:
            s.d.rectangle([x + 200, 1150, x + 1000, 1210], fill=(205, 225, 245))
            s.text((x + 600, 1270), "ghiaccio", 50, "b", BLU, anchor="mm")
        s.text((x + 570, 1430), nota, 46, "s", INK, anchor="mm")
        s.mark(x, 140, x + 1140, 1540)
    return s


def ep05_idraulica():
    s = S()
    items = [("pompa di calore", 140), ("defangatore\nmagnetico e filtro", 640), ("accumulo inerziale", 1140), ("vaso d'espansione", 1640), ("impianto", 2140)]
    y = 620
    s.d.line([(300, y), (2300, y)], fill=ROSSO, width=20)
    s.d.line([(300, y + 120), (2300, y + 120)], fill=BLU, width=20)
    s.unita_esterna(130, 470, 340, 270)
    s.d.rounded_rectangle([700, 540, 860, 820], radius=30, fill=(90, 95, 105)); s.d.ellipse([730, 560, 830, 660], fill=(200, 60, 50))
    s.d.rounded_rectangle([1160, 380, 1420, 900], radius=90, fill=(232, 236, 242), outline=(140, 145, 155), width=8)
    s.d.ellipse([1680, 820, 1860, 1000], fill=ROSSO); s.d.line([(1770, 740), (1770, 820)], fill=GRIGIO, width=16)
    s.radiatore(2100, 400, 300, 160)
    labels = ["pompa di calore", "defangatore e filtro", "accumulo inerziale", "vaso d'espansione", "impianto"]
    xs = [300, 780, 1290, 1770, 2250]
    boxes = [(130, 450, 480, 760), (680, 520, 880, 840), (1140, 360, 1440, 920), (1660, 720, 1880, 1020), (2080, 330, 2420, 580)]
    for lab, x in zip(labels, xs):
        s.text((x, 1120), lab, 46, "s", INK, anchor="mm")
    s.d.line([(300, y), (300, 740)], fill=ROSSO, width=0)
    for b in boxes[1:4]:
        s.mark(*b)
    s.card(300, 1250, 1980, 280, fill=AMBRA_L, border=BORDO)
    s.text((1290, 1330), "Volume d'acqua sufficiente: sbrinamenti e cicli non troppo brevi", 48, "s", INK, anchor="mm")
    s.text((1290, 1430), "Tubi ben isolati", 48, "s", INK, anchor="mm")
    s.mark(300, 1250, 2280, 1530)
    return s


def ep05_tre():
    s = S()
    cards = [("Antigelo", BLU, ["monoblocco: tubi d'acqua", "all'esterno protetti", "con glicole o dispositivi", "antigelo"]),
             ("Elettrico", (200, 150, 0), ["linea dedicata", "contatore con la", "potenza adatta"]),
             ("F-gas", ROSSO, ["split: collegamenti", "frigoriferi solo con", "certificazione F-gas"])]
    for i, (t, c, lines) in enumerate(cards):
        x = 120 + i * 790
        s.card(x, 240, 740, 1200)
        s.text((x + 370, 360), t, 76, "b", c, anchor="mm")
        if i == 0:
            s.d.ellipse([x + 290, 470, x + 450, 630], outline=c, width=12)
            for a in range(6):
                ang = a * math.pi / 3
                s.d.line([(x + 370, 550), (x + 370 + 70 * math.cos(ang), 550 + 70 * math.sin(ang))], fill=c, width=8)
        elif i == 1:
            s.fulmine(x + 380, 450, 1.1)
        else:
            s.d.rounded_rectangle([x + 260, 470, x + 480, 640], radius=24, outline=c, width=12)
            s.text((x + 370, 555), "F-gas", 48, "b", c, anchor="mm")
        s.para(x + 70, 760, lines, 50, "s", INK)
        s.mark(x, 240, x + 740, 1440)
    return s


def ep05_messa():
    s = S()
    voci = ["curva climatica e parametri impostati", "sbrinamento: lo scarico funziona", "spiegata al cliente la regolazione"]
    s.text((1290, 200), "Messa in servizio", 80, "b", AMBRA, anchor="mm")
    for i, v in enumerate(voci):
        y = 380 + i * 360
        s.card(300, y, 1980, 290)
        s.ok(450, y + 145, 54)
        s.text((560, y + 145), v, 62, "s", INK, anchor="lm")
        s.mark(300, y, 2280, y + 290)
    return s


# ---------------------------------------------------------------------------
# Episodio 06
# ---------------------------------------------------------------------------
def ep06_regolazione():
    s = S()
    for k, (tit, col, costante) in enumerate((("Temperatura costante", VERDE, True), ("Spegni e riaccendi", ROSSO, False))):
        y = 160 + k * 640
        s.card(120, y, 2340, 580)
        (s.ok if costante else s.no)(220, y + 90, 40)
        s.text((290, y + 90), tit, 64, "b", col, anchor="lm")
        x0, x1, base = 300, 2300, y + 500
        if costante:
            s.d.line([(x0, base - 220), (x1, base - 220)], fill=col, width=14)
        else:
            pts = []
            for i in range(9):
                xa = x0 + i * (x1 - x0) / 8
                pts.append((xa, base - (300 if i % 2 else 60)))
            s.d.line(pts, fill=col, width=14)
        s.mark(120, y, 2460, y + 580)
    s.card(300, 1450, 1980, 150, fill=AMBRA_L, border=BORDO)
    s.text((1290, 1525), "Curva climatica bassa · acqua sanitaria non più calda del necessario", 48, "s", INK, anchor="mm")
    s.mark(300, 1450, 2280, 1600)
    return s


def ep06_fv():
    s = S()
    x0, y0, x1, y1 = 300, 260, 2300, 1260
    s.assi(x0, y0, x1, y1, "ore del giorno", "produzione dei pannelli")
    pts = [(x0 + i * (x1 - x0) / 60, y1 - max(0, math.sin((i / 60) * math.pi)) * 820) for i in range(61)]
    s.d.polygon([(x0, y1)] + pts + [(x1, y1)], fill=(253, 230, 170))
    s.d.line(pts, fill=(230, 160, 20), width=12)
    s.sole(1300, 300, 50)
    s.d.rectangle([1050, y1 - 260, 1550, y1 - 40], fill=ROSSO)
    s.text((1300, y1 - 150), "acqua calda sanitaria", 46, "b", (255, 255, 255), anchor="mm")
    for i, h in enumerate(("6", "9", "12", "15", "18", "21")):
        s.text((x0 + (i + 1) * (x1 - x0) / 7, y1 + 30), h, 42, "r", MUTED, anchor="ma")
    s.mark(1030, y1 - 280, 1570, y1 - 20)
    s.card(300, 1400, 1980, 180, fill=AMBRA_L, border=BORDO)
    s.text((1290, 1490), "Fai lavorare la pompa di calore quando i pannelli producono", 52, "s", INK, anchor="mm")
    s.mark(300, 1400, 2280, 1580)
    return s


def ep06_manutenzione():
    s = S()
    voci = ["batteria esterna pulita", "scarico della condensa libero", "filtro dell'impianto pulito",
            "pressione dell'impianto giusta", "glicole verificato, dove c'è", "controlli F-gas previsti per la macchina"]
    for i, v in enumerate(voci):
        col, row = i % 2, i // 2
        x, y = 120 + col * 1190, 180 + row * 470
        s.card(x, y, 1150, 400)
        s.ok(x + 110, y + 200, 50)
        s.text((x + 200, y + 200), v, 56, "s", INK, anchor="lm")
        s.mark(x, y, x + 1150, y + 400)
    return s


def ep06_errori():
    s = S()
    err = ["macchina sovradimensionata", "acqua di mandata troppo calda", "unità esterna soffocata", "filtro intasato", "volume d'acqua troppo piccolo"]
    for i, e in enumerate(err):
        y = 140 + i * 300
        s.card(220, y, 2140, 250, fill=(253, 240, 236), border=(240, 160, 140))
        s.no(340, y + 125, 50)
        s.text((440, y + 125), f"{i + 1}. {e}", 62, "s", INK, anchor="lm")
        s.mark(220, y, 2360, y + 250)
    return s


SCHEMI = {
    "pdc-02-tipi": ep02_tipi, "pdc-02-terreno": ep02_terreno, "pdc-02-monoblocco-split": ep02_mono_split, "pdc-02-ibrido": ep02_ibrido,
    "pdc-03-cop": ep03_cop, "pdc-03-scop": ep03_scop, "pdc-03-mandata": ep03_mandata, "pdc-03-curva": ep03_curva,
    "pdc-04-casa": ep04_casa, "pdc-04-potenza": ep04_potenza, "pdc-04-bivalenza": ep04_bivalenza, "pdc-04-taglia": ep04_taglia, "pdc-04-acs": ep04_acs,
    "pdc-05-esterna": ep05_esterna, "pdc-05-condensa": ep05_condensa, "pdc-05-idraulica": ep05_idraulica, "pdc-05-tre": ep05_tre, "pdc-05-messa": ep05_messa,
    "pdc-06-regolazione": ep06_regolazione, "pdc-06-fv": ep06_fv, "pdc-06-manutenzione": ep06_manutenzione, "pdc-06-errori": ep06_errori,
}


def genera(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    ev = {}
    for name, fn in SCHEMI.items():
        s = fn()
        s.im.save(out / f"{name}.png")
        ev[name] = s.boxes
    (out / "riquadri.json").write_text(json.dumps(ev, indent=1))
    return ev


if __name__ == "__main__":
    genera(Path(sys.argv[1]))
