#!/usr/bin/env python3
"""Dopo il montaggio di un corso: pagina di visione e manifesti di deposito per episodio.

  CORSO=gestione-finanziamenti python3 pipeline/consegna_corso.py pagina    # video compressi + index.html (da pubblicare)
  CORSO=gestione-finanziamenti python3 pipeline/consegna_corso.py manifesti # output/deposito/<corso>_<episodio>/manifesto.json
Poi: python3 pipeline/deposito.py episodio <manifesto.json> (uno alla volta, attendendo "consegnato").
"""
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOME = os.environ.get("CORSO", "fotovoltaici")
CORSO = ROOT / "corsi" / NOME
MAT = CORSO / "materiale"
OUT = ROOT / "output" / NOME
PAG = OUT / "pagina"


def cfg():
    return json.loads((CORSO / "course.json").read_text())


def capitoli():
    import openpyxl
    tl = json.loads((OUT / "timeline.json").read_text())
    wb = openpyxl.load_workbook(MAT / "Storyboard_Animazione.xlsx", data_only=True)
    ob = {int(r[0]): r[2] for r in list(wb["Capitoli"].iter_rows(values_only=True))[1:] if isinstance(r[0], int)}
    caps = {}
    for s in tl:
        c = caps.setdefault(s["cap"], {"n": s["cap"], "titolo": s["cap_titolo"].split("—", 1)[1].strip(), "t0": s["t0"], "scene": [], "obiettivo": ob.get(s["cap"], "")})
        c["scene"].append({"n": s["n"], "titolo": s["titolo"], "t": round(s["t0"] - c["t0"], 2)})
    for c in caps.values():
        ss = [s for s in tl if s["cap"] == c["n"]]
        c["dur"] = round(ss[-1]["t0"] + ss[-1]["dur"] - c["t0"], 2)
    return tl, [caps[k] for k in sorted(caps)]


