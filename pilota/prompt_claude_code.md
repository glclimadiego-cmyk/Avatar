# Istruzioni da incollare in Claude Code

Lavora nella cartella di questo pacchetto. Voglio un workflow il più possibile automatico per creare videocorsi 3D cartoon da testi e documenti, senza richiedermi di usare manualmente programmi di animazione.

Leggi README.md, storyboard.json, copione.md e le tre immagini in assets. La tavola 3D è una reference grafica, non un modello 3D riggato. Mantieni la fisionomia e l'abbigliamento dell'avatar approvato.

FASE 1: esamina i servizi video generativi e TTS disponibili nella mia configurazione e verifica quali sono davvero accessibili via API, quali richiedono credenziali e quali hanno costi aggiuntivi. Non inventare API o disponibilità. Proponi una pipeline con generazione video image-to-video, voce italiana, compositing di grafica tecnica controllata e rendering finale con Remotion/FFmpeg.

FASE 2: costruisci un test end-to-end di 5–8 secondi: avatar che cammina, si ferma, si gira e indica una pompa di calore. Non creare solo una panoramica di immagine statica. Prima di spendere crediti o inviare dati a servizi esterni, mostrami costo previsto e chiedi autorizzazione.

FASE 3: dopo la mia approvazione, realizza il pilota da ~60 secondi con storyboard e copione. Suddividi in clip brevi per ridurre i difetti, verifica continuità del personaggio, sincronizza la voce, aggiungi grafici tecnici tramite codice e monta MP4 1080p con sottotitoli SRT.

FASE 4: prepara un comando unico per i corsi successivi: documenti in input -> sceneggiatura approvata -> scene -> audio -> video MP4. Registra errori, costi, servizi usati e punti che richiedono approvazione umana.

Importante: non dichiarare il video completato senza aver prodotto e verificato realmente il file MP4. Se non hai API video disponibili, prepara la pipeline e indicami esattamente quale connessione o chiave serve.
