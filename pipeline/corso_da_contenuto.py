#!/usr/bin/env python3
"""Costruisce il "pacchetto" di un corso scritto da noi (senza pacchetto dello sviluppo):
schemi grafici + Slide_*.pptx + Storyboard_Animazione.xlsx, nello stesso formato dei pacchetti
delle app, così il montaggio usa course_render.py con la regia a tutto schermo.

  CORSO=tatano-commerciale python3 pipeline/corso_da_contenuto.py

Ingresso: corsi/<CORSO>/materiale/contenuto.json (testi e schemi; resta fuori da git perché
contiene materiale aziendale). Gli schemi sono disegnati qui da codice: le scritte vengono
solo dal contenuto, niente testo inventato da modelli generativi.
"""
import json
import math
import os
import sys
from pathlib import Path

import openpyxl
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Emu

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corso_pdc import add_rect, add_text  # noqa: E402
from allinea import completa, posizioni  # noqa: E402
from schemi_pdc import (AMBRA, AMBRA_L, BG, BLU, BORDO, CARD, F, GRIGIO, H, INK, MUTED, ROSSO, VERDE, W, S)  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
NOME = os.environ.get("CORSO", "tatano-commerciale")
MAT = ROOT / "corsi" / NOME / "materiale"
ASSET = MAT / "Asset_Grafici"
SW, SH = 12191695, 6858000
COLORI = {"ambra": AMBRA, "rosso": ROSSO, "verde": VERDE, "blu": BLU, "grigio": GRIGIO, "ink": INK}
FONDI = {"ambra": (255, 248, 232), "rosso": (253, 236, 234), "verde": (232, 246, 236), "blu": (232, 241, 252), "grigio": (243, 243, 245), "ink": CARD}


# ---------------------------------------------------------------------------
# testo
# ---------------------------------------------------------------------------
def wrap(text, size, w, maxw):
    font = F(size, w)
    out = []
    for par in str(text).split("\n"):
        line = ""
        for word in par.split():
            prova = (line + " " + word).strip()
            if font.getlength(prova) <= maxw or not line:
                line = prova
            else:
                out.append(line)
                line = word
        out.append(line)
    return out


def blocco(s, x, y, text, size, w, fill, maxw, gap=1.28):
    for i, l in enumerate(wrap(text, size, w, maxw)):
        s.text((x, y + i * size * gap), l, size, w, fill)
    return y + len(wrap(text, size, w, maxw)) * size * gap


def h_blocco(text, size, w, maxw, gap=1.28):
    return len(wrap(text, size, w, maxw)) * size * gap


def intestazione(s, sch):
    """Titolo dello schema (facoltativo) in alto; ritorna la y da cui partire."""
    if sch.get("titolo"):  # più in basso: in alto a sinistra, a tutto schermo, c'è la fascia col titolo della scena
        s.text((110, 175), sch["titolo"], 74, "b", AMBRA)
        y = 290
        if sch.get("sottotitolo"):
            y = blocco(s, 110, y, sch["sottotitolo"], 46, "r", MUTED, W - 220) + 20
        return y + 20
    return 170


def nota(s, sch):
    if sch.get("nota"):
        t = sch["nota"]
        hh = h_blocco(t, 40, "r", W - 300) + 50
        s.card(110, H - 70 - hh, W - 220, hh, fill=(255, 250, 236), border=BORDO, r=26, width=4)
        blocco(s, 150, H - 70 - hh + 22, t, 40, "r", MUTED, W - 300)
        return H - 70 - hh - 30
    return H - 80


