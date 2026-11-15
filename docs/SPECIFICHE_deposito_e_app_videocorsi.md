# Specifiche per lo sviluppo del gestionale — Deposito file e app "Video Corsi"

Destinatario: chi sviluppa il gestionale (persona o sessione Claude).
Mittente: la sessione di **produzione video** (Claude Code nel cloud) che crea gli episodi.
Data: 15/11/2026. Leggere insieme a «Passaggio di consegne – Video Corsi», nella stessa cartella Drive.

Gli obiettivi sono due:
1. **Deposito:** predisporre sul server un punto di consegna dove la produzione video possa depositare da sola video e materiali di ogni episodio.
2. **App:** costruire nel gestionale l'app **"Video Corsi"**, che cataloga, protegge e mostra quei video.

---

## Parte A — Il deposito dei file

### A.1 Vincoli della produzione video (perché è fatto così)
- La produzione gira in un **contenitore cloud** che può fare **solo richieste HTTPS in uscita** verso indirizzi autorizzati uno per uno. **Niente FTP, SFTP, SSH o cartelle condivise.**
- L'indirizzo IP di uscita **non è fisso**: non si può proteggere il deposito con una lista di IP. La protezione è un **token**.
- Il token viene inserito da Diego in un **modulo sicuro** e aggiunto automaticamente alle richieste. Non passa mai in chat, nel codice o nei log della produzione.
- Ogni episodio pesa da 30 MB (solo finale) a 300 MB (con i sorgenti). I singoli file arrivano a circa 100 MB e possono crescere.

Il deposito è quindi una **piccola API HTTPS di caricamento** sul server (o sulla VPS), protetta da token.

