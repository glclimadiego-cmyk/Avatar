# Render report — Pompa di calore - pilota 3D cartoon

Generato: 2026-11-15T20:46:17  
File: `test.mp4`

## Stato

## Verifiche automatiche sul file

- [x] risoluzione 1920x1080
- [x] 25 fps
- [x] video H.264
- [x] audio AAC
- [x] durata ~8.0s (misurata 8.00s)

## Timeline (adattata alla durata reale della voce)

| Scena | Inizio | Durata | Layout | Testo |
|---|---|---|---|---|
| S01 | 0.0s | 10.4s | walk_in | Ciao! Oggi scopriamo come funziona una pompa di calore e perché può ri… |
| S02 | 10.4s | 10.6s | walk_to_monitor | Anche quando fuori fa freddo, l'aria contiene energia termica. La pomp… |
| S03 | 21.0s | 13.8s | diagram_cycle | Il refrigerante evapora assorbendo calore, il compressore ne aumenta p… |
| S04 | 34.8s | 14.1s | hydronic | Con l'energia elettrica necessaria al compressore, il sistema può tras… |
| S05 | 48.9s | 8.9s | closeup | Nei prossimi episodi vedremo come dimensionarla, installarla e farla l… |

Durata totale: 57.8s (obiettivo storyboard 60s; la narrazione non è stata compressa).

## Servizi usati e costi

- 2026-11-15T19:40:44+00:00 voice  — espeak-ng (locale) — ok — 0.0 USD 
- 2026-11-15T19:40:44+00:00 voice  — espeak-ng (locale) — ok — 0.0 USD 
- 2026-11-15T19:40:44+00:00 voice  — espeak-ng (locale) — ok — 0.0 USD 
- 2026-11-15T19:40:44+00:00 voice  — espeak-ng (locale) — ok — 0.0 USD 
- 2026-11-15T19:40:45+00:00 voice  — espeak-ng (locale) — ok — 0.0 USD 
- 2026-11-15T20:43:01+00:00 keyframe S01 — fal:fal-ai/nano-banana-2/edit — ok — 0.12 USD 
- 2026-11-15T20:46:01+00:00 clip S01 — fal:fal-ai/kling-video/v2.5-turbo/pro/image-to-video — ok — 0.7 USD 

Spesa stimata cumulativa: 0.82 USD

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
