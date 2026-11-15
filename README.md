# Avatar — pipeline videocorsi 3D cartoon

Pipeline automatica: **documenti → sceneggiatura approvata → scene → audio → MP4 1080p + SRT**,
senza lavoro manuale in programmi di animazione.

- `pilota/` — pacchetto del pilota "pompa di calore" (copione, storyboard, tavola avatar, scena di riferimento) + `course.json` (servizi, tariffe, prompt).
- `pipeline/` — codice:
  - `make_course.py` comando unico (`services`, `draft`, `plan`, `approve`, `build`)
  - `providers.py` TTS (espeak-ng offline / ElevenLabs), fal.ai (keyframe + image-to-video), registro costi e approvazioni
  - `graphics.py` grafica tecnica vettoriale controllata (tutte le scritte nascono qui, mai nelle clip AI)
  - `render.py` timeline sulla durata reale della voce, SRT, compositing Pillow → FFmpeg (H.264/AAC, sottotitoli mov_text)
  - `sprites.py` ritaglio pose dalla tavola approvata (solo per l'animatic di controllo)
- `output/pilota/` — risultato attuale: **animatic di controllo** (`pilot.mp4`, `test.mp4`, `pilot.srt`, `render_report.md`, `ledger.jsonl`).

## Uso

```bash
pip install pillow numpy            # + apt-get install espeak-ng ffmpeg
python3 pipeline/make_course.py services
python3 pipeline/make_course.py build --project pilota --out output/pilota            # animatic gratuito
python3 pipeline/make_course.py plan  --project pilota --out output/pilota            # costi previsti
# dopo aver impostato FAL_KEY e consentito la rete:
python3 pipeline/make_course.py approve --out output/pilota --key test_clip --max-usd 3
python3 pipeline/make_course.py build --project pilota --out output/pilota --video fal --test
# dopo approvazione del test:
python3 pipeline/make_course.py approve --out output/pilota --key full_generation --max-usd 15
python3 pipeline/make_course.py approve --out output/pilota --key voice_paid --max-usd 1
python3 pipeline/make_course.py build --project pilota --out output/pilota --video fal --tts elevenlabs
```

Nuovo episodio: `make_course.py draft --docs doc1.pdf note.md --project corsi/ep02` (richiede `ANTHROPIC_API_KEY`),
rileggere `copione.md`/`storyboard.json`, impostare `"approved": true`, poi `build`.

## Punti di approvazione umana (bloccanti nel codice)

1. Copione/storyboard (`"approved": true`) 2. spesa test (`test_clip`) 3. spesa generazione completa (`full_generation`)
4. voce a pagamento (`voice_paid`) 5. revisione finale MP4. Ogni chiamata e costo stimato va in `ledger.jsonl`; i tetti di spesa sono applicati.
