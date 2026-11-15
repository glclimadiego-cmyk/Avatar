# Passaggio di consegne — Modulo "Video Corsi" per il gestionale

Documento per chi prosegue il lavoro nello **sviluppo del gestionale** (persona o sessione Claude Code).
Stato al 15/11/2026.

**Dove sono i file**
- **Google Drive** di Diego, cartella `Videocorsi / Pompe di calore / 01 Come funziona`:
  - `Avatar_progetto_completo.zip`: tutto il progetto (codice `pipeline/`, progetto `pilota/`, risultati `output/`, questo documento);
  - `sorgenti_pilota.zip`: clip originali, fotogrammi e tracce voce;
  - `pilot.mp4` e `pilot.srt`: il video finale.
- Copia di riferimento nel repository GitHub `glclimadiego-cmyk/Avatar`, ramo `claude/new-session-frmbxv`.

Nel resto del documento i percorsi (`pipeline/…`, `output/pilota/…`) sono quelli dentro `Avatar_progetto_completo.zip`.

---

## 1. In breve

- Esiste una **pipeline funzionante** che produce videocorsi 3D cartoon con l'avatar di Diego:
  copione → voce → clip video generate → schemi tecnici disegnati da codice → montaggio MP4 1080p + sottotitoli.
- È stato prodotto e verificato il **pilota "La pompa di calore"** (51 s), costo di produzione **4,45 $**.
- Obiettivo ora: portare questa produzione dentro le **app del gestionale** come modulo **"Video Corsi"**,
  con **archivio dei file sul server aziendale e sulla VPS**.

---

## 2. Cosa esiste oggi

### Pilota finito
| File | Dove | Note |
|---|---|---|
| Video finale | `output/pilota/pilot.mp4` | 1920×1080, 25 fps, H.264 + AAC, sottotitoli incorporati, 51,06 s, 22 MB |
| Sottotitoli | `output/pilota/pilot.srt` | italiano |
| Report di produzione | `output/pilota/render_report.md` | verifiche, timeline, servizi, avvisi |
| Registro costi | `output/pilota/ledger.jsonl` | ogni chiamata a pagamento, con esito e costo |
| Approvazioni | `output/pilota/approvals.json` | autorizzazioni di spesa date da Diego, con tetto |
| Timeline | `output/pilota/timeline.json` | inizio/durata di ogni scena, adattate alla voce |
| Anteprima web | https://claude.ai/artifact/TLPQZiGqgzn8dsw4LEzFDa | privata, versione compressa |

Scene del pilota: S01 ingresso e saluto (0:00) · S02 verso la pompa di calore (0:09) · S03 ciclo frigorifero in 4 fasi, solo grafica (0:18) · S04 circuito idronico e bilancio energetico (0:31) · S05 chiusura (0:43).

### Progetto sorgente del pilota (`pilota/`)
- `copione.md`: testo narrato, diviso in sezioni `**MM–MM s — titolo**` + «testo».
- `storyboard.json`: scene (id, azione, camera, sezione di copione), criteri di accettazione.
- `course.json`: configurazione dell'episodio (servizi, modelli, voce, tariffe, prompt per scena).
- `assets/avatar_3d_approvato.png`: **tavola dell'avatar approvata** (riferimento di identità visiva).
- `assets/scena_riferimento.png`, `assets/avatar_originale_2d.jpeg`: riferimenti.

