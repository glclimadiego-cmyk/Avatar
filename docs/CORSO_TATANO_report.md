# Corsi «Tatano Kalorina Mini K30» — report di produzione

Data: 19/11/2026. Richiesta di Diego: un video per i commerciali e uno per i tecnici sulla caldaia a biomassa Tatano Kalorina Mini K30.

## Fonti

Nessun pacchetto dallo sviluppo: copione, schemi e slide sono scritti da noi, solo con quello che c'è nei documenti del costruttore trovati su Google Drive (cartella TATANO):
- depliant commerciale «Kalorina Mini K / Low Emission» (versione attuale: 4,5-32 kW, 94,5 %, Classe 5 secondo EN 303-5:2021+A1:2022, 5 stelle, incentivi Conto Termico 3.0);
- «Libretto di installazione uso e manutenzione Mini 20-30», edizione 07/2019 rev. 04 (installazione, manutenzione, centralina SY400, errori Er01-Er35, ricambi);
- «Descrizione tecnica low emission» (gamma 110-400 kW: usata solo per non confonderla con la Mini) e un rapporto di collaudo (altro modello, con dati personali: usata solo la struttura dei controlli).

Testi e schemi restano in `corsi/tatano-*/materiale` (fuori da git). Il programma che costruisce slide e storyboard è `pipeline/corso_da_contenuto.py`.

## Corso per i commerciali — corso `tatano-mini-k30-commerciale`

21 scene, **10:50**.

| Episodio | Titolo | Scene | Durata |
|---|---|---|---|
| `01-il-prodotto` | Il prodotto in breve | 1–3 | 1:34 |
| `02-perche-la-biomassa` | Perché la biomassa | 4–5 | 1:02 |
| `03-punti-di-forza` | I punti di forza | 6–10 | 2:36 |
| `04-incentivi` | Gli incentivi | 11–12 | 1:02 |
| `05-spazi-e-installazione` | Spazi e installazione | 13–15 | 1:36 |
| `06-cosa-dire-al-cliente` | Cosa dire al cliente prima della firma | 16–18 | 1:26 |
| `07-leve-e-sintesi` | Le leve commerciali e la sintesi | 19–21 | 1:31 |

- Cifre del depliant attuale; spazi, canna fumaria e manutenzione dal manuale.
- Incentivi: tabella del Conto Termico 3.0 del depliant, sempre detta come «valore massimo, da verificare dall'ufficio incentivi». Nessun prezzo di listino (scelta di Diego).
- Risparmio rispetto al gasolio detto come stima del costruttore («circa»).

## Corso per i tecnici — corso `tatano-mini-k30-tecnici`

28 scene, **15:25**.

| Episodio | Titolo | Scene | Durata |
|---|---|---|---|
| `01-la-macchina` | La macchina | 1–5 | 2:45 |
| `02-installazione-e-prima-accensione` | Installazione e prima accensione | 6–12 | 3:59 |
| `03-funzionamento-e-centralina` | Funzionamento e centralina | 13–14 | 1:06 |
| `04-manutenzione-utente` | La manutenzione dell'utente | 15–16 | 1:03 |
| `05-manutenzione-annuale` | La manutenzione annuale del tecnico | 17–21 | 2:36 |
| `06-allarmi-e-soluzioni` | Allarmi, problemi e soluzioni | 22–26 | 2:54 |
| `07-errori-e-sintesi` | Errori da evitare e sintesi | 27–28 | 1:00 |

- Basato sul manuale 2019 (scelta di Diego). La prima scena lo dice e avvisa che sulle caldaie più recenti menù e allarmi possono cambiare: valgono le istruzioni della macchina.
- Errori Er01-Er35 con causa e rimedio del manuale; i «problemi senza codice» vengono dai consigli pratici del manuale.

## Punti da sapere

- **Dati diversi tra manuale e depliant**: 31 kW e 93,5 % (manuale 2019) contro 4,5-32 kW e 94,5 % (depliant). Nel corso tecnici è detto a voce che fa fede la targhetta.
- **Montaggio vicino al muro**: il depliant dice che la caldaia si può montare adiacente al muro, il manuale del 2019 chiede 600 mm dietro e a sinistra. Nei video ci sono le distanze del manuale: da verificare con l'ufficio tecnico per il modello attuale.
- **Non presenti nei documenti, quindi non nei video**: consumo di pellet, valvola di scarico termico, intervalli di sostituzione delle guarnizioni, procedura di pulizia manuale del fascio tubiero.
- Pronuncia (solo voce): «K30» = «cappa trenta», «Er01» = «e erre zero uno», «CO2» = «ci o due».

## Costi

- fal.ai: 0 $.
- ElevenLabs: 9050 + 12750 caratteri, compresi nell'abbonamento.