# ---------------------------------------------------------------------------
# tipi di schema
# ---------------------------------------------------------------------------
def sch_copertina(s, sch):
    s.text((W / 2, 300), sch.get("marchio", ""), 60, "s", MUTED, anchor="mm")
    y = 420
    for l in wrap(sch["titolo"], 120, "b", W - 300):
        s.text((W / 2, y), l, 120, "b", AMBRA, anchor="mm"); y += 150
    y = y + 10
    for l in wrap(sch.get("sottotitolo", ""), 58, "r", W - 500):
        s.text((W / 2, y), l, 58, "r", INK, anchor="mm"); y += 76
    punti = sch.get("punti", [])
    if punti:
        n = len(punti); gap = 50; cw = (W - 260 - gap * (n - 1)) / n; ch = 380; cy = H - ch - 150
        for i, p in enumerate(punti):
            cx = 130 + i * (cw + gap)
            s.card(cx, cy, cw, ch)
            s.d.ellipse([cx + cw / 2 - 52, cy + 40, cx + cw / 2 + 52, cy + 144], fill=AMBRA)
            s.text((cx + cw / 2, cy + 92), str(i + 1), 64, "b", (255, 255, 255), anchor="mm")
            yy = cy + 180
            for l in wrap(p, 48, "s", cw - 80):
                s.text((cx + cw / 2, yy), l, 48, "s", INK, anchor="ma"); yy += 62
            s.mark(cx, cy, cx + cw, cy + ch)


def sch_schede(s, sch):
    """Fino a 8 schede in griglia: [titolo, testo, colore?]."""
    y0 = intestazione(s, sch)
    y1 = nota(s, sch)
    voci = sch["voci"]
    n = len(voci)
    cols = sch.get("colonne") or (1 if n <= 3 and sch.get("righe_lunghe") else (2 if n <= 6 else 3))
    if n <= 3 and not sch.get("righe_lunghe") and not sch.get("colonne"):
        cols = n
    rows = math.ceil(n / cols)
    gap = 40
    cw = (W - 220 - gap * (cols - 1)) / cols
    ch = (y1 - y0 - gap * (rows - 1)) / rows
    for i, v in enumerate(voci):
        tit, txt = v[0], v[1] if len(v) > 1 else ""
        col = COLORI.get(v[2] if len(v) > 2 else "ambra", AMBRA)
        r, c = divmod(i, cols)
        x = 110 + c * (cw + gap); y = y0 + r * (ch + gap)
        s.card(x, y, cw, ch, fill=FONDI.get(v[2] if len(v) > 2 else "ink", CARD), border=col if len(v) > 2 else BORDO)
        s.d.rounded_rectangle([x, y, x + 22, y + ch], radius=10, fill=col)
        # dimensione del testo che entra nella scheda
        for ts in (84, 78, 72, 66, 60, 56, 52, 48, 44, 40):
            hs = ts * 0.82
            need = h_blocco(tit, ts, "b", cw - 120) + (h_blocco(txt, hs, "r", cw - 120) + 14 if txt else 0)
            if need <= ch - 60:
                break
        yy = y + max(30, (ch - need) / 2)
        yy = blocco(s, x + 70, yy, tit, ts, "b", INK, cw - 120)
        if txt:
            blocco(s, x + 70, yy + 14, txt, hs, "r", MUTED, cw - 120)
        s.mark(x, y, x + cw, y + ch)


def sch_tabella(s, sch):
    """Tabella: colonne, righe; 'gruppi' = liste di indici di riga da evidenziare insieme."""
    y0 = intestazione(s, sch)
    y1 = nota(s, sch)
    cols = sch["colonne"]
    pesi = sch.get("pesi") or [1] * len(cols)
    tw = W - 220
    xs = [110]
    for p in pesi:
        xs.append(xs[-1] + tw * p / sum(pesi))
    righe = sch["righe"]

    def alt_tot(sz):
        return sum(max(h_blocco(str(cell), sz, "b" if i == 0 else "r", xs[i + 1] - xs[i] - 60) for i, cell in enumerate(r)) + sz * 1.1 for r in righe) + 110
    size = 74
    while alt_tot(size) > y1 - y0 and size > 30:
        size -= 2
    hh = 100
    s.d.rounded_rectangle([110, y0, W - 110, y0 + hh], radius=20, fill=AMBRA)
    for i, c in enumerate(cols):
        s.text((xs[i] + 30, y0 + hh / 2), c, min(size, 54), "b", (255, 255, 255), anchor="lm")
    y = y0 + hh + 10
    alt = []
    for k, r in enumerate(righe):
        hr = max(h_blocco(str(cell), size, "b" if i == 0 else "r", xs[i + 1] - xs[i] - 60) for i, cell in enumerate(r)) + size * 1.1
        alt.append((y, y + hr))
        s.d.rectangle([110, y, W - 110, y + hr], fill=CARD if k % 2 == 0 else (250, 245, 235))
        for i, cell in enumerate(r):
            blocco(s, xs[i] + 30, y + size * .55, str(cell), size, "b" if i == 0 else "r", INK if i == 0 else (60, 52, 40), xs[i + 1] - xs[i] - 60)
        y += hr
    s.d.rounded_rectangle([110, y0, W - 110, y], radius=20, outline=BORDO, width=5)
    for g in sch.get("gruppi") or [[k] for k in range(len(righe))]:
        s.mark(110, alt[g[0]][0], W - 110, alt[g[-1]][1])