### Codice (`pipeline/`)
| File | Ruolo |
|---|---|
| `make_course.py` | comando unico: `services`, `draft`, `plan`, `approve`, `build` |
| `providers.py` | chiamate a ElevenLabs e fal.ai, registro costi, controllo approvazioni e tetti di spesa |
| `render.py` | timeline, sottotitoli SRT, compositing (Pillow) ed encoding (FFmpeg) |
| `graphics.py` | grafica tecnica vettoriale: **tutte le scritte del video nascono qui**, mai nelle clip AI |
| `sprites.py` | ritaglio pose dalla tavola (solo per l'animatic di controllo gratuito) |

### Materiale sorgente (in `sorgenti_pilota.zip` su Drive)
Questi file non sono nel repository GitHub (troppo pesanti). Sono in `sorgenti_pilota.zip` e vanno copiati sul server nella cartella `sorgenti/` dell'episodio:

| Cartella | Contenuto | Peso | A cosa serve |
|---|---|---|---|
| `output/pilota/clips/` | 5 clip originali generate (S01, S02, S04 in 2 parti, S05) | 227 MB | rimontare senza ripagare |
| `output/pilota/keyframes/` | fotogrammi di partenza approvati (PNG 2K) | 21 MB | rigenerare una clip con lo stesso inizio |
| `output/pilota/voice/` | tracce voce per scena (WAV) | 10 MB | rimontare senza rigenerare la voce |

Sono esclusi da Git tramite `.gitignore`. Dopo lo zip va ripristinata la stessa struttura (`output/pilota/clips`, `keyframes`, `voice`) per rimontare senza costi.

---

## 3. Come funziona la produzione

```
documenti ──draft──▶ copione.md + storyboard.json  ──[APPROVAZIONE 1: testo]──▶
voce per scena (ElevenLabs) ──▶ timeline adattata alla voce ──▶ SRT
fotogrammi di partenza (fal.ai, Nano Banana 2) ──[APPROVAZIONE 2: immagini]──▶
clip video 5/10 s (fal.ai, Kling 2.5 Turbo Pro) ──▶
montaggio: clip + schemi vettoriali + titoli + voce + sottotitoli ──▶ MP4 ──[APPROVAZIONE 3: revisione finale]
```

Comandi (dalla radice del repository):
```bash
python3 pipeline/make_course.py services                                   # cosa è configurato
python3 pipeline/make_course.py draft --docs doc.pdf note.md --project corsi/ep02   # bozza copione (Claude API)
python3 pipeline/make_course.py plan    --project pilota --out output/pilota        # costi previsti
python3 pipeline/make_course.py approve --out output/pilota --key full_generation --max-usd 8
python3 pipeline/make_course.py build   --project pilota --out output/pilota --video fal          # si ferma per revisione keyframe
python3 pipeline/make_course.py build   --project pilota --out output/pilota --video fal --keyframes-ok
python3 pipeline/make_course.py build   --project pilota --out output/pilota                      # animatic gratuito
```

Regole già implementate nel codice:
- **Nessuna spesa senza approvazione**: chiavi `test_clip`, `full_generation`, `voice_paid` in `approvals.json`, ciascuna con **tetto in dollari**.
- **Stop obbligatorio** dopo i fotogrammi di partenza: il video parte solo dopo la revisione umana.
- **Cache**: voce, keyframe e clip già prodotti non vengono rigenerati (si rimonta gratis).
- **Verifica automatica** del file finale (risoluzione, fps, codec, durata, sottotitoli) e foglio di fotogrammi di controllo.
- Clip più lunghe di 10 s: più segmenti, ognuno parte dall'ultimo fotogramma del precedente.

Requisiti macchina: Python 3.11+ (testato 3.13), FFmpeg 6, `pip install pillow numpy` (+ `anthropic` per `draft`), font DejaVu. Nessuna GPU: il rendering di 51 s richiede circa 2 minuti su 4 CPU. Generazione clip: circa 2 minuti per clip lato fal.ai.

---

## 4. Servizi, account e chiavi

| Servizio | Uso | Account | Piano / credito | Chiave |
|---|---|---|---|---|
| **fal.ai** | fotogrammi (Nano Banana 2 edit) e clip (Kling 2.5 Turbo Pro image-to-video) | account di Diego | pagamento a consumo; caricati 25 $, spesi 4,45 $; **ricarica automatica spenta** | header `Authorization: Key <chiave>`; variabile `FAL_KEY` |
| **ElevenLabs** | voce narrante | account di Diego | **Creator**: 11 $ il primo mese, poi 22 $/mese; 131.000 crediti/mese; clonazione vocale inclusa | header `xi-api-key`; variabile `ELEVENLABS_API_KEY` |
| **Claude API** (facoltativo) | bozza del copione dai documenti | da attivare | fatturazione API separata dall'abbonamento Claude | variabile `ANTHROPIC_API_KEY` |

Voce scelta: **Marco – Friendly, Calm and Warm**, `voice_id = GcAgjAjkhWsmUd4GlPiv`, modello `eleven_v4`.

**Sicurezza delle chiavi**
- Le chiavi attuali sono salvate solo nell'ambiente cloud Claude "Avatar" (segreti di rete), **non** nel codice né nel repository.
- Per il server/VPS: creare **chiavi nuove e dedicate** (una per server) da fal.ai → Keys ed ElevenLabs → Developers → API Keys, salvarle come variabili d'ambiente o nel gestore di segreti del server, **mai** nel database in chiaro né nel codice.
- Il gestionale non deve mai mostrare o restituire le chiavi al browser: le chiamate ai servizi partono solo dal server.

---

## 5. Costi di riferimento (listino fal.ai letto il 15/11/2026)

| Voce | Prezzo |
|---|---|
| Clip Kling 2.5 Turbo Pro | 0,35 $ per 5 s, 0,07 $/s → 0,70 $ per 10 s |
| Fotogramma Nano Banana 2 edit (2K) | 0,12 $ |
| Voce ElevenLabs | compresa nell'abbonamento (circa 750 caratteri per un episodio di 1 minuto) |

Un episodio di circa 1 minuto costa **3,5–5 $** di fal.ai, rigenerazioni comprese. Con 25 $ di credito si fanno circa 5 episodi.

---

## 6. Proposta di architettura per il modulo "Video Corsi"

### Componenti
1. **Archivio file** sul server aziendale, con **replica sulla VPS**: il server è l'archivio principale, la VPS serve i video online. Sincronizzazione notturna con `rsync` o `rclone`, solo in un verso.
2. **Catalogo nel database del gestionale**: corsi, episodi, file e stati di produzione.
3. **Interfaccia nelle app del gestionale**:
   - elenco corsi
   - scheda episodio con player, sottotitoli, scaletta delle scene e descrizione
   - ricerca
   - permessi
4. **Servizio di produzione** (questa pipeline) installato sul server o sulla VPS. Il gestionale lo avvia e ne legge lo stato; non lo riscrive.

### Struttura cartelle proposta (identica su server e VPS)
```
/videocorsi/
  <corso-slug>/                       es. pompe-di-calore
    corso.json                        titolo, descrizione, ordine episodi
    <NN-episodio-slug>/               es. 01-come-funziona
      finale/   video.mp4  video.srt  poster.jpg  anteprima_mobile.mp4
      progetto/ copione.md  storyboard.json  course.json  documenti_origine/
      sorgenti/ clips/  keyframes/  voice/          (solo server, non serve sulla VPS)
      report/   render_report.md  ledger.jsonl  approvals.json  contact_sheet.png
```
Il pilota attuale diventa `/videocorsi/pompe-di-calore/01-come-funziona/`.

### Modello dati minimo
- **corsi**: id, slug, titolo, descrizione, stato (bozza/pubblicato), ordinamento.
- **episodi**: id, corso_id, numero, slug, titolo, descrizione, durata_s, stato, percorso_cartella, pubblicato_il.
  Gli stati sono: bozza_copione → copione_approvato → keyframe_da_approvare → in_generazione → da_revisionare → pubblicato.
- **file_episodio**: id, episodio_id, tipo (video, srt, poster, sorgente...), percorso, dimensione, sha256, copiato_su_vps (sì/no).
- **produzioni**: id, episodio_id, servizio, modello, secondi, costo_usd, esito, errore, data. Si importa da `ledger.jsonl`.
- **approvazioni**: id, episodio_id, tipo (copione, keyframe, test_clip, full_generation, voice_paid, pubblicazione), tetto_usd, approvato_da, data.
- Facoltativo: **visualizzazioni** (utente, episodio, percentuale vista), per i corsi interni con tracciamento.

### Riproduzione video
- I file MP4 sono già pronti per lo streaming (`+faststart`). Basta servirli con **nginx** e il supporto alle richieste "range" (standard), dietro autenticazione.
- Link temporanei firmati (es. `secure_link` di nginx, o un token del gestionale) per non esporre i file pubblicamente.
- Sottotitoli: convertire SRT → VTT per il player web (`ffmpeg -i video.srt video.vtt`).
- Versione leggera per il telefono: `ffmpeg -i video.mp4 -c:v libx264 -crf 25 -maxrate 2200k -bufsize 4400k -c:a aac -b:a 128k -movflags +faststart anteprima_mobile.mp4`. Per il pilota passa da 22 a 8,7 MB.

### Flusso di produzione dentro il gestionale
1. **Nuovo episodio**: si caricano i documenti tecnici e si genera la bozza del copione.
2. **Revisione copione**: si modifica e si approva (approvazione 1).
3. **Stima costi** (`plan`) e approvazione di spesa con tetto (approvazione 2).
4. Generazione voce e fotogrammi, poi **galleria per approvarli** o rigenerarli uno per uno (approvazione 3).
5. Generazione clip e montaggio automatico, con notifica a fine lavoro.
6. **Revisione finale** (player + foglio fotogrammi + report), poi pubblicazione (approvazione 4).
7. Copia sulla VPS e voce in catalogo.

Il servizio di produzione può essere avviato dal gestionale come coda di lavori (es. un worker che esegue `make_course.py build`). Il gestionale legge l'esito dal codice di uscita (0 = ok, 2 = manca approvazione, 3 = fotogrammi da approvare) e dai file `report/`.

### Privacy
- La tavola dell'avatar riproduce il **volto di Diego**: sono dati personali. Va conservata nell'archivio riservato e inviata solo ai servizi autorizzati (oggi fal.ai).
- Se in futuro si clona la voce di Diego, il campione vocale va trattato allo stesso modo.
- Per i corsi verso clienti: informativa e controllo di chi vede cosa.

---

## 7. Decisioni ancora aperte (da chiedere a Diego)
1. Quale gestionale: GLcantiere o un'altra app Gasparini? Con quale tecnologia è fatto e dove sta il codice?
2. Il modulo va **dentro** il gestionale o è un'app separata con lo stesso accesso?
3. Server e VPS: fornitore, accesso (SSH o pannello), chi li gestisce, spazio disco disponibile. Si stimano circa 300 MB per episodio con i sorgenti, 30 MB senza.
4. Chi guarda i video: solo i tecnici interni, oppure anche clienti e corsisti esterni?
5. Logo aziendale sulla polo dell'avatar: serve un file del logo (SVG o PNG) da sovrapporre in grafica.

---

## 8. Limiti noti e miglioramenti possibili
- **Labiale non sincronizzato** con la voce: si può aggiungere con un modello di lip-sync su fal.ai (costo extra per clip).
- Nella scena di sola grafica (S03) il presentatore è l'immagine ferma della tavola, non animata.
- In alcune clip le **proporzioni** del personaggio risultano un po' più tozze rispetto alla tavola. Si controlla in fase di revisione dei fotogrammi.
- I layout delle scene (`walk_in`, `walk_to_monitor`, `diagram_cycle`, `hydronic`, `closeup`) e gli schemi tecnici sono pensati per l'episodio sulla pompa di calore. Per altri argomenti servono **nuovi schemi in `graphics.py`**: è una scelta voluta, per garantire testi tecnici corretti.
- `draft` (bozza da documenti) è scritto ma **non ancora provato**: manca una chiave Claude API.
- Le tariffe in `course.json` vanno aggiornate se fal.ai cambia listino.

---

## 9. Testo pronto da incollare nella sessione di sviluppo del gestionale

> Devo aggiungere al gestionale un modulo "Video Corsi" per archiviare e mostrare i videocorsi 3D che produco con una pipeline già pronta. Sul mio Google Drive, cartella "Videocorsi / Pompe di calore / 01 Come funziona", trovi il documento "Passaggio di consegne – Video Corsi" (leggilo per primo), lo zip con tutto il progetto e il codice (`Avatar_progetto_completo.zip`), lo zip con il materiale sorgente e il video finale. Il documento contiene lo stato attuale, la pipeline, gli account, i costi e una proposta di architettura (cartelle, tabelle, riproduzione video, flusso di approvazione).
> L'archivio dei file va sul nostro server, con copia sulla VPS. Prima di scrivere codice, guarda come è fatto il gestionale e proponimi dove inserire il modulo, il modello dati e come servire i video in modo protetto. Fammi le domande della sezione 7 a cui non trovi risposta nel codice.
> Primo traguardo: il pilota "La pompa di calore" (`pilot.mp4` + `pilot.srt` dalla cartella Drive) visibile nell'app, con elenco corsi, scheda episodio e player con sottotitoli.
