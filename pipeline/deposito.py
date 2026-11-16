#!/usr/bin/env python3
"""Client del deposito Video Corsi del gestionale (API v1).

Il token NON è in questo codice né nell'ambiente: lo aggiunge il proxy della sessione
(intestazione Authorization). Qui si manda solo un segnaposto, mai il valore vero.

  python3 pipeline/deposito.py salute
  python3 pipeline/deposito.py episodio <manifesto.json>     # scheda + file + controllo (+ consegna se "consegna": true)
  python3 pipeline/deposito.py stato <corso> <NN-episodio>
  python3 pipeline/deposito.py elenco <corso> <NN-episodio>
"""
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://app.diegoluigigasparini.com/api/videocorsi/v1"
AUTH = {"Authorization": "Bearer proxy-injected"}   # segnaposto: il proxy lo sostituisce con il token vero
MAX_REQ = 200 * 1024 * 1024
CHUNK = 50 * 1024 * 1024
NOME = re.compile(r"^(?!\.)[A-Za-z0-9._-]{1,120}$")
SLUG = re.compile(r"^[a-z0-9-]{1,60}$")
EPI = re.compile(r"^\d{2}-[a-z0-9-]{1,57}$")
ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "output" / "deposito_registro.jsonl"


def call(method, path, body=None, headers=None, timeout=900):
    data = body if isinstance(body, (bytes, type(None))) else json.dumps(body, ensure_ascii=False).encode()
    h = dict(AUTH)
    if headers:
        h.update(headers)
    if body is not None and not isinstance(body, bytes):
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, method=method, headers=h)
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as e:
            raw = e.read()
            try:
                js = json.loads(raw)
            except Exception:  # noqa: BLE001
                js = {"errore": raw[:300].decode(errors="replace")}
            if e.code in (429, 503) and attempt < 5:
                time.sleep(30 * (attempt + 1)); continue
            return e.code, js
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt < 5:
                time.sleep(10 * (attempt + 1)); continue
            return 0, {"errore": str(e)}


def log(**kw):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    kw["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with LOG.open("a") as f:
        f.write(json.dumps(kw, ensure_ascii=False) + "\n")


def sha256(p: Path):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def check_name(categoria, nome):
    assert categoria in ("finale", "progetto", "sorgenti", "report"), categoria
    parts = nome.split("/")
    if categoria != "sorgenti":
        assert len(parts) == 1, f"sottocartelle solo in sorgenti: {nome}"
    assert len(parts) <= 7 and all(NOME.match(x) and x != "_versioni" and ".." not in x for x in parts), f"nome non valido: {nome}"


def put_file(corso, epi, categoria, nome, src: Path):
    check_name(categoria, nome)
    size = src.stat().st_size
    digest = sha256(src)
    path = f"/episodi/{corso}/{epi}/file/{categoria}/{nome}"
    if size <= MAX_REQ:
        st, js = call("PUT", path, src.read_bytes(), {"Content-Length": str(size), "X-Content-SHA256": digest,
                                                      "Content-Type": "application/octet-stream"})
        if st == 409 and "ricevuti" not in js:
            return st, js, digest
        return st, js, digest
    start = 0
    with src.open("rb") as f:
        while start < size:
            f.seek(start)
            piece = f.read(CHUNK)
            end = start + len(piece) - 1
            st, js = call("PUT", path, piece, {"Content-Length": str(len(piece)), "X-Content-SHA256": digest,
                                              "Content-Range": f"bytes {start}-{end}/{size}", "Content-Type": "application/octet-stream"})
            if st == 202:
                start = int(js.get("ricevuti", end + 1)); continue
            if st == 409 and "ricevuti" in js:
                start = int(js["ricevuti"]); continue
            return st, js, digest
    return 201, {}, digest


def episodio(manifest_path):
    m = json.loads(Path(manifest_path).read_text())
    corso, epi = m["corso"], m["episodio"]
    assert SLUG.match(corso) and EPI.match(epi), (corso, epi)
    st, js = call("PUT", f"/episodi/{corso}/{epi}", m["scheda"])
    print("scheda", st, js.get("errore", ""))
    log(op="scheda", corso=corso, episodio=epi, stato=st)
    if st not in (200, 201):
        return 1
    tot_b, esiti = 0, []
    for item in m["file"]:
        src = Path(item["src"])
        st, js, dg = put_file(corso, epi, item["categoria"], item["nome"], src)
        ok = st in (200, 201)
        if st == 422:  # impronta diversa: un nuovo tentativo
            st, js, dg = put_file(corso, epi, item["categoria"], item["nome"], src); ok = st in (200, 201)
        esiti.append((item["categoria"], item["nome"], st))
        tot_b += src.stat().st_size if ok else 0
        print(f"  {item['categoria']}/{item['nome']}: {st} {js.get('errore', '') if not ok else ('già presente' if js.get('gia_presente') else '')}")
        log(op="file", corso=corso, episodio=epi, categoria=item["categoria"], nome=item["nome"], stato=st,
            dimensione=src.stat().st_size, sha256=dg, errore=js.get("errore"))
        if st == 401:
            print("[STOP] 401: token mancante, sbagliato o revocato"); return 2
    # controllo
    st, js = call("GET", f"/episodi/{corso}/{epi}/file")
    remote = {(f["categoria"], f["nome"]): f for f in (js.get("file", js) if isinstance(js, dict) else js)} if st == 200 else {}
    mancanti = [(c, n) for c, n, s in esiti if (c, n) not in remote]
    print(f"controllo: {len(remote)} file sul server, mancanti {mancanti}")
    if m.get("consegna") and not mancanti and all(s in (200, 201) for *_, s in esiti):
        st, js = call("POST", f"/episodi/{corso}/{epi}/consegna", {})
        print("consegna", st, js.get("errore", ""))
        log(op="consegna", corso=corso, episodio=epi, stato=st, errore=js.get("errore"))
    print(f"totale inviato: {tot_b / 1e6:.1f} MB")
    return 0 if not mancanti else 3


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(0)
    if a[0] == "salute":
        st, js = call("GET", "/salute"); js.pop("token", None) if isinstance(js, dict) and "token" in js and len(str(js["token"])) > 24 else None
        print(st, json.dumps(js, ensure_ascii=False))
    elif a[0] == "episodio":
        sys.exit(episodio(a[1]))
    elif a[0] in ("stato", "elenco"):
        path = f"/episodi/{a[1]}/{a[2]}" + ("/file" if a[0] == "elenco" else "")
        st, js = call("GET", path); print(st, json.dumps(js, ensure_ascii=False, indent=1)[:4000])