def sch_barre(s, sch):
    y0 = intestazione(s, sch)
    y1 = nota(s, sch)
    voci = sch["voci"]
    vmax = max(v[1] for v in voci)
    n = len(voci)
    lw = 620
    bh = min(170, (y1 - y0 - 40) / n - 40)
    for i, v in enumerate(voci):
        y = y0 + 40 + i * (bh + 40)
        col = COLORI.get(v[2] if len(v) > 2 else "ambra", AMBRA)
        s.text((110, y + bh / 2), v[0], 58, "b", INK, anchor="lm")
        L = (W - 110 - lw - 420) * v[1] / vmax
        s.d.rounded_rectangle([lw, y, lw + max(L, 30), y + bh], radius=18, fill=col)
        s.text((lw + max(L, 30) + 30, y + bh / 2), v[3] if len(v) > 3 else f"{v[1]}", 58, "b", col, anchor="lm")
        s.mark(100, y - 10, W - 110, y + bh + 10)


def sch_due(s, sch):
    y0 = intestazione(s, sch)
    y1 = nota(s, sch)
    gap = 60; cw = (W - 220 - gap) / 2
    for k, lato in enumerate(("sx", "dx")):
        c = sch[lato]
        col = COLORI.get(c.get("colore", "ambra"))
        x = 110 + k * (cw + gap)
        s.card(x, y0, cw, y1 - y0, fill=FONDI.get(c.get("colore", "ambra")), border=col)
        s.d.rounded_rectangle([x, y0, x + cw, y0 + 120], radius=36, fill=col)
        s.text((x + cw / 2, y0 + 60), c["titolo"], 58, "b", (255, 255, 255), anchor="mm")
        yy = y0 + 170
        size = 72
        while sum(h_blocco(v, size, "r", cw - 160) + 26 for v in c["voci"]) > y1 - y0 - 220 and size > 34:
            size -= 2
        for v in c["voci"]:
            y_start = yy
            s.d.ellipse([x + 50, yy + 12, x + 82, yy + 44], fill=col)
            yy = blocco(s, x + 110, yy, v, size, "r", INK, cw - 160) + 26
        s.mark(x, y0, x + cw, y1)


def sch_lista(s, sch):
    """Elenco numerato verticale (passi o regole), una evidenza per voce."""
    y0 = intestazione(s, sch)
    y1 = nota(s, sch)
    voci = sch["voci"]
    col = COLORI.get(sch.get("colore", "ambra"))
    size = sch.get("size", 74)
    tot = sum(h_blocco(v, size, "r", W - 420) + 40 for v in voci)
    while tot > y1 - y0 and size > 34:
        size -= 2
        tot = sum(h_blocco(v, size, "r", W - 420) + 40 for v in voci)
    y = y0 + max(0, (y1 - y0 - tot) / 2)
    for i, v in enumerate(voci):
        hv = h_blocco(v, size, "r", W - 420)
        s.d.ellipse([130, y + 4, 130 + size * 1.25, y + 4 + size * 1.25], fill=col)
        s.text((130 + size * .625, y + 4 + size * .625), str(i + 1), int(size * .75), "b", (255, 255, 255), anchor="mm")
        blocco(s, 130 + size * 1.6, y, v, size, "r", INK, W - 420)
        s.mark(110, y - 14, W - 110, y + hv + 14)
        y += hv + 40


