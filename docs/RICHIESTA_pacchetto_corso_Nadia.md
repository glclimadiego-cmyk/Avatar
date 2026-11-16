# Richiesta per lo sviluppo del gestionale — pacchetto del videocorso «Nadia, l'assistente»

Da: Diego Gasparini, con la sessione di produzione dei videocorsi.
Data: 16/11/2026.

## Parte A — Prima del corso: nuove funzioni di Nadia sui dati dei clienti (priorità di Diego)

**Stato attuale**, verificato il 16/11/2026 con il profilo titolare: gli strumenti di Nadia sui dati lavorano solo sui **lead commerciali**, cioè agenda, ricerca e scheda contatto, attività, prossima azione, opportunità, situazione generale, sopralluoghi e tecnici di riferimento. A questi si aggiungono il Manuale e il giornale incentivi.
Nadia **non legge** commesse, pratiche di finanziamento, pratiche fotovoltaiche, fatture e manutenzioni. A una domanda come «il finanziamento di Rossi è passato?» oggi può solo dire dove guardare.

**Obiettivo:** Diego vuole che il personale possa fare a Nadia domande **trasversali su tutti i dati di un cliente**, in linguaggio naturale. Esempi:
- «Il finanziamento di Rossi Mario è passato?»
- «A che punto è la commessa di via Roma a Treviso?»
- «La pratica GSE del fotovoltaico di Bianchi è chiusa?»
- «Rossi ha fatture da pagare?» · «Quando scade la manutenzione della caldaia di Verdi?»
- «Quali documenti stiamo ancora aspettando da Neri?»
- «Quali finanziamenti sono in istruttoria da più di 10 giorni?»

