#!/usr/bin/env python3
"""Comando unico per i videocorsi: documenti -> sceneggiatura -> scene -> audio -> MP4.

  python3 pipeline/make_course.py services                       # cosa è configurato davvero
  python3 pipeline/make_course.py draft --docs a.pdf b.md --project corsi/ep02   # bozza copione (Claude API)
  python3 pipeline/make_course.py plan  --project pilota --out output/pilota     # costi previsti
  python3 pipeline/make_course.py approve --out output/pilota --key test_clip --max-usd 3
  python3 pipeline/make_course.py build --project pilota --out output/pilota [--video fal] [--tts elevenlabs] [--test]

Punti di approvazione umana (bloccanti):
  script          -> storyboard.json con "approved": true (o file scritti a mano)
  test_clip       -> spesa per il test 5-8 s (keyframe + 1 clip)
  full_generation -> spesa per tutte le clip del pilota
  voice_paid      -> spesa TTS a pagamento
"""
import argparse
import hashlib
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import providers as pv  # noqa: E402
import render as rd  # noqa: E402

DEFAULT_CFG = {
    "tts": "espeak",
    "video": "animatic",
    "elevenlabs_voice_id": None,
    "elevenlabs_model": "eleven_multilingual_v2",
    "fal_video_model": "fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
    "fal_keyframe_model": "fal-ai/nano-banana-2/edit",
    "clip_seconds_options": [5, 10],
    "rates": pv.DEFAULT_RATES,
    "character": ("stylized 3D cartoon man, bald with short dark hair on the sides, dark-blue rectangular glasses, "
                  "short salt-and-pepper beard, stocky build, navy polo shirt, dark grey work trousers with orange-trimmed "
                  "cargo pockets, black belt, dark safety shoes with orange laces"),
    "style": "Pixar-like 3D animation, soft warm lighting, clean boiler room with red and blue pipes, 16:9, steady camera",
    "negative_prompt": "text, letters, logos, watermark, subtitles, extra fingers, deformed hands, face change, different glasses",
}


def load_project(project: Path):
    sb = json.loads((project / "storyboard.json").read_text())
    script = rd.parse_script((project / "copione.md").read_text())
    cfg = dict(DEFAULT_CFG)
    if (project / "course.json").exists():
        cfg.update(json.loads((project / "course.json").read_text()))
    for sc in sb["scenes"]:
        sc.update(cfg.get("scene_overrides", {}).get(sc["id"], {}))
        key = sc["speech_section"].replace("–", "-")
        if key not in script:
            raise SystemExit(f"Sezione copione '{key}' per {sc['id']} non trovata in copione.md")
        sc["text"] = script[key]
        sc.setdefault("keyframe_prompt",
                      f"Place exactly this character (keep face, glasses, beard, body and clothes identical to the reference sheet) "
                      f"in this setting: {sc['action']}. Camera: {sc['camera']}. {cfg['style']}. Any screen in the scene is blank. "
                      f"No text, no logos.")
        sc.setdefault("motion_prompt",
                      f"{cfg['character']}. {sc['action']}. Camera: {sc['camera']}. Natural walk cycle, hands with five fingers, "
                      f"consistent face and glasses. {cfg['style']}. No text on screens.")
    return sb, cfg


