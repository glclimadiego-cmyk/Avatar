# Richiesta per lo sviluppo del gestionale — pacchetto del videocorso «Nadia, l'assistente»

Da: Diego Gasparini, con la sessione di produzione dei videocorsi.
Data: 16/11/2026.

Prepara il pacchetto `Videocorso_App_Nadia`, **nello stesso formato** dei pacchetti già consegnati (Fotovoltaici, Gestione finanziamenti, Fatturazione, Commesse):
- `LEGGIMI_per_la_produzione.md`
- `Struttura_Corso.pdf`
- `Slide_Nadia.pptx`, con lo spazio per il personaggio e le evidenziazioni come riquadri «Evidenza N»
- `Copione_Voce.docx`
- `Storyboard_Animazione.xlsx`, con gli stessi fogli e le stesse colonne
- `Screenshot_App/`
- `Asset_Grafici/`, con `evidenze.json`
- il capitolo del manuale
- `ISTRUZIONI_DEPOSITO.md`

Quando è pronto, Diego lo porta alla produzione: monto il corso con la regia a tutto schermo e lo deposito in «Da revisionare».

## Destinatari
**Tutti gli interni**: consulenti, front office, ufficio tecnico, fatture e incentivi, marketing, operatori, magazzino, manutenzione, titolare, amministratore.
Ognuno vede solo gli strumenti del suo ruolo, e il corso lo deve dire chiaramente. Dove una funzione vale solo per alcuni ruoli, va indicato per chi.

## Fonti
Solo il **Manuale del gestionale** e il comportamento vero di Nadia, verificati sull'installazione attuale. Sezioni di partenza:
- `nadia` — Nadia, l'assistente in Claude
- `nadia-manuale` — Nadia risponde con il Manuale (v156)
- `nadia.un-connettore-per-tutta-l-azienda`
- `nadia.sul-telefono`
- `nadia.scollega-e-registro` — Scollega e registro (v156)
- `nadia.riferimenti` — Riferimenti (v202)
- `operatore.rapportino` — «✨ Nadia compila il rapportino»
- `profilo.nadia` — l'indirizzo del connettore nel profilo

Se nell'installazione ci sono funzioni di Nadia non ancora descritte nel manuale, aggiungile **solo se verificate**, e segnalale nei «punti aperti».

## Struttura proposta (8 episodi, 1–2 minuti l'uno)
| Ep. | Nome per il deposito | Titolo | Contenuto |
|---|---|---|---|
| 01 | `01-chi-e-nadia` | Chi è Nadia | assistente dentro l'app Claude, a voce; scrive nel gestionale con il nome e i permessi di chi la usa; chiede conferma prima di scrivere; non inventa: se non sa, lo dice |
| 02 | `02-come-si-collega` | Come si collega | Impostazioni → Connettori → Nadia → Connetti → pagina «Nadia — Luigi Gasparini Srl» con utente e PIN; vale anche sul telefono; in ogni chat si attiva dal «+»; senza PIN non ci si collega |
| 03 | `03-contatti-e-agenda` | Contatti e agenda | «chi devo sentire oggi», ricerca contatto, scheda contatto, riferimenti ulteriori («chi apre la casa di Rossi?»), nuovo contatto, aggiornamento |
| 04 | `04-attivita-e-opportunita` | Attività e opportunità | registra attività, prossima azione, opportunità aperte, situazione generale, tecnici di riferimento |
| 05 | `05-sopralluoghi` | Sopralluoghi | fissare un sopralluogo a voce («segna il sopralluogo da Rossi giovedì alle 10»), relazione di sopralluogo |
| 06 | `06-il-manuale` | Nadia risponde con il Manuale | «come si fa…»; risposta a passi con schermata e pulsante; sezione usata e data; precedenza alle sezioni del proprio ruolo; parti «non ancora nel gestionale»; domande senza risposta nell'elenco del Portale |
| 07 | `07-telefono-e-cantiere` | Sul telefono e in cantiere | calendario e promemoria del telefono, con permesso e conferma; per gli operatori «✨ Nadia compila il rapportino» in GL Operatore |
| 08 | `08-permessi-e-sicurezza` | Permessi e sicurezza | strumenti per ruolo; i consulenti vedono solo i loro contatti; Portale → Impostazioni → Assistente Nadia: chi è collegato, ultimo uso, «Scollega», registro degli accessi; PIN cambiato o utente disattivato: collegamento decaduto entro un minuto |

Corso per il deposito: `nadia`. Titolo del corso: «Nadia, l'assistente».

## Schermate da preparare (con dati di prova, mai dati veri)
**Computer**
1. Claude → Impostazioni → Connettori, con il connettore «Nadia»
2. La pagina «Nadia — Luigi Gasparini Srl» con utente e PIN, vuota
3. Una chat con Nadia attivata dal «+»
4. Conversazioni d'esempio, una per episodio 03–06: domanda e risposta di Nadia, compresa la richiesta di conferma prima di scrivere
5. Una risposta dal Manuale con i passi numerati e la sezione citata
6. Portale → Impostazioni → Assistente Nadia: elenco utenti (collegato, ultimo uso, «Scollega»), registro degli accessi, permessi per ruolo
7. Portale → Impostazioni → «Manuale — domande senza risposta»
8. Il mio profilo → Nadia (indirizzo del connettore)

**Telefono**
9. Claude sul telefono con Nadia attiva
10. Richiesta di conferma prima di creare un appuntamento o un promemoria
11. GL Operatore → rapportino con «✨ Nadia compila il rapportino»

Per ogni schermata servono `evidenze.json` (posizioni dei campi e dei pulsanti da evidenziare) e un'immagine **senza scritte sopra**.

## Regole da riportare nel LEGGIMI
1. Non inventare: solo funzioni verificate.
2. Le parole tra «» sono le etichette vere: vanno scritte identiche.
3. Nelle conversazioni d'esempio: clienti, telefoni, indirizzi e nomi **inventati**. Nessun dato di clienti veri, nessun PIN visibile.
4. Dire sempre che Nadia **chiede conferma** prima di scrivere e che **non inventa**.
5. Dire per chi vale ogni funzione, quando non vale per tutti i ruoli.
6. Schermata a tutto schermo con evidenziazioni, come negli altri corsi (richiesta di Diego del 16/11/2026).
7. Punti aperti: tutto quello che non è ancora definitivo o non è nel manuale.

## Cosa deve tornare alla produzione
Lo zip `Videocorso_App_Nadia.zip`. La produzione monta gli 8 episodi e li deposita in «Da revisionare» del corso `nadia`.
