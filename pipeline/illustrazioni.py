#!/usr/bin/env python3
"""Illustrazioni dei concetti per i corsi scritti da noi, generate con fal.ai (nano-banana-2, testo -> immagine).

  python3 pipeline/illustrazioni.py <elenco.json> <cartella_uscita> <tetto_usd> "<approvazione>"

elenco.json: [{"nome": "pellet", "prompt": "..."}]. Le immagini già presenti non si rigenerano.
Ogni chiamata finisce nel registro spese <cartella_uscita>/spese_fal.jsonl; ci si ferma prima di superare il tetto.
Mai il prodotto del costruttore: per quello si usano le foto vere.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from providers import _fal_run  # noqa: E402

MODELLO = "fal-ai/nano-banana-2"
COSTO = 0.08  # USD per immagine a 1K (listino fal.ai letto il 19/11/2026)
STILE = (" Style: clean realistic editorial photo look with soft natural light, warm tones, simple uncluttered background,"
         " no text, no letters, no numbers, no logos, no brand names, no watermarks.")


def main(elenco, out, tetto, approvazione):
    out.mkdir(parents=True, exist_ok=True)
    reg = out / "spese_fal.jsonl"
    speso = sum(json.loads(l).get("costo_usd", 0) for l in reg.open()) if reg.exists() else 0.0
    os.environ.setdefault("FAL_KEY", "proxy-injected")
    for it in json.loads(Path(elenco).read_text()):
        dest = out / f"{it['nome']}.jpg"
        if dest.exists():
            continue
        if speso + COSTO > tetto:
            print("tetto raggiunto:", round(speso, 2), "USD"); break
        try:
            res = _fal_run(MODELLO, {"prompt": it["prompt"] + STILE, "num_images": 1, "aspect_ratio": it.get("formato", "4:3"),
                                     "output_format": "jpeg", "resolution": "1K"})
            url = res["images"][0]["url"]
            with urllib.request.urlopen(url, timeout=300) as r:
                dest.write_bytes(r.read())
            speso += COSTO
            esito, err = "ok", None
        except Exception as e:  # noqa: BLE001
            esito, err = "errore", str(e)[:300]
        with reg.open("a") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "fase": "illustrazione", "servizio": f"fal:{MODELLO}",
                                "nome": it["nome"], "costo_usd": COSTO if esito == "ok" else 0, "esito": esito, "errore": err,
                                "approvazione": approvazione}, ensure_ascii=False) + "\n")
        print(it["nome"], esito, err or "", "| speso", round(speso, 2), "USD")
    print("totale speso", round(speso, 2), "USD su tetto", tetto)


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
