# Corso «Pompe di calore» — report di produzione

Data: 16/11/2026.

## Risultato

- 6 episodi: **01 Come funziona** (pilota, rifatto con la voce clonata di Diego, 0:54) + episodi 02–06 (32 scene, 9:50).
- 1920×1080, 25 fps, H.264 + AAC, sottotitoli italiani incorporati. Deposito: corso `pompe-di-calore`, episodi «Da revisionare».

| Ep. | Titolo | Durata |
|---|---|---|
| 01 | Come funziona (pilota) | 0:54 |
| 02 | I tipi di pompa di calore | 2:13 |
| 03 | COP, SCOP e temperatura di mandata | 1:56 |
| 04 | Il dimensionamento | 2:02 |
| 05 | L'installazione | 1:59 |
| 06 | Efficienza e manutenzione | 1:40 |

## Contenuti

Copioni scritti da Claude e approvati da Diego (`corsi/pompe-di-calore/COPIONI_episodi_02-06.md`). Nessun valore normativo o di prodotto inventato; l'unico numero (COP 4) è dichiarato come esempio. Incentivi esclusi.

## Come è fatto

- **Schemi tecnici**: 22 schemi disegnati da codice (`pipeline/schemi_pdc.py`), stessa grafica delle slide dei corsi sulle app.
- **Pacchetto slide/storyboard** generato da codice (`pipeline/corso_pdc.py`) e montato con `pipeline/course_render.py` con la regia a tutto schermo: la slide si ingrandisce, l'avatar esce, evidenziatori sulle parti spiegate, ritorno con l'avatar.
- **Scene 3D** (fal.ai, Kling 2.5 Turbo Pro): un'apertura diversa per episodio (modello di pompa di calore, pannello di regolazione, disegno della casa, unità esterna in giardino, pulizia della batteria) e una chiusura comune; titolo dell'episodio in sovrimpressione.
- **Voce**: clone della voce di Diego (Eleven v4).

## Costi

- fal.ai: **5.86 $** (7 fotogrammi di partenza + 2 rigenerati, 6 clip + 1 rigenerata; tetto autorizzato 12 $).
- ElevenLabs: 7948 caratteri, compresi nell'abbonamento.

## Limiti

- Labiale non sincronizzato; nelle scene 3D il personaggio parla in modo generico.
- La chiusura 3D è la stessa per gli episodi 02–06 (cambia il testo parlato).
- Le clip 3D sono rallentate fino a 1,5× per coprire la voce; oltre, l'ultimo fotogramma resta fermo per pochi istanti.
