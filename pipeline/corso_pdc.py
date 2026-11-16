#!/usr/bin/env python3
"""Costruisce il "pacchetto" del corso Pompe di calore (episodi 02-06) nello stesso formato
dei pacchetti delle app: Slide_*.pptx + Storyboard_Animazione.xlsx + Asset_Grafici.
Così il montaggio usa lo stesso programma (course_render.py) con la regia a tutto schermo.

Scene 3D (apertura/chiusura): nello storyboard la colonna file vale "clip:<nome>".
"""
import json
import re
from pathlib import Path

import openpyxl
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Emu, Pt

ROOT = Path(__file__).resolve().parent.parent
CORSO = ROOT / "corsi" / "pompe-di-calore"
MAT = CORSO / "materiale"
ASSET = MAT / "Asset_Grafici"
SW, SH = 12191695, 6858000

SCHEMI = {
    2: ["pdc-02-tipi", "pdc-02-terreno", "pdc-02-monoblocco-split", "pdc-02-ibrido"],
    3: ["pdc-03-cop", "pdc-03-scop", "pdc-03-mandata", "pdc-03-curva"],
    4: ["pdc-04-casa", "pdc-04-potenza", "pdc-04-bivalenza", "pdc-04-taglia", "pdc-04-acs"],
    5: ["pdc-05-esterna", "pdc-05-condensa", "pdc-05-idraulica", "pdc-05-tre", "pdc-05-messa"],
    6: ["pdc-06-regolazione", "pdc-06-fv", "pdc-06-manutenzione", "pdc-06-errori"],
}
OBIETTIVI = {
    2: "Riconoscere i tipi di pompa di calore: sorgente e destinazione, monoblocco e split, sistemi ibridi.",
    3: "Capire COP, SCOP e perché la temperatura di mandata e la curva climatica contano.",
    4: "Scegliere la potenza giusta: fabbisogno dell'edificio, potenza al freddo, punto di bivalenza, acqua calda sanitaria.",
    5: "Installare bene: unità esterna, condensa, circuito idraulico, antigelo, elettrico, F-gas, messa in servizio.",
    6: "Far lavorare bene la pompa di calore nel tempo: regolazione, fotovoltaico, manutenzione, errori da evitare.",
}
GESTI = {  # movimento per gli schemi (parole chiave lette da course_render)
    "pdc-02-tipi": "indica le tre righe una alla volta", "pdc-02-terreno": "indica le due linee",
    "pdc-02-monoblocco-split": "indica i due schemi; alza l'indice sull'attenzione", "pdc-02-ibrido": "indica la regolazione; pollice in su",
    "pdc-03-cop": "conta sulle dita fino a quattro", "pdc-03-scop": "indica la linea della media",
    "pdc-03-mandata": "indica le due colonne; alza l'indice", "pdc-03-curva": "indica la curva; pollice in su",
    "pdc-04-casa": "indica le dispersioni", "pdc-04-potenza": "indica la linea blu", "pdc-04-bivalenza": "indica il punto; alza l'indice",
    "pdc-04-taglia": "serio, scuote la testa", "pdc-04-acs": "conta le persone sulle dita",
    "pdc-05-esterna": "indica l'unità esterna; serio sull'avviso", "pdc-05-condensa": "pollice in su; poi serio, scuote la testa",
    "pdc-05-idraulica": "indica i componenti uno alla volta", "pdc-05-tre": "conta sulle dita fino a tre",
    "pdc-05-messa": "indica la lista; pollice in su",
    "pdc-06-regolazione": "indica le due linee; pollice in su", "pdc-06-fv": "indica il sole; mostra il telefono",
    "pdc-06-manutenzione": "conta sulle dita", "pdc-06-errori": "serio, conta gli errori sulle dita",
}
TITOLI_EP = {2: "I tipi di pompa di calore", 3: "COP, SCOP e temperatura di mandata", 4: "Il dimensionamento",
             5: "L'installazione", 6: "Efficienza e manutenzione"}


def parse_copioni():
    t = (CORSO / "COPIONI_episodi_02-06.md").read_text()
    eps = {}
    for block in re.split(r"\n## Episodio ", t)[1:]:
        n = int(block[:2])
        scenes = []
        for m in re.finditer(r"\*\*Scena (\d+) · ([^*]+)\*\*\s*\n«(.+?)»", block, re.S):
            scenes.append({"n": int(m.group(1)), "titolo": m.group(2).strip(), "testo": " ".join(m.group(3).split())})
        eps[n] = scenes
    return eps


def rgb(c):
    return RGBColor(*c)