def pagina():
    tl, caps = capitoli()
    PAG.mkdir(parents=True, exist_ok=True)
    procs = []
    for c in caps:
        src = OUT / "capitoli" / f"capitolo_{c['n']:02d}.mp4"
        procs.append(subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-map", "0:v", "-map", "0:a", "-c:v", "libx264", "-preset", "slow",
                                       "-crf", "28", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart", str(PAG / f"cap{c['n']:02d}.mp4")]))
    for p in procs:
        p.wait()
    for c in caps:
        nn = f"{c['n']:02d}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(OUT / "capitoli" / f"capitolo_{nn}.srt"), str(PAG / f"cap{nn}.vtt")], check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "3", "-i", str(PAG / f"cap{nn}.mp4"), "-frames:v", "1", "-vf", "scale=960:-1", "-q:v", "4", str(PAG / f"cap{nn}.jpg")], check=True)
        c["vtt"] = (PAG / f"cap{nn}.vtt").read_text(encoding="utf-8")
    titolo_corso = cfg().get("deposito", {}).get("corso_titolo") or NOME.replace("-", " ").capitalize()
    tot = sum(c["dur"] for c in caps)
    tmpl = (ROOT / "pipeline" / "pagina_corso.html").read_text(encoding="utf-8")
    page = (tmpl.replace("{{TITOLO_PAGINA}}", f"Corso {titolo_corso}")
            .replace("{{TITOLO}}", f"App «{titolo_corso}»")
            .replace("{{META}}", f"<span>{len(caps)} capitoli · {len(tl)} scene</span><span>{int(tot // 60)} min {int(tot % 60):02d} s</span><span>Voce: Diego</span><span>Sottotitoli in italiano</span>")
            .replace("{{DATI}}", json.dumps(caps, ensure_ascii=False).replace("</", "<\\/")))
    (PAG / "index.html").write_text(page, encoding="utf-8")
    print("pagina", PAG / "index.html", sum(f.stat().st_size for f in PAG.glob("*.mp4")) / 1e6, "MB di video")


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")[:50].rstrip("-")


def manifesti():
    import openpyxl
    from PIL import Image
    tl, caps = capitoli()
    c_cfg = cfg()
    dep = c_cfg.get("deposito", {})
    corso = dep.get("corso", NOME)
    nomi = dep.get("episodi") or [f"{c['n']:02d}-{slug(c['titolo'])}" for c in caps]
    wb = openpyxl.load_workbook(MAT / "Storyboard_Animazione.xlsx", data_only=True)
    rows = list(wb.worksheets[0].iter_rows(values_only=True))
    sb = [dict(zip(rows[0], r)) for r in rows[1:] if isinstance(r[0], int)]
    led = [json.loads(l) for l in open(OUT / "ledger.jsonl")] if (OUT / "ledger.jsonl").exists() else []
    report = ROOT / "docs" / c_cfg.get("report", f"CORSO_{NOME.upper().replace('-', '_')}_report.md")
    for c, epi in zip(caps, nomi):
        nums = [s["n"] for s in c["scene"]]
        ss = [s for s in tl if s["cap"] == c["n"]]
        c0 = ss[0]["t0"]
        D = ROOT / "output" / "deposito" / f"{corso}_{epi}"
        D.mkdir(parents=True, exist_ok=True)
        cop = [f"# Copione — {dep.get('corso_titolo', NOME)}, capitolo {c['n']}: {c['titolo']}", ""]
        for r in sb:
            if r["Scena"] in nums:
                cop += [f"## Scena {r['Scena']} — {r['Titolo della slide']}", "", r["Testo pronunciato"], ""]
        (D / "copione.md").write_text("\n".join(cop))
        (D / "storyboard.json").write_text(json.dumps([r for r in sb if r["Scena"] in nums], ensure_ascii=False, indent=1, default=str))
        (D / "timeline.json").write_text(json.dumps([{k: v for k, v in s.items() if k != "geo"} | {"t0": round(s["t0"] - c0, 3), "speech_t0": round(s["speech_t0"] - c0, 3)} for s in ss], ensure_ascii=False, indent=1))
        rows_led = [{"data": e.get("ts"), "fase": "voce", "servizio": "elevenlabs", "modello": f"{c_cfg.get('elevenlabs_model')} (voce clonata di Diego)",
                     "secondi": None, "costo_usd": 0, "esito": e.get("status"), "errore": e.get("error"), "caratteri": e.get("chars"), "scena": e.get("scena")}
                    for e in led if e.get("scena") in nums]
        (D / "ledger.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rows_led))
        tiles = []
        for s in ss:
            for f in (0.3, 0.75):
                subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{(s['t0'] - c0) + s['dur'] * f:.2f}", "-i", str(OUT / f"capitoli/capitolo_{c['n']:02d}.mp4"),
                                "-frames:v", "1", "-vf", "scale=480:270", str(D / "_t.png")], check=True)
                tiles.append(Image.open(D / "_t.png").convert("RGB"))
        cols = 4
        sh = Image.new("RGB", (480 * cols, 270 * ((len(tiles) + cols - 1) // cols)))
        for i, im in enumerate(tiles):
            sh.paste(im, ((i % cols) * 480, (i // cols) * 270))
        sh.save(D / "contact_sheet.png")
        (D / "_t.png").unlink()
        F = []
        add = lambda cat, n, src: F.append({"categoria": cat, "nome": n, "src": str(src)})
        nn = f"{c['n']:02d}"
        add("finale", "video.mp4", OUT / f"capitoli/capitolo_{nn}.mp4")
        add("finale", "video.srt", OUT / f"capitoli/capitolo_{nn}.srt")
        if (PAG / f"cap{nn}.jpg").exists():
            add("finale", "poster.jpg", PAG / f"cap{nn}.jpg")
            add("finale", "anteprima_mobile.mp4", PAG / f"cap{nn}.mp4")
        add("progetto", "copione.md", D / "copione.md")
        add("progetto", "storyboard.json", D / "storyboard.json")
        add("progetto", "course.json", CORSO / "course.json")
        add("progetto", "timeline.json", D / "timeline.json")
        for n in nums:
            add("progetto", f"slide_{n:02d}.png", OUT / f"slide/full/s-{n:02d}.png")
            add("sorgenti", f"voice/{n:02d}.wav", OUT / f"voce/{n:02d}.wav")
        if c["n"] == caps[0]["n"]:  # materiale originale del pacchetto, una volta sola
            for f in sorted(MAT.glob("*")):
                if f.is_file() and f.suffix.lower() in (".pptx", ".xlsx", ".docx", ".pdf", ".md"):
                    add("progetto", re.sub(r"[^A-Za-z0-9._-]", "_", f.name), f)
        if report.exists():
            add("report", "render_report.md", report)
        add("report", "ledger.jsonl", D / "ledger.jsonl")
        add("report", "contact_sheet.png", D / "contact_sheet.png")
        for f in F:
            assert Path(f["src"]).exists(), f
        scheda = {"corso_titolo": dep.get("corso_titolo", NOME), "episodio_numero": c["n"], "episodio_titolo": c["titolo"], "descrizione": c["obiettivo"],
                  "durata_s": c["dur"], "scene": [{"inizio_s": s["t"], "titolo": s["titolo"]} for s in c["scene"]], "lingua": "it"}
        (D / "manifesto.json").write_text(json.dumps({"corso": corso, "episodio": epi, "consegna": True, "scheda": scheda, "file": F}, ensure_ascii=False, indent=1))
        print(epi, len(F), "file", round(sum(Path(f["src"]).stat().st_size for f in F) / 1e6, 1), "MB")


if __name__ == "__main__":
    {"pagina": pagina, "manifesti": manifesti}[sys.argv[1]]()