def clip_seconds(dur, opts, tolerance=0.8):
    """Segmenti di clip per coprire `dur` (l'ultimo fotogramma può essere tenuto fino a `tolerance` s)."""
    big, small = max(opts), min(opts)
    segs = [big] * int(dur // big)
    rem = dur - big * len(segs)
    if rem > tolerance or not segs:
        segs.append(small if rem <= small + tolerance else big)
    return segs


def estimate(sb, cfg, durations=None, test=False):
    rates = cfg["rates"]
    rows, total = [], 0.0
    scenes = sb["scenes"][:1] if test else sb["scenes"]
    for sc in scenes:
        if test:
            sc = {**sc, **cfg.get("test_scene", {})}
        if sc.get("base", "clip") != "clip":
            continue
        d = 8 if test else (durations or {}).get(sc["id"], sc["end"] - sc["start"])
        secs = clip_seconds(d, cfg["clip_seconds_options"])
        c = sum(secs) * rates["fal_video_usd_per_s"] + rates["fal_keyframe_usd_per_image"]
        rows.append((sc["id"], secs, round(c, 2)))
        total += c
    chars = sum(len(sc["text"]) for sc in scenes)
    voice = chars / 1000 * rates["elevenlabs_usd_per_1k_chars"]
    return rows, round(total, 2), chars, round(voice, 3)


# --------------------------------------------------------------------------
def cmd_services(a):
    print("Servizi e credenziali visti da questo ambiente:\n")
    checks = [
        ("Voce italiana offline (espeak-ng)", os.path.exists("/usr/bin/espeak-ng"), "gratuita, robotica: solo segnaposto"),
        ("FFmpeg", os.path.exists("/usr/bin/ffmpeg"), "encoding H.264/AAC, sottotitoli"),
        ("ElevenLabs TTS", bool(os.environ.get("ELEVENLABS_API_KEY")), "serve ELEVENLABS_API_KEY + host api.elevenlabs.io"),
        ("fal.ai video/immagini", bool(os.environ.get("FAL_KEY")), "serve FAL_KEY + host queue.fal.run, fal.media"),
        ("Claude API (bozza copione)", bool(os.environ.get("ANTHROPIC_API_KEY")), "serve ANTHROPIC_API_KEY (fatturazione API separata dall'abbonamento)"),
    ]
    for name, ok, note in checks:
        print(f"  [{'OK' if ok else '--'}] {name:38s} {note}")
    print("\nNota: la presenza della chiave non basta: anche la rete dell'ambiente deve consentire l'host.")


def cmd_plan(a):
    sb, cfg = load_project(Path(a.project))
    out = Path(a.out)
    tl_path = out / "timeline.json"
    durs = {s["id"]: s["dur"] for s in json.loads(tl_path.read_text())} if tl_path.exists() else None
    for test in (True, False):
        rows, total, chars, voice = estimate(sb, cfg, durs, test)
        print(f"\n== {'TEST 5-8 s (approvazione: test_clip)' if test else 'PILOTA COMPLETO (approvazione: full_generation)'} ==")
        for sid, secs, c in rows:
            print(f"  {sid}: clip {'+'.join(map(str, secs))} s + 1 keyframe  ~{c:.2f} USD")
        print(f"  Totale video stimato: ~{total:.2f} USD  (tariffa {cfg['rates']['fal_video_usd_per_s']} $/s, modello {cfg['fal_video_model']})")
        print(f"  Voce ElevenLabs: {chars} caratteri ~{voice:.2f} USD (approvazione: voice_paid)")
    print("\nLe tariffe sono indicative (course.json -> rates). Aggiungere ~50% di margine per rigenerazioni.")
    print("Dati inviati a terzi: tavola avatar (volto dell'utente), immagine di scena, testi dei prompt e del copione.")


def cmd_approve(a):
    pv.Ledger(Path(a.out)).approve(a.key, a.max_usd, a.note or "")
    print(f"Approvato '{a.key}' con tetto {a.max_usd} USD")


def cmd_draft(a):
    try:
        import anthropic
    except ImportError:
        raise SystemExit("pip install anthropic   (e impostare ANTHROPIC_API_KEY: fatturazione API separata)")
    proj = Path(a.project); proj.mkdir(parents=True, exist_ok=True)
    content = []
    for d in a.docs:
        p = Path(d)
        if p.suffix.lower() == ".pdf":
            import base64
            content.append({"type": "document", "source": {"type": "base64", "media_type": "application/pdf",
                                                           "data": base64.b64encode(p.read_bytes()).decode()}})
        else:
            content.append({"type": "text", "text": f"<documento nome='{p.name}'>\n{p.read_text()}\n</documento>"})
    example = Path(__file__).parent.parent / "pilota"
    content.append({"type": "text", "text": (
        "Dai documenti sopra ricava un episodio di videocorso tecnico in italiano di circa "
        f"{a.seconds} secondi, stesso formato dell'esempio. Rispondi SOLO con un oggetto JSON con le chiavi "
        "'copione_md' (stringa markdown con sezioni '**MM–MM s — titolo**' seguite da «testo») e 'storyboard' "
        "(oggetto come l'esempio, con \"approved\": false). Ogni scena ha action, camera, speech_section e, se serve "
        "uno schema, layout tra: walk_in, walk_to_monitor, diagram_cycle, hydronic, closeup, talk. "
        "Non inventare dati tecnici assenti nei documenti; segnala dubbi nel campo storyboard.notes.\n\n"
        f"ESEMPIO copione:\n{(example / 'copione.md').read_text()}\n\nESEMPIO storyboard:\n{(example / 'storyboard.json').read_text()}")})
    client = anthropic.Anthropic()
    with client.beta.messages.stream(model="claude-opus-5-5", max_tokens=32000, thinking={"type": "adaptive"},
                                     output_config={"effort": "high"},
                                     betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                                     messages=[{"role": "user", "content": content}]) as s:
        msg = s.get_final_message()
    if msg.stop_reason == "refusal":
        raise SystemExit("Richiesta rifiutata dal modello")
    txt = "".join(b.text for b in msg.content if b.type == "text")
    data = json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
    (proj / "copione.md").write_text(data["copione_md"])
    data["storyboard"]["approved"] = False
    (proj / "storyboard.json").write_text(json.dumps(data["storyboard"], indent=2, ensure_ascii=False))
    print(f"Bozza scritta in {proj}. Rileggere, correggere e impostare \"approved\": true in storyboard.json.")


def _hash(s):
    return hashlib.sha1(s.encode()).hexdigest()[:12]


def cmd_build(a):
    project, out = Path(a.project), Path(a.out)
    sb, cfg = load_project(project)
    tts = a.tts or cfg["tts"]
    video = a.video or cfg["video"]
    if sb.get("approved") is False and not a.allow_draft:
        raise SystemExit("[STOP] storyboard non approvato (\"approved\": false). Rileggere e approvare prima del render.")
    led = pv.Ledger(out)
    led.log(stage="build_start", tts=tts, video=video, test=a.test)
    errors = []

    # 1) voce per scena (cache su hash del testo + provider)
    vdir = out / "voice"
    durs = {}
    for sc in sb["scenes"]:
        wav, tag = vdir / f"{sc['id']}.wav", vdir / f"{sc['id']}.tag"
        key = f"{tts}:{_hash(sc['text'])}"
        if not (wav.exists() and tag.exists() and tag.read_text() == key):
            pv.tts(tts, sc["text"], wav, led, cfg)
            tag.write_text(key)
        durs[sc["id"]] = pv.ffprobe_duration(wav)

    # 2) timeline adattata alla voce reale, SRT, voiceover
    tl = rd.build_timeline(sb["scenes"], durs)
    (out / "timeline.json").write_text(json.dumps(tl, indent=2, ensure_ascii=False))
    rd.write_srt(tl, out / "pilot.srt")
    rd.build_voiceover(tl, vdir, out / "voiceover.wav")

    # 3) clip generative (solo se richiesto e approvato)
    clips = out / "clips"
    if video == "fal":
        approval = "test_clip" if a.test else "full_generation"
        targets = [{**tl[0], **cfg.get("test_scene", {})}] if a.test else [s for s in tl if s.get("base", "clip") == "clip"]
        assets = project / "assets"
        refs = [assets / sb.get("character_reference", "assets/avatar_3d_approvato.png").split("/")[-1], assets / "scena_riferimento.png"]
        for sc in targets:
            kf = out / "keyframes" / f"{sc['id']}.png"
            try:
                if not kf.exists():
                    # continuità: dopo la prima scena il riferimento di ambiente è il keyframe approvato della prima
                    first_kf = out / "keyframes" / f"{tl[0]['id']}.png"
                    sc_refs = [refs[0], first_kf] if sc["id"] != tl[0]["id"] and first_kf.with_suffix(".approvato").exists() else refs
                    pv.generate_keyframe(sc, sc_refs, kf, led, cfg, approval)
                ok_flag = kf.with_suffix(".approvato")
                if not ok_flag.exists() and not a.keyframes_ok:
                    print(f"[STOP] Controlla il fotogramma di partenza {kf} (volto, occhiali, abiti, niente scritte).\n"
                          f"       Se va bene rilancia con --keyframes-ok; se no cancellalo e rilancia per rigenerarlo.")
                    led.log(stage="stop", reason=f"revisione keyframe {sc['id']}"); return 3
                ok_flag.write_text("ok")
                segs = clip_seconds(8 if a.test else sc["dur"], cfg["clip_seconds_options"])
                dest = clips / f"{sc['id']}.mp4"
                if not dest.exists():
                    parts, start = [], kf
                    for k, secs in enumerate(segs):
                        part = clips / "parts" / f"{sc['id']}_{k}.mp4"
                        if not part.exists():
                            pv.generate_clip(sc, start, secs, part, led, cfg, approval)
                        parts.append(part)
                        if k + 1 < len(segs):  # continuità: il segmento successivo parte dall'ultimo fotogramma
                            start = clips / "parts" / f"{sc['id']}_{k}_last.png"
                            pv.last_frame(part, start)
                    if len(parts) > 1:
                        errors.append(f"{sc['id']}: {len(parts)} segmenti concatenati, verificare la giunzione")
                    pv.concat_clips(parts, dest)
            except pv.ApprovalRequired as e:
                print(e); led.log(stage="stop", reason=str(e)); return 2
            except Exception as e:  # noqa: BLE001
                errors.append(f"{sc['id']}: {e}"); print(f"[ERRORE] {sc['id']}: {e}")

    # 4) render
    actor = rd.Actor(out / "sprites", project / "assets" / "avatar_3d_approvato.png")
    animatic = not any((clips / f"{s['id']}.mp4").exists() for s in tl)
    badge = ("ANIMATIC - personaggio provvisorio" + (", voce sintetica" if tts == "espeak" else "")) if animatic else None
    name = "test.mp4" if a.test else "pilot.mp4"
    mp4 = out / name
    only = {tl[0]["id"]} if a.test else None
    n = rd.render(tl, mp4, out / "voiceover.wav", None if a.test else out / "pilot.srt", actor, clips, badge,
                  only=only, max_seconds=8 if a.test else None)

    # 5) verifica reale del file
    info = rd.probe(mp4)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    au = [s for s in info["streams"] if s["codec_type"] == "audio"]
    dur = float(info["format"]["duration"])
    expected = 8 if a.test else sum(s["dur"] for s in tl)
    checks = {
        "risoluzione 1920x1080": (v["width"], v["height"]) == (1920, 1080),
        "25 fps": v["r_frame_rate"] == "25/1",
        "video H.264": v["codec_name"] == "h264",
        "audio AAC": bool(au) and au[0]["codec_name"] == "aac",
        f"durata ~{expected:.1f}s (misurata {dur:.2f}s)": abs(dur - min(expected, n / rd.FPS)) < 0.3,
    }
    if not a.test:
        checks["sottotitoli SRT incorporati"] = any(s["codec_type"] == "subtitle" for s in info["streams"])
    sheet_times = [1.0, 3.5, 7.0] if a.test else [s["t0"] + s["dur"] * 0.5 for s in tl]
    rd.contact_sheet(mp4, sheet_times, out / ("test_contact.png" if a.test else "contact_sheet.png"))
    led.log(stage="render", file=str(mp4), frames=n, duration=dur, checks=checks, status="ok" if all(checks.values()) else "check_failed")
    write_report(out, sb, cfg, tl, tts, video, animatic, checks, errors, led, mp4, a.test)
    print(json.dumps(checks, indent=2, ensure_ascii=False))
    print(f"\nFile: {mp4}  ({os.path.getsize(mp4) / 1e6:.1f} MB)\nReport: {out / 'render_report.md'}")
    return 0 if all(checks.values()) else 1


def write_report(out, sb, cfg, tl, tts, video, animatic, checks, errors, led, mp4, test):
    L = [f"# Render report — {sb.get('project', '')}", "",
         f"Generato: {datetime.now().isoformat(timespec='seconds')}  ", f"File: `{mp4.name}`", "",
         "## Stato", ""]
    if animatic:
        L += ["**ANIMATIC DI CONTROLLO — NON è il video finale.** Personaggio = pose statiche ritagliate dalla tavola approvata "
              "(spostate e alternate, senza camminata né labiale reali); voce = "
              + ("sintesi offline espeak-ng segnaposto. " if tts == "espeak" else f"{tts} ({cfg.get('elevenlabs_voice_name', '')}). ")
              + "Servono per verificare tempi, grafica tecnica, sottotitoli e montaggio.", ""]
    L += ["## Verifiche automatiche sul file", ""] + [f"- [{'x' if ok else ' '}] {k}" for k, ok in checks.items()] + [""]
    L += ["## Timeline (adattata alla durata reale della voce)", "", "| Scena | Inizio | Durata | Layout | Testo |", "|---|---|---|---|---|"]
    for s in tl:
        L.append(f"| {s['id']} | {s['t0']:.1f}s | {s['dur']:.1f}s | {s.get('layout') or rd.DEFAULT_LAYOUT.get(s['id'], 'talk')} | {s['text'][:70]}… |")
    tot = sum(s["dur"] for s in tl)
    L += ["", f"Durata totale: {tot:.1f}s (obiettivo storyboard {sb.get('target_duration_seconds')}s; la narrazione non è stata compressa).", ""]
    L += ["## Servizi usati e costi", ""]
    spent = 0.0
    for e in led.entries():
        if e.get("service"):
            spent += e.get("est_cost_usd", 0) if e.get("status") == "ok" else 0
            L.append(f"- {e['ts']} {e.get('stage')} {e.get('scene', '')} — {e['service']} — {e.get('status')} — {e.get('est_cost_usd', 0)} USD {e.get('error', '')}")
    L += ["", f"Spesa stimata cumulativa: {spent:.2f} USD", ""]
    L += ["## Errori / avvisi", ""] + ([f"- {x}" for x in errors] or ["- nessuno"]) + [""]
    L += ["## Criteri di accettazione (verifica umana)", ""]
    notes = {"coerenza volto e occhiali": "N/A nell'animatic (immagine approvata)" if animatic else "da controllare clip per clip",
             "camminata fluida": "NON presente nell'animatic: richiede clip image-to-video" if animatic else "da controllare",
             "mani senza deformazioni evidenti": "N/A animatic" if animatic else "da controllare",
             "sincronizzazione labiale accettabile": "NON presente: serve lip-sync (clip o servizio dedicato)" if animatic else "da controllare",
             "schemi tecnici corretti": "generati da codice (graphics.py): rileggere",
             "testi senza errori": "testi solo da codice/copione: rileggere"}
    L += [f"- [ ] {k} — {notes.get(k, '')}" for k in sb.get("acceptance", [])]
    L += ["", "## Punti di approvazione umana", "",
          "1. Copione e storyboard (`\"approved\": true`).", "2. Test 5–8 s (`approve --key test_clip`).",
          "3. Generazione completa (`approve --key full_generation`).", "4. Voce a pagamento (`approve --key voice_paid`).",
          "5. Revisione finale del MP4 e degli schemi tecnici prima della pubblicazione."]
    (out / ("test_report.md" if test else "render_report.md")).write_text("\n".join(L) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("services")
    p = sub.add_parser("plan"); p.add_argument("--project", required=True); p.add_argument("--out", required=True)
    p = sub.add_parser("approve"); p.add_argument("--out", required=True); p.add_argument("--key", required=True,
                                                                                         choices=["test_clip", "full_generation", "voice_paid"])
    p.add_argument("--max-usd", type=float, required=True); p.add_argument("--note")
    p = sub.add_parser("draft"); p.add_argument("--docs", nargs="+", required=True); p.add_argument("--project", required=True)
    p.add_argument("--seconds", type=int, default=60)
    p = sub.add_parser("build"); p.add_argument("--project", required=True); p.add_argument("--out", required=True)
    p.add_argument("--tts", choices=["espeak", "elevenlabs"]); p.add_argument("--video", choices=["animatic", "fal"])
    p.add_argument("--test", action="store_true", help="solo prima scena, max 8 s"); p.add_argument("--allow-draft", action="store_true")
    p.add_argument("--keyframes-ok", action="store_true", help="fotogrammi di partenza rivisti e approvati")
    a = ap.parse_args()
    return {"services": cmd_services, "plan": cmd_plan, "approve": cmd_approve, "draft": cmd_draft, "build": cmd_build}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.exit(main())