def add_rect(slide, name, x, y, w, h, fill=None, line=None, lw=0, shape=MSO_SHAPE.RECTANGLE):
    sh = slide.shapes.add_shape(shape, Emu(int(x)), Emu(int(y)), Emu(int(w)), Emu(int(h)))
    sh.name = name
    if fill:
        sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill)
    else:
        sh.fill.background()
    if line:
        sh.line.color.rgb = rgb(line); sh.line.width = Pt(lw)
    else:
        sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def add_text(slide, name, x, y, w, h, text, size, bold=False, color=(43, 36, 24)):
    tb = slide.shapes.add_textbox(Emu(int(x)), Emu(int(y)), Emu(int(w)), Emu(int(h)))
    tb.name = name
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold; r.font.name = "Segoe UI"; r.font.color.rgb = rgb(color)
    return tb


def build():
    eps = parse_copioni()
    riq = json.loads((ASSET / "riquadri.json").read_text())
    prs = Presentation(); prs.slide_width, prs.slide_height = SW, SH
    blank = prs.slide_layouts[6]
    rows = []
    n = 0
    total = sum(len(v) for v in eps.values())
    side = "destra"
    for ep in sorted(eps):
        sch = iter(SCHEMI[ep])
        scenes = eps[ep]
        for k, sc in enumerate(scenes):
            n += 1
            s = prs.slides.add_slide(blank)
            add_rect(s, "Sfondo", 0, 0, SW, SH, fill=(251, 248, 241))
            is_clip = k == 0 or k == len(scenes) - 1
            cap_label = f"Episodio {ep} · {TITOLI_EP[ep]}"
            if is_clip:
                clipname = f"ep{ep:02d}-apertura" if k == 0 else "chiusura"
                add_text(s, "Titolo", SW * .08, SH * .38, SW * .84, SH * .2, TITOLI_EP[ep], 44, True, (181, 105, 0))
                add_text(s, "Capitolo", SW * .08, SH * .3, SW * .84, SH * .08, "Corso Pompe di calore", 20, False, (122, 106, 82))
                file_, lato, mov = f"clip:{clipname}", "", ("cammina e saluta" if k == 0 else "saluta")
            else:
                name = next(sch)
                side = "sinistra" if side == "destra" else "destra"
                px = 0.026 if side == "destra" else 0.319
                add_rect(s, "Spazio per il personaggio", SW * (0.70 if side == "destra" else 0.0), 0, SW * .30, SH, fill=(246, 240, 228))
                bx = 0.026 if side == "destra" else 0.319
                add_rect(s, "Barra del titolo", SW * bx, SH * .043, SW * .009, SH * .127, fill=(181, 105, 0))
                add_text(s, "Capitolo", SW * (bx + .019), SH * .029, SW * .636, SH * .047, cap_label, 12, False, (122, 106, 82))
                add_text(s, "Titolo", SW * (bx + .019), SH * .067, SW * .636, SH * .113, sc["titolo"].split(" (")[0], 30, True, (181, 105, 0))
                pw, ph = SW * .655, SH * .757
                pic = s.shapes.add_picture(str(ASSET / f"{name}.png"), Emu(int(SW * px)), Emu(int(SH * .2)), Emu(int(pw)), Emu(int(ph)))
                pic.name = f"Schema: {name}"
                sx, sy = pw / 2580, ph / 1677
                for i, b in enumerate(riq[name], 1):
                    add_rect(s, f"Evidenza {i}", SW * px + b[0] * sx, SH * .2 + b[1] * sy, (b[2] - b[0]) * sx, (b[3] - b[1]) * sy,
                             line=(214, 48, 39), lw=2.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
                file_, lato, mov = f"Asset_Grafici/{name}.png", side, GESTI.get(name, "indica")
            add_text(s, "Numero della slide", SW * .88, SH * .952, SW * .09, SH * .04, f"{n} / {total}", 10, False, (122, 106, 82))
            rows.append([n, f"{ep} — {TITOLI_EP[ep]}", sc["titolo"].split(" (")[0], file_, "Schema grafico" if not is_clip else "Scena 3D",
                         "", sc["testo"], lato, mov, "", "", None, None, None])
        side = "destra"  # dopo la scena 3D di chiusura il personaggio rientra da destra
    prs.save(MAT / "Slide_Pompe_di_calore.pptx")
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = "Storyboard"
    ws.append(["Scena", "Capitolo", "Titolo della slide", "Schermata o schema (file)", "Dispositivo", "Testo in slide", "Testo pronunciato",
               "Lato del personaggio", "Movimento del personaggio", "Elementi da evidenziare", "Zoom e transizioni", "Durata (s)", "Inizio", "Fine"])
    for r in rows:
        ws.append(r)
    wc = wb.create_sheet("Capitoli")
    wc.append(["Capitolo", "Titolo", "Obiettivo formativo", "Slide", "Durata (s)", "Durata"])
    for ep in sorted(eps):
        wc.append([ep, TITOLI_EP[ep], OBIETTIVI[ep], "", "", ""])
    wb.save(MAT / "Storyboard_Animazione.xlsx")
    print(len(rows), "scene;", "slide e storyboard scritti in", MAT)


if __name__ == "__main__":
    build()
