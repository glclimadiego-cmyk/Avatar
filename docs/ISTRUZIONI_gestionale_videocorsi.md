# Istruzioni per lo sviluppo del gestionale — App "Video Corsi"

Da: Diego Gasparini, con la sessione Claude che produce i videocorsi.
Per: chi sviluppa il gestionale (persona o sessione Claude).
Data: 15/11/2026.

## Contesto in breve
- Produciamo **videocorsi tecnici 3D** con un avatar di Diego: un presentatore cartoon, voce narrante in italiano, schemi tecnici animati, sottotitoli.
- La produzione è automatica e gira in una **sessione Claude nel cloud**, separata dal gestionale.
- Il primo episodio è pronto: **"Pompe di calore – 01 Come funziona"**, 51 secondi, 1080p.
- Da **costruire nel gestionale**:
  1. un **archivio** dei video sul server aziendale, con copia sulla VPS;
  2. un **punto di deposito** protetto, dove la produzione possa consegnare da sola ogni nuovo episodio;
  3. l'**app "Video Corsi"**, per catalogare, rivedere, pubblicare e guardare i video.

I file del primo episodio **non sono allegati**: li depositerà la produzione appena le darete l'accesso (Parte C).

---

## Parte A — Archivio dei file

### A.1 Dove
- **Server aziendale**: archivio principale e completo.
- **VPS**: copia per la visione online, senza il materiale di lavorazione.
- Copia **in un solo verso**, server → VPS, con `rsync` o `rclone`: dopo ogni consegna o almeno ogni notte.

### A.2 Struttura delle cartelle (uguale su server e VPS)
```
/videocorsi/
  <corso>/                       es. pompe-di-calore
    <NN-episodio>/               es. 01-come-funziona
      finale/     video.mp4  video.srt  video.vtt  poster.jpg  anteprima_mobile.mp4
      progetto/   copione.md  storyboard.json  course.json  timeline.json
      sorgenti/   clips/  keyframes/  voice/        (solo server: serve per rimontare senza ripagare)
      report/     render_report.md  ledger.jsonl  approvals.json  contact_sheet.png
```
- Nomi di corso ed episodio: solo `a-z 0-9 -`, il numero dell'episodio a due cifre.
- Nomi dei file: solo `A-Z a-z 0-9 . _ -`.

### A.3 Spazio
- Server: circa **300 MB per episodio**. Prevedere almeno 50 GB per i primi 100 episodi.
- VPS: circa **35 MB per episodio**.

---

## Parte B — Il punto di deposito (API di consegna)

### B.1 Perché un'API web
La produzione gira nel cloud e può solo fare **richieste HTTPS** verso indirizzi autorizzati:
- **niente** FTP, SFTP, SSH o cartelle condivise;
- l'indirizzo IP di uscita **non è fisso**, quindi la protezione è un **token**, non una lista di IP.

### B.2 Cosa predisporre
1. Un **indirizzo HTTPS** con certificato valido, ad esempio `videocorsi.<dominio>.it`, che punti al server principale.
2. Una piccola **API di deposito** con base `https://<indirizzo>/api/videocorsi/v1`.
3. Un **token dedicato alla produzione**:
   - casuale, di almeno 32 caratteri;
   - salvato sul server solo come hash;
   - revocabile in ogni momento;
   - abilitato **solo** al deposito: non legge il resto del gestionale, non cancella, non pubblica.

### B.3 Le chiamate dell'API
Ogni richiesta porta `Authorization: Bearer <token>`. Le risposte sono in JSON e gli errori hanno un campo `errore` leggibile.

| Chiamata | Scopo |
|---|---|
| `GET /salute` | Prova di collegamento; risponde `{"ok":true,"spazio_libero_gb":…}` |
| `PUT /episodi/{corso}/{NN-episodio}` | Crea o aggiorna la scheda dell'episodio. Ripeterla non crea doppioni |
| `PUT /episodi/{corso}/{NN-episodio}/file/{categoria}/{nome}` | Deposita un file (categoria: `finale`, `progetto`, `sorgenti`, `report`). In `sorgenti` il nome può includere sottocartelle |
| `GET /episodi/{corso}/{NN-episodio}/file` | Elenca i file presenti con dimensione e sha256 |
| `POST /episodi/{corso}/{NN-episodio}/consegna` | Chiude la consegna: verifica, catalogo, copia sulla VPS |