### A.2 Cosa deve essere predisposto
1. **Un nome a dominio con HTTPS valido**, ad esempio `videocorsi.<dominio-aziendale>.it` (certificato Let's Encrypt o equivalente). Serve il **nome esatto**: va inserito nella lista degli indirizzi autorizzati della produzione.
2. **Un token dedicato** alla produzione video:
   - lungo almeno 32 caratteri casuali;
   - valido **solo** per le operazioni di deposito qui sotto: niente lettura del resto del gestionale, niente cancellazioni;
   - revocabile in ogni momento;
   - salvato sul server **solo come hash**.
3. **La cartella di archivio** `/videocorsi/` sul server principale, con lo spazio disco necessario (vedi A.6).
4. **La replica sulla VPS**: dopo ogni deposito andato a buon fine, o almeno ogni notte, copia in un solo verso, server → VPS (`rsync` o `rclone`). Sulla VPS non serve la sottocartella `sorgenti/`.

### A.3 Struttura dell'archivio
```
/videocorsi/
  <corso>/                         es. pompe-di-calore
    <NN-episodio>/                 es. 01-come-funziona
      finale/     video.mp4  video.srt  video.vtt  poster.jpg  anteprima_mobile.mp4
      progetto/   copione.md  storyboard.json  course.json  timeline.json
      sorgenti/   clips/…  keyframes/…  voice/…           (solo sul server principale)
      report/     render_report.md  ledger.jsonl  approvals.json  contact_sheet.png
```
Regole per i nomi:
- corso ed episodio rispettano `^[a-z0-9-]{1,60}$`, il numero ha due cifre;
- i file rispettano `^[A-Za-z0-9._-]{1,120}$`;
- dentro `sorgenti/` sono ammesse sottocartelle con le stesse regole.

Qualsiasi altro nome, `..` o percorso assoluto va **rifiutato** con errore 400.

### A.4 L'API di deposito (contratto)

Indirizzo di base: `https://<host>/api/videocorsi/v1`.
Ogni richiesta porta l'intestazione `Authorization: Bearer <token>`. Le risposte sono in JSON. Gli errori usano gli stati 400, 401, 403, 404, 409, 413 e 422, con un campo `errore` leggibile.

| # | Metodo e percorso | Cosa fa |
|---|---|---|
| 1 | `GET /salute` | Prova di collegamento: risponde `{"ok":true,"spazio_libero_gb":…}` |
| 2 | `PUT /episodi/{corso}/{NN-episodio}` | Crea o aggiorna la scheda dell'episodio (vedi sotto). Ripeterla non crea doppioni |
| 3 | `PUT /episodi/{corso}/{NN-episodio}/file/{categoria}/{percorso}` | Carica un file. Il corpo della richiesta è il file grezzo |
| 4 | `GET /episodi/{corso}/{NN-episodio}/file` | Elenca i file presenti con dimensione e sha256, così la produzione salta quelli già consegnati |
| 5 | `POST /episodi/{corso}/{NN-episodio}/consegna` | Dichiara la consegna completa: il server verifica i file, aggiorna il catalogo e avvia la replica sulla VPS |

**Richiesta 2: corpo della scheda episodio**
```json
{
  "corso_titolo": "Pompe di calore",
  "episodio_numero": 1,
  "episodio_titolo": "La pompa di calore: come funziona",
  "descrizione": "…",
  "durata_s": 51.06,
  "scene": [{"inizio_s": 0, "titolo": "Ingresso e saluto"}, {"inizio_s": 9.4, "titolo": "…"}],
  "lingua": "it",
  "stato": "da_revisionare"
}
```

**Richiesta 3: caricamento di un file**
- `categoria` è una di `finale`, `progetto`, `sorgenti`, `report`.
- Intestazioni obbligatorie:
  - `Content-Type`;
  - `Content-Length`;
  - `X-Content-SHA256`: l'impronta dell'intero file, in esadecimale.
- **File grandi a pezzi:** se presente l'intestazione `Content-Range: bytes <inizio>-<fine>/<totale>`, il server accoda il pezzo a un file temporaneo `.part`. Il file è completo quando arriva l'ultimo byte. La produzione invierà pezzi da circa 50 MB.
- Alla fine il server:
  - calcola lo sha256 e lo confronta con quello dichiarato; se non coincide, cancella il file e risponde **422**;
  - sposta il file al suo posto con una rinomina atomica.
- **Nessuna sovrascrittura silenziosa:** se il file esiste già con lo stesso sha256 risponde `200 {"gia_presente":true}`. Se esiste con un contenuto diverso risponde **409**. Con `?sovrascrivi=1` sostituisce il file e conserva la versione precedente in `…/_versioni/`.
- Risposta: `201 {"percorso":"…","dimensione":…,"sha256":"…"}`.

**Richiesta 5: consegna**
- Il server controlla che ci siano almeno `finale/video.mp4` e `finale/video.srt`.
- Se manca, genera da solo `video.vtt` (`ffmpeg -i video.srt video.vtt`), `poster.jpg` e `anteprima_mobile.mp4` (comandi in Parte B).
- Importa `report/ledger.jsonl` nella tabella dei costi.
- Mette l'episodio in stato `da_revisionare`. **La pubblicazione la decide una persona nell'app, mai la produzione.**

### A.5 Impostazioni del server web (nginx, indicative)
```nginx
client_max_body_size 200m;          # ogni pezzo o file singolo; i file più grandi arrivano a pezzi
proxy_request_buffering off;        # scrive su disco mentre riceve
proxy_read_timeout 900s; proxy_send_timeout 900s; client_body_timeout 900s;
limit_req zone=deposito burst=20;   # limite di frequenza per token
```
I file vanno scritti in **streaming su disco**, mai caricati interi in memoria. Va tenuto un registro di ogni deposito: data, token usato, file, dimensione, esito.

### A.6 Spazio disco
- Server principale: circa **300 MB per episodio** con i sorgenti. Prevedere almeno 50 GB per i primi 100 episodi.
- VPS: circa **35 MB per episodio**, senza sorgenti.

### A.7 Cosa restituire a Diego (che lo passa alla produzione)
1. Il **nome esatto dell'host**, ad esempio `videocorsi.esempio.it`.
2. Il **token**. Va consegnato a Diego per una via privata, non in chat: Diego lo inserirà nel modulo sicuro della produzione.
3. La conferma che `GET /salute` funziona, e i limiti effettivi: dimensione massima per richiesta, spazio libero.

### A.8 Collaudo (da eseguire prima di consegnare)
```bash
H=https://<host>/api/videocorsi/v1; T=<token>
curl -fsS -H "Authorization: Bearer $T" $H/salute
curl -fsS -X PUT -H "Authorization: Bearer $T" -H "Content-Type: application/json" \
     -d '{"corso_titolo":"Prova","episodio_numero":99,"episodio_titolo":"Collaudo","stato":"da_revisionare"}' \
     $H/episodi/prova/99-collaudo
S=$(sha256sum prova.mp4 | cut -d' ' -f1)
curl -fsS -X PUT -H "Authorization: Bearer $T" -H "Content-Type: video/mp4" -H "X-Content-SHA256: $S" \
     --data-binary @prova.mp4 $H/episodi/prova/99-collaudo/file/finale/video.mp4
curl -fsS -H "Authorization: Bearer $T" $H/episodi/prova/99-collaudo/file
# casi che DEVONO fallire: token assente (401), sha256 sbagliato (422), nome con ".." (400), stesso file con contenuto diverso (409)
```

### A.9 In alternativa (o in aggiunta): funzione in Nadia
Se è più semplice, si può aggiungere al servizio Nadia uno strumento `importa_file_videocorso(corso, episodio, categoria, nome, url, sha256)`. Il **server scarica** il file dall'indirizzo indicato, per esempio un link GitHub o un link temporaneo, controlla l'impronta e lo archivia come in A.3. In questo caso la produzione invia a Nadia solo indirizzi, e il limite di circa 4 MB per chiamata a Nadia non conta. Il server deve però poter raggiungere la sorgente del file. Per i repository privati GitHub serve un token in sola lettura **sul server**.

---

## Parte B — L'app "Video Corsi" nel gestionale

### B.1 Chi la usa
| Ruolo | Può fare |
|---|---|
| **Amministratore** (Diego) | tutto: rivede, pubblica, archivia, vede costi e materiale di lavorazione |
| **Tecnico interno** | vede i corsi pubblicati per i tecnici, segna gli episodi come visti |
| **Cliente / corsista esterno** (eventuale, fase 2) | vede solo i corsi a lui assegnati |

La produzione video **non è un utente dell'app**: deposita tramite l'API (Parte A) e non può pubblicare.

### B.2 Schermate
1. **Catalogo corsi**: schede con copertina (`poster.jpg`), titolo, numero di episodi, durata totale, avanzamento personale.
2. **Corso**: elenco episodi in ordine, con stato (per l'amministratore) e "visto / da vedere" (per gli altri).
3. **Episodio**:
   - player video con sottotitoli italiani attivabili;
   - **scaletta delle scene** cliccabile, che porta il video all'istante della scena;
   - descrizione;
   - per l'amministratore: costi e report.
   - Sul telefono parte in automatico `anteprima_mobile.mp4`, sul computer `video.mp4`.
4. **Da revisionare** (solo amministratore):
   - episodi appena consegnati, con player, foglio fotogrammi (`report/contact_sheet.png`) e report;
   - pulsanti **Pubblica**, **Rimanda in produzione** (con nota) e **Archivia**.
5. **Ricerca** su titoli, descrizioni e testo dei sottotitoli. Il testo dei sottotitoli si indicizza alla consegna, così si trova anche "condensatore" o "COP".

### B.3 Dati (tabelle minime)
- **corsi**: id, slug, titolo, descrizione, copertina, pubblico (tecnici / clienti), ordinamento, creato_il.
- **episodi**: id, corso_id, numero, slug, titolo, descrizione, durata_s, scene (JSON), stato, cartella, consegnato_il, pubblicato_il, pubblicato_da.
  - Stati: `da_revisionare` → `pubblicato` / `da_rifare` → `archiviato`.
- **file_episodio**: id, episodio_id, categoria, percorso, dimensione, sha256, presente_su_vps, creato_il.
- **costi_produzione**: id, episodio_id, data, fase (keyframe, clip, voce), servizio, modello, secondi, costo_usd, esito, errore. Si importa da `ledger.jsonl`.
- **depositi** (registro dell'API): id, data, token_id, episodio, file, dimensione, esito.
- **visualizzazioni**: utente_id, episodio_id, secondi_visti, completato, ultimo_accesso.
- **accessi_corso** (fase 2, clienti): utente_id o gruppo, corso_id, dal, al.

### B.4 Riproduzione protetta
- I video **non** devono essere raggiungibili da un indirizzo pubblico fisso.
- Il gestionale verifica i permessi e risponde con un **link temporaneo**, valido poche ore. Due modi:
  - nginx `secure_link` (firma e scadenza nell'indirizzo);
  - `X-Accel-Redirect` verso una location `internal`.
- Il server web deve supportare le richieste **Range**, che servono per andare avanti e indietro nel video. nginx lo fa già; i file sono pronti per lo streaming (`+faststart`).
- Sottotitoli serviti come `.vtt` dallo stesso meccanismo.
- I video vengono serviti dalla **VPS**; il server principale resta l'archivio.

### B.5 Elaborazioni alla consegna (sul server)
```bash
ffmpeg -i finale/video.srt finale/video.vtt
ffmpeg -ss 5 -i finale/video.mp4 -frames:v 1 -vf scale=1280:-1 finale/poster.jpg
ffmpeg -i finale/video.mp4 -c:v libx264 -crf 25 -maxrate 2200k -bufsize 4400k -pix_fmt yuv420p \
       -c:a aac -b:a 128k -movflags +faststart finale/anteprima_mobile.mp4
```
Per il pilota la versione mobile passa da 22 MB a 8,7 MB, sempre in 1080p.

### B.6 Traguardi
1. **Traguardo 1: deposito pronto.** API della Parte A online e collaudata (A.8). Host e token consegnati a Diego.
   - Poi la produzione deposita il pilota **"Pompe di calore / 01 Come funziona"** (finale, progetto, sorgenti, report).
2. **Traguardo 2: app minima.** Catalogo, corso, episodio con player, sottotitoli e scaletta, pagina "Da revisionare" con Pubblica. Solo utenti interni.
3. **Traguardo 3:** ricerca nei sottotitoli, avanzamento di visione, costi per episodio, replica automatica sulla VPS con controllo dello sha256.
4. **Traguardo 4 (facoltativo):** accesso clienti e corsisti esterni con corsi assegnati. Avvio della produzione direttamente dall'app (carica documenti → bozza copione → approvazioni).

### B.7 Sicurezza e privacy
- Il token di deposito **può solo depositare**: niente lettura del gestionale, niente cancellazioni, niente pubblicazione.
- Le chiavi dei servizi di produzione (fal.ai, ElevenLabs) **non** servono al gestionale e non vanno salvate lì.
- La tavola dell'avatar (volto di Diego) e un'eventuale voce clonata sono **dati personali**. Vanno tenute in `sorgenti/` o `progetto/`, visibili solo all'amministratore e mai servite pubblicamente.
- I video per i clienti richiedono un'informativa e un registro degli accessi (tabella `visualizzazioni`).

---

## Riepilogo: cosa serve indietro alla produzione video
1. **Host** del deposito: nome esatto.
2. **Token** di deposito, consegnato a Diego in modo privato.
3. Conferma del collaudo A.8 e dei limiti (dimensione massima per richiesta, spazio libero).

Appena Diego li ha:
- la produzione chiede di autorizzare l'host nella sua rete;
- Diego inserisce il token nel modulo sicuro;
- la produzione deposita il pilota con tutti i materiali e chiama la consegna.

Da quel momento ogni nuovo episodio arriva da solo nella pagina **"Da revisionare"** dell'app.