**Strumenti da aggiungere, tutti in sola lettura:**
| Strumento | Cosa restituisce |
|---|---|
| `cerca_cliente` | clienti dell'anagrafica per nome, telefono, email, comune o indirizzo, con l'id. Se ci sono omonimi Nadia chiede quale |
| `riepilogo_cliente` | un colpo d'occhio su tutto: commesse con stato e tappe, pratiche di finanziamento con stato ed esito, pratiche fotovoltaiche con stato GSE, fatture aperte o scadute, manutenzioni e scadenze, documenti richiesti al cliente e ancora mancanti |
| `stato_finanziamento` | per cliente o commessa: stato della pratica (le parole dell'app: «da preparare», «caricata alla finanziaria», «in istruttoria», «sospesa», «approvata», «rifiutata», «erogata», «non serve più»), finanziaria, date dei passaggi, dati definitivi uguali o diversi da quelli firmati |
| `stato_commessa` | tappe e stati, presa in carico, chi la segue, ultime voci della cronologia |
| `pratica_fotovoltaico` | stato della pratica, presa in carico, punti 1–6, stato GSE, documenti mancanti |
| `fatture_cliente` | fatture con stato («bozza», «emessa», «esportata», «incassata»), importi, scadenze, incassi |
| `manutenzioni_cliente` | impianti, prossime scadenze, ultimi interventi |
| `elenchi_per_stato` | domande per gruppo: per esempio finanziamenti «in istruttoria» da più di N giorni, commesse ferme, pratiche oltre il termine |

**Regole:**
- **Permessi per ruolo**, come oggi:
  - ognuno vede solo quello che vede nelle sue app;
  - i consulenti vedono solo i loro clienti;
  - gli importi, i margini e i costi interni li vedono solo i ruoli che li vedono già nel gestionale.
- **Sola lettura:** queste funzioni non modificano nulla. Le scritture restano quelle di oggi, con conferma.
- **Registro:** ogni consultazione finisce nel registro degli accessi di Nadia (chi, quando, quale cliente).
- **Risposte con la fonte:** Nadia dice da quale app viene il dato e di quando è («Gestione finanziamenti, aggiornato il …»). Se il dato non c'è, lo dice, senza dedurlo.
- **Manuale:** va aggiornato con un capitolo su queste domande, che sarà la fonte del corso.

Quando le funzioni sono pronte e collaudate, si prepara il pacchetto del corso (Parte B).

## Parte B — Il pacchetto del videocorso

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

## Struttura proposta (9 episodi, 1–2 minuti l'uno)
| Ep. | Nome per il deposito | Titolo | Contenuto |
|---|---|---|---|
| 01 | `01-chi-e-nadia` | Chi è Nadia | assistente dentro l'app Claude, a voce; scrive nel gestionale con il nome e i permessi di chi la usa; chiede conferma prima di scrivere; non inventa: se non sa, lo dice |
| 02 | `02-come-si-collega` | Come si collega | Impostazioni → Connettori → Nadia → Connetti → pagina «Nadia — Luigi Gasparini Srl» con utente e PIN; vale anche sul telefono; in ogni chat si attiva dal «+»; senza PIN non ci si collega |
| 03 | `03-contatti-e-agenda` | Contatti e agenda | «chi devo sentire oggi», ricerca contatto, scheda contatto, riferimenti ulteriori («chi apre la casa di Rossi?»), nuovo contatto, aggiornamento |
| 04 | `04-attivita-e-opportunita` | Attività e opportunità | registra attività, prossima azione, opportunità aperte, situazione generale, tecnici di riferimento |
| 05 | `05-domande-sui-clienti` | Domande sui clienti | **(dopo la Parte A)** «il finanziamento di Rossi è passato?», «a che punto è la commessa?», «ha fatture da pagare?», «che documenti aspettiamo?», gli elenchi per stato; Nadia cita da quale app viene il dato e di quando è; cosa vede ogni ruolo |
| 06 | `06-sopralluoghi` | Sopralluoghi | fissare un sopralluogo a voce («segna il sopralluogo da Rossi giovedì alle 10»), relazione di sopralluogo |
| 07 | `07-il-manuale` | Nadia risponde con il Manuale | «come si fa…»; risposta a passi con schermata e pulsante; sezione usata e data; precedenza alle sezioni del proprio ruolo; parti «non ancora nel gestionale»; domande senza risposta nell'elenco del Portale |
| 08 | `08-telefono-e-cantiere` | Sul telefono e in cantiere | calendario e promemoria del telefono, con permesso e conferma; per gli operatori «✨ Nadia compila il rapportino» in GL Operatore |
| 09 | `09-permessi-e-sicurezza` | Permessi e sicurezza | strumenti per ruolo; i consulenti vedono solo i loro contatti; Portale → Impostazioni → Assistente Nadia: chi è collegato, ultimo uso, «Scollega», registro degli accessi; PIN cambiato o utente disattivato: collegamento decaduto entro un minuto |

Corso per il deposito: `nadia`. Titolo del corso: «Nadia, l'assistente».

## Schermate da preparare (con dati di prova, mai dati veri)
**Computer**
1. Claude → Impostazioni → Connettori, con il connettore «Nadia»
2. La pagina «Nadia — Luigi Gasparini Srl» con utente e PIN, vuota
3. Una chat con Nadia attivata dal «+»
4. Conversazioni d'esempio, una per episodio 03–07, con **almeno 5 domande trasversali sui clienti** per l'episodio 05 (finanziamento passato, stato commessa, pratica GSE, fatture da pagare, documenti mancanti) e una domanda con omonimi in cui Nadia chiede quale cliente: domanda e risposta di Nadia, compresa la richiesta di conferma prima di scrivere
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
5. Dire per chi vale ogni funzione, quando non vale per tutti i ruoli; nelle domande sui clienti mostrare che un consulente vede solo i suoi clienti.
6. Schermata a tutto schermo con evidenziazioni, come negli altri corsi (richiesta di Diego del 16/11/2026).
7. Punti aperti: tutto quello che non è ancora definitivo o non è nel manuale.

## Cosa deve tornare alla produzione
Prima la conferma che le funzioni della Parte A sono attive, collaudate e descritte nel Manuale. Poi lo zip `Videocorso_App_Nadia.zip`. La produzione monta i 9 episodi e li deposita in «Da revisionare» del corso `nadia`.
