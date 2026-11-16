# Corso «Fotovoltaici» — report di produzione

Data: 16/11/2026. Pagina di visione (privata): https://claude.ai/artifact/LmbW4VSnPnSPp4ntihhESd

## Risultato

- 38 scene in 10 capitoli, durata totale **14:00**, 1920×1080, 25 fps, H.264 + AAC, sottotitoli italiani incorporati.
- File (non in Git, materiale interno): `output/fotovoltaici/corso_fotovoltaici.mp4` + `.srt`, un file per capitolo in `output/fotovoltaici/capitoli/` (`capitolo_NN.mp4` + `.srt`).

| Cap. | Titolo | Scene | Durata |
|---|---|---|---|
| 1 | A cosa serve l'app e chi la usa | 1–3 | 1:06 |
| 2 | Le pratiche nascono da sole | 4–6 | 1:18 |
| 3 | L'elenco: numeri in alto, filtri, ricerca | 7–10 | 1:19 |
| 4 | Presa in carico entro un giorno lavorativo | 11–14 | 1:23 |
| 5 | Punto 1: l'impianto e i documenti dei prodotti | 15–17 | 0:59 |
| 6 | Punto 2: tempi e modalità di posa | 18–20 | 0:57 |
| 7 | Punto 3: documenti per la pratica GSE | 21–25 | 1:51 |
| 8 | Chiedere i documenti al cliente | 26–29 | 1:40 |
| 9 | Punti 4 e 5: pratica GSE e dichiarazione di conformità | 30–33 | 1:30 |
| 10 | Punto 6: chiudere la pratica, e gli errori da evitare | 34–38 | 1:52 |

## Come è fatto

- **Sfondo**: le slide del pacchetto (`Slide_Fotovoltaico.pptx`) trasformate in immagini con LibreOffice (carattere Segoe UI sostituito da Open Sans).
- **Evidenziazioni**: quelle già disegnate nelle slide (riquadri numerati e frecce), fatte comparire una alla volta durante il parlato; zoom leggero (ancorato in alto) nelle scene in cui lo storyboard lo chiede.
- **Schermate secondarie** a metà scena: scena 6 (pc-24), 13 (pc-08), 31 (pc-21); scena 3: telefono (tel-01) accanto al personaggio.
- **Voce**: clone della voce di Diego (ElevenLabs, modello Eleven v4), testo dello storyboard parola per parola (etichette tra «» lette senza emoji); circa 158 parole/minuto.
- **Personaggio**: pacchetto di 8 clip riutilizzabili (avatar 3D approvato, fondo verde scontornato); cambia lato a ogni scena camminando; gesti dallo storyboard (saluta, indica, conta, telefono, pollice, attenzione), nei tratti lunghi torna a indicare la schermata.
- **Durate**: voce reale + pause per mostrare le operazioni (più evidenziazioni o una seconda schermata = più tempo). Il pacchetto stimava 17:48 con una lettura più lenta.

## Costi

- fal.ai per questo corso: **0 $** (riusato il pacchetto clip; il pacchetto è costato 5,42 $ una tantum).
- ElevenLabs: 11450 caratteri, compresi nell'abbonamento Creator.

## Limiti noti

- Labiale non sincronizzato con la voce (la clip «parla» muove la bocca in modo generico).
- Le pose cambiano con una breve dissolvenza (0,2 s); la camminata è sul posto con spostamento orizzontale.
- Alcuni effetti descritti nello storyboard non sono riprodotti alla lettera: animazioni interne agli schemi (le tappe che compaiono una a una, il foglio che si attacca al prodotto, l'effetto scatto fotografico, lo sfondo diverso per il telefono del cliente). Gli schemi compaiono interi.
- Punti aperti del pacchetto rispettati: elenco documenti GSE presentato come «di partenza»; riquadro «Storia» mostrato in breve.

## Rifare o aggiornare

```bash
python3 pipeline/course_render.py prepara      # slide, maschere, pose
python3 pipeline/course_render.py voce         # solo le scene con testo cambiato
python3 pipeline/course_render.py capitoli [N] # uno o più capitoli
python3 pipeline/course_render.py corso        # unione e SRT completo
```
