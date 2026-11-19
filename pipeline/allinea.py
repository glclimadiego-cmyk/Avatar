"""Allinea le evidenziazioni al parlato: per ogni riquadro trova nel testo pronunciato il punto in cui
la voce nomina quell'elemento e lo restituisce come frazione (0-1) della durata del parlato.
La voce di ElevenLabs ha un ritmo quasi costante, quindi la posizione nel testo è una buona stima del tempo."""
import re
import unicodedata

STOP = set("""alla allo alle agli dalla dalle dallo dagli della delle dello degli nella nelle nello negli sulla sulle sullo sugli
come cosa sono essere anche solo sempre dove quando quindi oppure ogni tutto tutti tutte questa questo quella quello
hanno viene vanno fare fatto dopo prima molto meno più circa senza sopra sotto ancora caldaia mini kalorina tatano""".split())


def norm(t):
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", t)


def posizioni(etichette, parlato):
    """Frazioni (0-1) del parlato in cui compare ciascuna etichetta, nell'ordine; None se non trovata."""
    p = norm(parlato)
    parole = [(m.start(), m.group()) for m in re.finditer(r"[a-z0-9]+", p)]
    L = max(1, len(p))
    cursore = 0
    out = []
    for lab in etichette:
        if isinstance(lab, (list, tuple)):  # alternative: si prova la prima, poi le altre
            alts = list(lab)
        else:
            alts = [lab]
        best = None
        for alt in alts:
            best = _trova(alt, parole, cursore)
            if best is not None:
                break
        out.append(None if best is None else best / L)
        if best is not None:
            cursore = best + 1
    return out


def _trova(lab, parole, cursore):
    """Posizione (in caratteri) della prima parola significativa dell'etichetta dopo il cursore."""
    toks = [w for w in norm(lab).split()
            if ((len(w) >= 4 and not w.isdigit()) or (len(w) >= 3 and re.search(r"\d", w) and re.search(r"[a-z]", w))) and w not in STOP][:5]
    best = None
    for w in toks:
        for lung in (6, 5, 4):
            stem = w[:lung]
            if len(stem) < 3:
                continue
            pos = next((ps for ps, pw in parole if ps >= cursore and pw.startswith(stem)), None)
            if pos is not None:
                best = pos if best is None else min(best, pos)  # la prima volta che la voce ne pronuncia una
                break
    return best


def completa(fr):
    """Riempie i None per interpolazione lineare (bordi: 0.08 e 0.9); garantisce l'ordine crescente."""
    n = len(fr)
    if not n:
        return fr
    pts = [(-1, 0.06)] + [(i, f) for i, f in enumerate(fr) if f is not None] + [(n, 0.92)]
    out = []
    for i in range(n):
        if fr[i] is not None:
            out.append(fr[i]); continue
        a = max(p for p in pts if p[0] < i)
        b = min(p for p in pts if p[0] > i)
        out.append(a[1] + (b[1] - a[1]) * (i - a[0]) / (b[0] - a[0]))
    for i in range(1, n):
        out[i] = max(out[i], out[i - 1] + 0.02)
    return [min(x, 0.97) for x in out]