def _caldaia_disegno(s, x, y, w, h):
    """Mini K30 vista di fronte: corpo caldaia a sinistra, silos a destra (schema semplificato)."""
    d = s.d
    cw = w * 0.56
    d.rounded_rectangle([x, y, x + cw, y + h], radius=26, fill=(236, 238, 242), outline=(110, 115, 125), width=7)
    d.rounded_rectangle([x + cw + 14, y + h * .12, x + w, y + h], radius=26, fill=(228, 230, 236), outline=(110, 115, 125), width=7)
    # quadro comandi
    d.rounded_rectangle([x + cw * .2, y + h * .05, x + cw * .8, y + h * .17], radius=12, fill=(40, 44, 52))
    d.rectangle([x + cw * .3, y + h * .075, x + cw * .62, y + h * .145], fill=(90, 160, 220))
    # portello
    d.rounded_rectangle([x + cw * .17, y + h * .27, x + cw * .83, y + h * .62], radius=16, fill=(200, 202, 208), outline=(90, 95, 105), width=6)
    d.ellipse([x + cw * .44, y + h * .36, x + cw * .56, y + h * .44], fill=(240, 140, 50), outline=(90, 95, 105), width=4)
    # cassetto cenere
    d.rounded_rectangle([x + cw * .2, y + h * .72, x + cw * .8, y + h * .9], radius=12, fill=(210, 212, 218), outline=(90, 95, 105), width=6)
    d.rectangle([x + cw * .42, y + h * .79, x + cw * .58, y + h * .82], fill=(90, 95, 105))
    # silos
    sx0 = x + cw + 14
    d.rectangle([sx0 + 30, y + h * .2, x + w - 30, y + h * .26], fill=(160, 165, 175))
    for k in range(5):
        yy = y + h * (.36 + k * .1)
        d.line([(sx0 + 40, yy), (x + w - 40, yy)], fill=(200, 160, 90), width=10)
    # canna fumaria in alto
    d.rectangle([x + cw * .38, y - h * .14, x + cw * .62, y], fill=(150, 150, 155), outline=(110, 115, 125), width=5)


def sch_caldaia(s, sch):
    """Schema della caldaia con etichette numerate: voci = [[etichetta, punto 'quadro'|'portello'|...], ...]."""
    y0 = intestazione(s, sch)
    x, y, w, h = 160, y0 + 160, 1000, H - y0 - 300
    _caldaia_disegno(s, x, y, w, h)
    cw = w * 0.56
    P = {"quadro": (x + cw * .5, y + h * .11), "portello": (x + cw * .5, y + h * .45), "visore": (x + cw * .5, y + h * .4),
         "cenere": (x + cw * .5, y + h * .81), "silos": (x + cw + 14 + (w - cw - 14) / 2, y + h * .55),
         "coperchio": (x + cw + 14 + (w - cw - 14) / 2, y + h * .23), "camino": (x + cw * .5, y - h * .07),
         "retro": (x + cw * .9, y + h * .3), "base": (x + cw * .5, y + h * .97)}
    voci = sch["voci"]
    lx = x + w + 150
    step = (H - 120 - y0) / max(len(voci), 1)
    for i, (et, punto) in enumerate(voci):
        ly = y0 + step * i + step / 2
        px, py = P.get(punto, P["portello"])
        s.d.line([(px, py), (lx - 20, ly)], fill=AMBRA, width=5)
        s.d.ellipse([px - 16, py - 16, px + 16, py + 16], fill=AMBRA)
        s.d.ellipse([lx - 10, ly - 38, lx + 66, ly + 38], fill=AMBRA)
        s.text((lx + 28, ly), str(i + 1), 46, "b", (255, 255, 255), anchor="mm")
        lines = wrap(et, 46, "s", W - lx - 200)
        for k, l in enumerate(lines):
            s.text((lx + 100, ly - (len(lines) - 1) * 29 + k * 58), l, 46, "s", INK, anchor="lm")
        s.mark(lx - 30, ly - max(46, len(lines) * 31), W - 90, ly + max(46, len(lines) * 31))