**Scheda episodio**, corpo JSON della seconda chiamata:
```json
{"corso_titolo":"Pompe di calore","episodio_numero":1,
 "episodio_titolo":"La pompa di calore: come funziona","descrizione":"…","durata_s":51.06,
 "scene":[{"inizio_s":0,"titolo":"Ingresso e saluto"},{"inizio_s":9.4,"titolo":"Verso la pompa di calore"}],
 "lingua":"it","stato":"da_revisionare"}
```

**Deposito di un file:**
- **Corpo:** il file grezzo.
- **Intestazioni:** `Content-Type`, `Content-Length` e `X-Content-SHA256` (l'impronta dell'intero file).
- **File grandi:** arrivano a pezzi da circa 50 MB, con `Content-Range: bytes <inizio>-<fine>/<totale>`. Il server li accoda in un file `.part`.
- **Verifica finale:** il server controlla lo sha256. Se non coincide cancella il file e risponde **422**. Se coincide sposta il file al suo posto con una rinomina atomica e risponde **201**.
- **Stesso file già presente:** risponde **200** `{"gia_presente":true}`.
- **Contenuto diverso con lo stesso nome:** risponde **409**. Con `?sovrascrivi=1` sostituisce il file e tiene la versione precedente in `_versioni/`.
- **Nomi non validi**, `..` o percorsi assoluti: risponde **400**.

**Alla chiamata di consegna** il server:
1. controlla che ci siano `finale/video.mp4` e `finale/video.srt`;
2. crea `video.vtt`, `poster.jpg` e `anteprima_mobile.mp4`, se mancano, con i comandi della sezione D.5;
3. importa `report/ledger.jsonl` nei costi di produzione;
4. mette l'episodio in stato **da_revisionare**. **La pubblicazione la decide una persona nell'app, mai la produzione.**

### B.4 Impostazioni del server web (nginx, indicative)
```nginx
client_max_body_size 200m;
proxy_request_buffering off;
client_body_timeout 900s; proxy_read_timeout 900s; proxy_send_timeout 900s;
```
- I file si scrivono **in streaming su disco**, mai interi in memoria.
- Va tenuto un **registro di ogni deposito**: data, token, file, dimensione, esito.
- Va impostato un limite di frequenza delle richieste per token.

### B.5 Collaudo, prima di consegnare l'accesso
```bash
H=https://<indirizzo>/api/videocorsi/v1; T=<token>
curl -fsS -H "Authorization: Bearer $T" $H/salute
curl -fsS -X PUT -H "Authorization: Bearer $T" -H "Content-Type: application/json" \
  -d '{"corso_titolo":"Prova","episodio_numero":99,"episodio_titolo":"Collaudo","stato":"da_revisionare"}' \
  $H/episodi/prova/99-collaudo
S=$(sha256sum prova.mp4 | cut -d' ' -f1)
curl -fsS -X PUT -H "Authorization: Bearer $T" -H "Content-Type: video/mp4" -H "X-Content-SHA256: $S" \
  --data-binary @prova.mp4 $H/episodi/prova/99-collaudo/file/finale/video.mp4
curl -fsS -H "Authorization: Bearer $T" $H/episodi/prova/99-collaudo/file
```
Questi casi **devono fallire**:
- senza token: 401;
- sha256 sbagliato: 422;
- nome con `..`: 400;
- stesso nome con contenuto diverso: 409.

---

## Parte C — Come dare l'accesso alla produzione (Claude)

1. Finito il collaudo B.5, comunicate a Diego:
   - **l'indirizzo esatto**, ad esempio `videocorsi.esempio.it`;
   - **il token**, per una via privata (di persona, messaggio diretto, gestore di password). **Mai in chat, email aperta o documento condiviso.**
   - i limiti reali: dimensione massima per richiesta e spazio libero.
2. Diego torna nella sessione di produzione e scrive l'indirizzo. Claude chiede di autorizzarlo nella sua rete, e Diego approva.
3. Claude apre un **modulo sicuro**, Diego vi incolla il token. Il token viene aggiunto alle richieste dal sistema: Claude non lo vede e non lo scrive da nessuna parte.
4. Claude prova `GET /salute`, poi deposita il primo episodio completo (finale, progetto, sorgenti, report) e chiama la **consegna**.
5. L'episodio compare nell'app nella pagina **"Da revisionare"**. Diego lo guarda e preme **Pubblica**.

Per revocare l'accesso basta disattivare il token sul server.

**Alternativa possibile:** una nuova funzione nel servizio **Nadia**, ad esempio `importa_file_videocorso(corso, episodio, categoria, nome, url, sha256)`, con cui il **server scarica** il file da un link. Le chiamate a Nadia hanno un limite di circa 4 MB, quindi i file non possono passare dentro la chiamata. L'API della Parte B resta la soluzione consigliata.

