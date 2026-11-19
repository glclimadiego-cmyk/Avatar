# Corsi «Tatano Kalorina Mini K30» — report di produzione

Data: 19/11/2026 (seconda versione, con immagini). Richiesta di Diego: un video per i consulenti e uno per i tecnici sulla caldaia a biomassa Tatano Kalorina Mini K30. Nel gestionale il ruolo si chiama «consulenti», non «commerciali»: il codice del corso nel deposito resta `tatano-mini-k30-commerciale`.

## Fonti

Nessun pacchetto dallo sviluppo: copione, schemi e slide sono scritti da noi, solo con quello che c'è nei documenti del costruttore e nelle indicazioni di Diego:
- dal sito tatano.com: depliant «Kalorina Mini K / Low Emission», **scheda tecnica Mini K30 CL5 rev. 05.1 (settembre 2026)**, foto del prodotto e dei particolari, schemi d'impianto;
- dal Drive: «Libretto Mini 20-30», edizione 07/2019 rev. 04 (installazione, manutenzione, centralina SY400, errori Er01-Er35, ricambi);
- indicazioni di Diego: nocciolino e gusci di nocciola come combustibili automatici; legna in modalità stufa con pezzi fino a 50 cm; convenienza anche contro il metano a condensazione;
- prezzi dei combustibili (novembre 2026): rilevazioni dei negozi per il pellet, AIEL per legna e cippato, MASE per il gasolio, comparatori per il metano, schede dei fornitori per nocciolino e gusci.

Testi, foto e illustrazioni restano in `corsi/tatano-*/materiale` (fuori da git). Programmi: `pipeline/corso_da_contenuto.py`, `pipeline/illustrazioni.py`, `pipeline/allinea.py`.

## Corso per i consulenti — corso `tatano-mini-k30-commerciale`, titolo «Tatano Mini K30 · per i consulenti»

27 scene, **14:43**.

| Episodio | Titolo | Scene | Durata |
|---|---|---|---|
| `01-il-prodotto` | Il prodotto in breve | 1–3 | 1:37 |
| `02-perche-la-biomassa` | Perché la biomassa | 4–6 | 1:45 |
| `03-scelta-del-combustibile` | La scelta del combustibile | 7–11 | 3:00 |
| `04-punti-di-forza` | I punti di forza | 12–16 | 2:41 |
| `05-incentivi` | Gli incentivi | 17–18 | 1:01 |
| `06-spazi-e-installazione` | Spazi e installazione | 19–21 | 1:36 |
| `07-cosa-dire-al-cliente` | Cosa dire al cliente prima della firma | 22–24 | 1:26 |
| `08-leve-e-sintesi` | Le leve commerciali e la sintesi | 25–27 | 1:33 |

- Capitolo 3 «La scelta del combustibile»: combustibili automatici (pellet, nocciolino, gusci di nocciola), libertà di scegliere il più conveniente, analisi di mercato con i prezzi di novembre 2026 e l'andamento in un anno, attenzioni (combustibile asciutto, regolazione, Conto Termico).
- Costo del calore utile (stima novembre 2026): nocciolino 40-85 €/MWh, legna circa 70, pellet circa 105, metano a condensazione 150-185, gasolio circa 230. Esempio: casa da 1.500 Smc di metano, 2.100-2.650 € all'anno; con il pellet circa 1.500 €; con il nocciolino 600-1.150 €.
- Gusci di nocciola: convenienti se comprati sfusi dai trasformatori; in sacchi dal rivenditore possono costare quanto il pellet (detto nel video).
- Incentivi: valori massimi del depliant, da verificare dall'ufficio incentivi. Nessun prezzo di listino.

## Corso per i tecnici — corso `tatano-mini-k30-tecnici`

28 scene, **15:42**.

| Episodio | Titolo | Scene | Durata |
|---|---|---|---|
| `01-la-macchina` | La macchina | 1–5 | 2:57 |
| `02-installazione-e-prima-accensione` | Installazione e prima accensione | 6–12 | 4:04 |
| `03-funzionamento-e-centralina` | Funzionamento e centralina | 13–14 | 1:06 |
| `04-manutenzione-utente` | La manutenzione dell'utente | 15–16 | 1:03 |
| `05-manutenzione-annuale` | La manutenzione annuale del tecnico | 17–21 | 2:36 |
| `06-allarmi-e-soluzioni` | Allarmi, problemi e soluzioni | 22–26 | 2:54 |
| `07-errori-e-sintesi` | Errori da evitare e sintesi | 27–28 | 1:00 |

- Dati tecnici dalla scheda tecnica di settembre 2026: 32 kW / 4,5 kW, 94,5 %, A++, 7,16 kg/h di pellet al massimo, 140 W elettrici, **tiraggio 10 Pa ± 20 %** (sotto, obbligatorio il tiraggio forzato). Il manuale del 2019 indicava 31 kW, 93,5 % e 15 Pa: detto nel video, fa fede la targhetta.
- Procedure, menù ed errori Er01-Er35 dal manuale del 2019.

## Immagini

- Foto vere Tatano (sito): caldaia, portello in refrattario, cassetto cenere, pannello touch, estrattore fumi, camera di combustione, dissipatore, app, sonda Lambda, schemi d'impianto, showroom. Il prodotto non è mai generato.
- Illustrazioni generate con fal.ai (nano-banana-2): 22 immagini, **1.76 $** su un tetto di 8 $ autorizzato da Diego il 19/11/2026 (registro: `Illustrazioni/spese_fal.jsonl`).
- Foto delle installazioni nella cartella Drive «TATANO FOTO»: non scaricabili da questa sessione; da aggiungere se Diego le carica.

## Regia

- Le evidenziazioni si accendono quando la voce nomina l'elemento (`tempi_evidenze.json`), e la schermata resta a tutto schermo fino all'ultimo elemento.

## Punti da sapere

- Montaggio vicino al muro: il depliant lo consente, il manuale del 2019 chiede 600 mm dietro e a sinistra; nei video le distanze del manuale. Da verificare con l'ufficio tecnico.
- Prezzi dei combustibili: stime di novembre 2026, da aggiornare a ogni stagione.
- Pronuncia (solo voce): «K30» = «cappa trenta», «Er01» = «e erre zero uno», «CO2» = «ci o due».

## Costi

- fal.ai: 1.76 $ (illustrazioni).
- ElevenLabs: 18096 + 14269 caratteri, compresi nell'abbonamento.