def sch_locale(s, sch):
    """Pianta e sezione del locale caldaia con le quote."""
    y0 = intestazione(s, sch)
    d = s.d
    # pianta
    px, py, pw, ph = 140, y0 + 60, 1150, H - y0 - 200
    d.rectangle([px, py, px + pw, py + ph], fill=(250, 246, 238), outline=INK, width=14)
    cx0, cy0, cx1, cy1 = px + 330, py + 230, px + 330 + 470, py + 230 + 400
    d.rounded_rectangle([cx0, cy0, cx1, cy1], radius=16, fill=(225, 228, 234), outline=(100, 105, 115), width=6)
    s.text(((cx0 + cx1) / 2, (cy0 + cy1) / 2), "caldaia", 46, "b", INK, anchor="mm")
    q = sch["quote"]

    def quota(a, b, testo, vert=False, col=ROSSO):
        d.line([a, b], fill=col, width=6)
        for p in (a, b):
            if vert:
                d.line([(p[0] - 20, p[1]), (p[0] + 20, p[1])], fill=col, width=6)
            else:
                d.line([(p[0], p[1] - 20), (p[0], p[1] + 20)], fill=col, width=6)
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        s.text((mx + (26 if vert else 0), my - (0 if vert else 40)), testo, 42, "b", col, anchor="lm" if vert else "mm")
    quota((cx0 + 120, py + 7), (cx0 + 120, cy0), q.get("dietro", ""), vert=True)
    quota((px + 7, cy0 + 120), (cx0, cy0 + 120), q.get("sinistra", ""))
    quota((cx1, cy0 + 260), (px + pw - 7, cy0 + 260), "", col=BLU)
    for k, l in enumerate(wrap(q.get("destra", ""), 40, "b", px + pw - cx1 - 40)):
        s.text((cx1 + 25, cy0 + 300 + k * 52), l, 40, "b", BLU)
    quota((cx0 + 350, cy1), (cx0 + 350, py + ph - 7), q.get("davanti", ""), vert=True, col=BLU)
    s.text((px + 30, py + ph + 50), "pianta (schema indicativo)", 38, "r", MUTED)
    s.mark(px, py, px + pw, py + ph)
    # sezione con finestra e massetto
    sx, sy, sw, sh_ = 1420, y0 + 60, 1040, H - y0 - 200
    d.rectangle([sx, sy, sx + sw, sy + sh_], fill=(250, 246, 238), outline=INK, width=14)
    d.rectangle([sx + sw - 200, sy + 30, sx + sw - 7, sy + 180], fill=(205, 228, 250), outline=BLU, width=6)
    s.text((sx + sw - 220, sy + 105), q.get("finestra", ""), 40, "b", BLU, anchor="rm")
    bx0, bx1 = sx + 220, sx + 600
    d.rectangle([bx0 - 40, sy + sh_ - 70, bx1 + 40, sy + sh_ - 7], fill=(190, 190, 190), outline=(120, 120, 120), width=4)
    d.rounded_rectangle([bx0, sy + sh_ - 70 - 420, bx1, sy + sh_ - 70], radius=14, fill=(225, 228, 234), outline=(100, 105, 115), width=6)
    s.text((bx1 + 60, sy + sh_ - 40), q.get("massetto", ""), 40, "b", INK, anchor="lm")
    quota((bx0 + 190, sy + 7), (bx0 + 190, sy + sh_ - 490), q.get("sopra", ""), vert=True)
    s.text((sx + 30, sy + sh_ + 50), "sezione (schema indicativo)", 38, "r", MUTED)
    s.mark(sx, sy, sx + sw, sy + sh_)