---

## Parte D — L'app "Video Corsi"

### D.1 Ruoli
| Ruolo | Può fare |
|---|---|
| Amministratore (Diego) | tutto: rivedere, pubblicare, archiviare, vedere costi e materiale di lavorazione |
| Tecnico interno | guardare i corsi pubblicati per i tecnici, segnare gli episodi come visti |
| Cliente / corsista (fase 2) | guardare solo i corsi assegnati |

La produzione **non è un utente dell'app**: deposita solo tramite l'API.

### D.2 Schermate
1. **Catalogo corsi**: copertina, titolo, numero di episodi, durata, avanzamento personale.
2. **Corso**: episodi in ordine, con stato (per l'amministratore) e "visto / da vedere".
3. **Episodio**:
   - player con sottotitoli italiani;
   - **scaletta delle scene cliccabile**, che porta il video all'istante della scena;
   - descrizione;
   - per l'amministratore: costi e report.
   - Sul telefono parte `anteprima_mobile.mp4`, sul computer `video.mp4`.
4. **Da revisionare** (solo amministratore): player, foglio dei fotogrammi (`report/contact_sheet.png`), report, e i pulsanti **Pubblica**, **Rimanda in produzione** (con nota) e **Archivia**.
5. **Ricerca** su titoli, descrizioni e testo dei sottotitoli, indicizzato alla consegna.

### D.3 Tabelle minime
- **corsi**: id, slug, titolo, descrizione, copertina, destinatari (tecnici/clienti), ordine.
- **episodi**: id, corso_id, numero, slug, titolo, descrizione, durata_s, scene (JSON), stato, cartella, consegnato_il, pubblicato_il, pubblicato_da.
  - Stati: `da_revisionare` → `pubblicato` oppure `da_rifare`, poi `archiviato`.
- **file_episodio**: id, episodio_id, categoria, percorso, dimensione, sha256, presente_su_vps.
- **costi_produzione**: id, episodio_id, data, fase, servizio, modello, secondi, costo_usd, esito, errore.
- **depositi**: registro dell'API (data, token, episodio, file, dimensione, esito).
- **visualizzazioni**: utente, episodio, secondi_visti, completato, ultimo_accesso.
- **accessi_corso** (fase 2): utente o gruppo, corso, dal, al.

### D.4 Visione protetta
- I video non devono avere un indirizzo pubblico fisso.
- L'app verifica i permessi e fornisce un **link temporaneo**, valido poche ore. Si può fare con `secure_link` di nginx oppure con `X-Accel-Redirect` verso una posizione interna.
- Il server web deve supportare le richieste **Range**, per andare avanti e indietro nel video. I file sono già preparati per lo streaming.
- I video si servono dalla **VPS**; il server principale resta l'archivio.

### D.5 Elaborazioni automatiche alla consegna
```bash
ffmpeg -i finale/video.srt finale/video.vtt
ffmpeg -ss 5 -i finale/video.mp4 -frames:v 1 -vf scale=1280:-1 finale/poster.jpg
ffmpeg -i finale/video.mp4 -c:v libx264 -crf 25 -maxrate 2200k -bufsize 4400k -pix_fmt yuv420p \
       -c:a aac -b:a 128k -movflags +faststart finale/anteprima_mobile.mp4
```

### D.6 Traguardi
1. **Archivio e deposito** pronti e collaudati (Parti A e B). Indirizzo e token consegnati a Diego (Parte C). Poi la produzione deposita il primo episodio.
2. **App minima**: catalogo, corso, episodio con player, sottotitoli e scaletta, pagina "Da revisionare" con Pubblica. Solo utenti interni.
3. Ricerca nei sottotitoli, avanzamento di visione, costi per episodio, copia automatica sulla VPS con controllo dello sha256.
4. (Facoltativo) Accesso per clienti e corsisti esterni con corsi assegnati.

### D.7 Sicurezza e privacy
- Il token di deposito può **solo depositare**.
- Le chiavi dei servizi di produzione (generazione video e voce) restano nella produzione: **non** servono al gestionale.
- Il volto di Diego (tavola dell'avatar) ed eventuali campioni della sua voce sono **dati personali**. Vanno tenuti in `progetto/` o `sorgenti/`, visibili solo all'amministratore e mai pubblici.
- Per i corsi rivolti ai clienti servono un'informativa e il registro delle visualizzazioni.

---

## Cosa deve tornare a Diego
1. **Indirizzo esatto** del deposito.
2. **Token** di deposito, per via privata.
3. Esito del **collaudo B.5** e limiti reali (dimensione massima per richiesta, spazio libero).
