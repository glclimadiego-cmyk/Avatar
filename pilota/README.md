# Pilota videocorso 3D cartoon — pompa di calore

## Obiettivo
Creare un video didattico di circa 60 secondi, 1920x1080, 25 fps, voce italiana, con un personaggio cartoon 3D che cammina e interagisce con una centrale termica.

## File di riferimento
- `assets/avatar_originale_2d.jpeg`: immagine 2D originale dell'utente.
- `assets/avatar_3d_approvato.png`: tavola visiva 3D approvata (NON un modello 3D riggato).
- `assets/scena_riferimento.png`: immagine di scena per direzione artistica (NON un filmato).

## Workflow consigliato per Claude Code
1. Leggere `storyboard.json`, `copione.md` e `prompt_claude_code.md`.
2. Verificare quali API video e TTS sono realmente accessibili, costi, licenze e limiti. Non presumere che l'abbonamento Claude includa API terze.
3. Generare prima un test di 5–8 secondi del personaggio che cammina, usando `avatar_3d_approvato.png` come riferimento.
4. Verificare fedeltà del volto, occhiali, corporatura, abbigliamento e continuità temporale. Richiedere approvazione prima di generare l'intero minuto.
5. Generare clip separate, voiceover e schemi vettoriali controllati; montare con Remotion/FFmpeg.
6. Esportare MP4 H.264, audio AAC e sottotitoli SRT.

## Vincoli fondamentali
- Nessun lavoro manuale in Rive, Blender, Adobe o editor di animazione richiesto all'utente.
- Non inventare scritte o dettagli tecnici nelle clip generative: aggiungerli come overlay vettoriali in montaggio.
- Evitare di mostrare la pompa di calore esterna come se fosse necessariamente installata dentro la centrale: nella scena usare un modello dimostrativo o posizionarla all'esterno, collegata al circuito interno.
- Le clip AI non garantiscono coerenza perfetta: verificare e rigenerare quando serve.
- Non usare marchi o loghi aziendali non forniti in forma autorizzata.