def sch_camino(s, sch):
    """Casa con canna fumaria a tetto e regole accanto."""
    y0 = intestazione(s, sch)
    d = s.d
    hx, hy, hw, hh = 170, y0 + 560, 820, H - y0 - 640
    d.polygon([(hx - 40, hy), (hx + hw / 2, hy - 260), (hx + hw + 40, hy)], fill=AMBRA)
    d.rectangle([hx, hy, hx + hw, hy + hh], fill=(255, 255, 255), outline=AMBRA, width=8)
    cx = hx + hw * .68
    d.rectangle([cx - 36, hy - 400, cx + 36, hy + hh - 150], fill=(150, 150, 155), outline=(100, 100, 105), width=4)
    d.rectangle([cx - 70, hy - 440, cx + 70, hy - 400], fill=(110, 110, 115))
    d.rounded_rectangle([hx + 80, hy + hh - 300, hx + 330, hy + hh - 20], radius=14, fill=(225, 228, 234), outline=(100, 105, 115), width=6)
    d.line([(hx + 205, hy + hh - 300), (hx + 205, hy + hh - 360), (cx - 36, hy + hh - 360)], fill=(150, 150, 155), width=26)
    # quota sopra il colmo
    ky = hy - 260
    d.line([(cx + 110, ky), (cx + 110, hy - 440)], fill=ROSSO, width=6)
    for yy in (ky, hy - 440):
        d.line([(cx + 90, yy), (cx + 130, yy)], fill=ROSSO, width=6)
    s.text((cx + 150, (ky + hy - 440) / 2), sch.get("quota", ""), 44, "b", ROSSO, anchor="lm")
    s.mark(hx - 60, y0, hx + hw + 300, H - 120)
    # regole
    rx = 1300
    voci = sch["voci"]
    size = 60
    while sum(h_blocco(v, size, "r", W - rx - 220) + 34 for v in voci) > H - 120 - y0 and size > 34:
        size -= 2
    y = y0 + 20
    for i, v in enumerate(voci):
        hv = h_blocco(v, size, "r", W - rx - 220)
        s.d.ellipse([rx, y + 6, rx + 50, y + 56], fill=AMBRA)
        s.text((rx + 25, y + 31), str(i + 1), 32, "b", (255, 255, 255), anchor="mm")
        blocco(s, rx + 80, y, v, size, "r", INK, W - rx - 200)
        s.mark(rx - 20, y - 12, W - 90, y + hv + 12)
        y += hv + 34


def etichette(sch):
    """Per ogni riquadro evidenziato, le parole con cui la voce lo nomina (stesso ordine dei riquadri)."""
    if sch.get("chiavi"):
        return sch["chiavi"]
    t = sch["tipo"]
    if t == "copertina":
        return sch.get("punti", [])
    if t == "schede":
        return [v[0] for v in sch["voci"]]
    if t == "tabella":
        gr = sch.get("gruppi") or [[k] for k in range(len(sch["righe"]))]
        return [" ".join(str(c) for c in sch["righe"][g[0]]) for g in gr]
    if t == "barre":
        return [v[0] for v in sch["voci"]]
    if t == "due":
        return [[sch[k]["voci"][0], sch[k]["titolo"]] for k in ("sx", "dx")]
    if t == "lista":
        return sch["voci"]
    if t == "caldaia":
        return [v[0] for v in sch["voci"]]
    if t == "locale":
        return ["vano tecnico locale", "finestra aerazione"]
    if t == "camino":
        return ["scarico fumi canna fumaria"] + sch["voci"]
    return []


TIPI = {"copertina": sch_copertina, "schede": sch_schede, "tabella": sch_tabella, "barre": sch_barre, "due": sch_due,
        "lista": sch_lista, "caldaia": sch_caldaia, "locale": sch_locale, "camino": sch_camino}


def disegna(nome, sch):
    s = S()
    TIPI[sch["tipo"]](s, sch)
    ASSET.mkdir(parents=True, exist_ok=True)
    s.im.save(ASSET / f"{nome}.png")
    return s.boxes


