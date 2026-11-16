# Render report — Pompa di calore - pilota 3D cartoon

Generato: 2026-11-16T08:19:40  
File: `pilot.mp4`

## Stato

## Verifiche automatiche sul file

- [x] risoluzione 1920x1080
- [x] 25 fps
- [x] video H.264
- [x] audio AAC
- [x] durata ~53.7s (misurata 53.70s)
- [x] sottotitoli SRT incorporati

## Timeline (adattata alla durata reale della voce)

| Scena | Inizio | Durata | Layout | Testo |
|---|---|---|---|---|
| S01 | 0.0s | 10.3s | walk_in | Ciao! Oggi scopriamo come funziona una pompa di calore e perché può ri… |
| S02 | 10.3s | 9.5s | walk_to_monitor | Anche quando fuori fa freddo, l'aria contiene energia termica. La pomp… |
| S03 | 19.7s | 13.0s | diagram_cycle | Il refrigerante evapora assorbendo calore, il compressore ne aumenta p… |
| S04 | 32.7s | 12.8s | hydronic | Con l'energia elettrica necessaria al compressore, il sistema può tras… |
| S05 | 45.5s | 8.2s | closeup | Nei prossimi episodi vedremo come dimensionarla, installarla e farla l… |

Durata totale: 53.7s (obiettivo storyboard 60s; la narrazione non è stata compressa).

## Servizi usati e costi

- 2026-11-15T19:40:44+00:00 voice  — espeak-ng (locale) — ok — 0.0 USD 
- 2026-11-15T19:40:44+00:00 voice  — espeak-ng (locale) — ok — 0.0 USD 
- 2026-11-15T19:40:44+00:00 voice  — espeak-ng (locale) — ok — 0.0 USD 
- 2026-11-15T19:40:44+00:00 voice  — espeak-ng (locale) — ok — 0.0 USD 
- 2026-11-15T19:40:45+00:00 voice  — espeak-ng (locale) — ok — 0.0 USD 
- 2026-11-15T20:43:01+00:00 keyframe S01 — fal:fal-ai/nano-banana-2/edit — ok — 0.12 USD 
- 2026-11-15T20:46:01+00:00 clip S01 — fal:fal-ai/kling-video/v2.5-turbo/pro/image-to-video — ok — 0.7 USD 
- 2026-11-15T21:05:46+00:00 voice  — elevenlabs — ok — 0.0 USD 
- 2026-11-15T21:05:48+00:00 voice  — elevenlabs — ok — 0.0 USD 
- 2026-11-15T21:05:52+00:00 voice  — elevenlabs — ok — 0.0 USD 
- 2026-11-15T21:05:55+00:00 voice  — elevenlabs — ok — 0.0 USD 
- 2026-11-15T21:05:57+00:00 voice  — elevenlabs — ok — 0.0 USD 
- 2026-11-15T21:10:30+00:00 keyframe S02 — fal:fal-ai/nano-banana-2/edit — ok — 0.12 USD 
- 2026-11-15T21:10:57+00:00 keyframe S04 — fal:fal-ai/nano-banana-2/edit — ok — 0.12 USD 
- 2026-11-15T21:11:19+00:00 keyframe S05 — fal:fal-ai/nano-banana-2/edit — ok — 0.12 USD 
- 2026-11-15T21:11:58+00:00 keyframe S04 — fal:fal-ai/nano-banana-2/edit — ok — 0.12 USD 
- 2026-11-15T21:15:11+00:00 clip S01 — fal:fal-ai/kling-video/v2.5-turbo/pro/image-to-video — ok — 0.7 USD 
- 2026-11-15T21:17:16+00:00 clip S02 — fal:fal-ai/kling-video/v2.5-turbo/pro/image-to-video — ok — 0.7 USD 
- 2026-11-15T21:19:11+00:00 clip S04 — fal:fal-ai/kling-video/v2.5-turbo/pro/image-to-video — ok — 0.7 USD 
- 2026-11-15T21:21:06+00:00 clip S04 — fal:fal-ai/kling-video/v2.5-turbo/pro/image-to-video — ok — 0.35 USD 
- 2026-11-15T21:23:16+00:00 clip S05 — fal:fal-ai/kling-video/v2.5-turbo/pro/image-to-video — ok — 0.7 USD 
- 2026-11-16T08:18:24+00:00 voice  — elevenlabs — ok — 0.0 USD 
- 2026-11-16T08:18:27+00:00 voice  — elevenlabs — ok — 0.0 USD 
- 2026-11-16T08:18:30+00:00 voice  — elevenlabs — ok — 0.0 USD 
- 2026-11-16T08:18:33+00:00 voice  — elevenlabs — ok — 0.0 USD 
- 2026-11-16T08:18:35+00:00 voice  — elevenlabs — ok — 0.0 USD 

Spesa stimata cumulativa: 4.45 USD

## Errori / avvisi

- nessuno

## Criteri di accettazione (verifica umana)

- [ ] coerenza volto e occhiali — da controllare clip per clip
- [ ] camminata fluida — da controllare
- [ ] mani senza deformazioni evidenti — da controllare
- [ ] sincronizzazione labiale accettabile — da controllare
- [ ] schemi tecnici corretti — generati da codice (graphics.py): rileggere
- [ ] testi senza errori — testi solo da codice/copione: rileggere

## Punti di approvazione umana

1. Copione e storyboard (`"approved": true`).
2. Test 5–8 s (`approve --key test_clip`).
3. Generazione completa (`approve --key full_generation`).
4. Voce a pagamento (`approve --key voice_paid`).
5. Revisione finale del MP4 e degli schemi tecnici prima della pubblicazione.
