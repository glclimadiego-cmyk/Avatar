# Archivio provvisorio dei sorgenti

Copia di sicurezza del materiale di lavorazione, in attesa dell'archivio sul server aziendale.
La struttura è quella prevista sul server: `/videocorsi/<corso>/<NN-episodio>/sorgenti/`.

## pompe-di-calore / 01-come-funziona / sorgenti
- `clips/`: clip generate per scena (S01, S02, S04, S05). In `parti/` ci sono i due segmenti di S04 e il fotogramma di raccordo.
- `keyframes/`: fotogrammi di partenza approvati (PNG 2K). I file `.approvato` segnano l'approvazione.
- `voice/`: tracce voce per scena e voce completa (`voiceover.wav`), voce "Marco", ElevenLabs.

Il video finale e il progetto sono in `output/pilota/` e `pilota/`.
Per rimontare senza costi: copiare `clips/` (con `parti/` rinominata in `parts/`), `keyframes/` e `voice/` in `output/pilota/`,
poi `python3 pipeline/make_course.py build --project pilota --out output/pilota --video fal --keyframes-ok`.

Contiene il volto di Diego (fotogrammi): repository privato, non condividere.