# ---------------------------------------------------------------------------
# slide e storyboard
# ---------------------------------------------------------------------------
def build():
    c = json.loads((MAT / "contenuto.json").read_text())
    prs = Presentation(); prs.slide_width, prs.slide_height = SW, SH
    blank = prs.slide_layouts[6]
    rows = []
    scene = c["scene"]
    side = "sinistra"
    riq = {}
    for n, sc in enumerate(scene, 1):
        nome = f"schema-{n:02d}"
        boxes = disegna(nome, sc["schema"])
        riq[nome] = boxes
        cap = sc["cap"]
        s = prs.slides.add_slide(blank)
        add_rect(s, "Sfondo", 0, 0, SW, SH, fill=(251, 248, 241))
        side = sc.get("lato") or ("sinistra" if side == "destra" else "destra")
        px = 0.026 if side == "destra" else 0.319
        add_rect(s, "Spazio per il personaggio", SW * (0.70 if side == "destra" else 0.0), 0, SW * .30, SH, fill=(246, 240, 228))
        add_rect(s, "Barra del titolo", SW * px, SH * .043, SW * .009, SH * .127, fill=(181, 105, 0))
        add_text(s, "Capitolo", SW * (px + .019), SH * .029, SW * .636, SH * .047, f"Capitolo {cap} · {c['capitoli'][str(cap)]['titolo']}", 12, False, (122, 106, 82))
        add_text(s, "Titolo", SW * (px + .019), SH * .067, SW * .636, SH * .113, sc["titolo"], 30, True, (181, 105, 0))
        pw, ph = SW * .655, SH * .757
        pic = s.shapes.add_picture(str(ASSET / f"{nome}.png"), Emu(int(SW * px)), Emu(int(SH * .2)), Emu(int(pw)), Emu(int(ph)))
        pic.name = f"Schema: {nome}"
        sx, sy = pw / W, ph / H
        for i, b in enumerate(boxes, 1):
            add_rect(s, f"Evidenza {i}", SW * px + b[0] * sx, SH * .2 + b[1] * sy, (b[2] - b[0]) * sx, (b[3] - b[1]) * sy,
                     line=(214, 48, 39) if sc.get("avviso") else (214, 48, 39), lw=2.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        add_text(s, "Numero della slide", SW * .88, SH * .952, SW * .09, SH * .04, f"{n} / {len(scene)}", 10, False, (122, 106, 82))
        rows.append([n, f"{cap} — {c['capitoli'][str(cap)]['titolo']}", sc["titolo"], f"Asset_Grafici/{nome}.png", "Schema grafico",
                     "", sc["testo"], side, sc.get("mov", "indica"), "", "zoom" if sc.get("zoom") else "", None, None, None])
    tempi = {}
    for n, sc in enumerate(scene, 1):
        et = etichette(sc["schema"])
        if et and len(et) == len(riq[f"schema-{n:02d}"]):
            tempi[str(n)] = [round(x, 3) for x in completa(posizioni(et, sc["testo"]))]
    (MAT / "tempi_evidenze.json").write_text(json.dumps(tempi, indent=1))
    prs.save(MAT / f"Slide_{c['file']}.pptx")
    (ASSET / "riquadri.json").write_text(json.dumps(riq))
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = "Storyboard"
    ws.append(["Scena", "Capitolo", "Titolo della slide", "Schermata o schema (file)", "Dispositivo", "Testo in slide", "Testo pronunciato",
               "Lato del personaggio", "Movimento del personaggio", "Elementi da evidenziare", "Zoom e transizioni", "Durata (s)", "Inizio", "Fine"])
    for r in rows:
        ws.append(r)
    wc = wb.create_sheet("Capitoli")
    wc.append(["Capitolo", "Titolo", "Obiettivo formativo", "Slide", "Durata (s)", "Durata"])
    for k in sorted(c["capitoli"], key=int):
        wc.append([int(k), c["capitoli"][k]["titolo"], c["capitoli"][k]["obiettivo"], "", "", ""])
    wb.save(MAT / "Storyboard_Animazione.xlsx")
    parole = sum(len(sc["testo"].split()) for sc in scene)
    print(len(rows), "scene,", parole, "parole (circa", round(parole / 140 + len(rows) * 0.12, 1), "min)")


if __name__ == "__main__":
    build()
