# Richiesta per lo sviluppo del gestionale — Radio Cantiere: chat più leggibile

Da Diego, 19/11/2026. Da incollare nella sessione che sviluppa il gestionale. Riguarda la chat di **Radio Cantiere** (la conversazione di un cantiere, aperta dal telefono).

## 1. Pulsante per tornare indietro più grande

- Quando si entra in una chat, in alto a sinistra c'è il pulsante che torna all'elenco: è troppo piccolo e si sbaglia a toccarlo.
- Farlo più grande, almeno della misura di un dito: area toccabile di circa 48×48 px o più, con l'icona e, se c'è spazio, la scritta.
- Non deve cambiare cosa fa: torna all'elenco delle chat come oggi.

## 2. La scheda dell'incarico più schematica

Oggi l'incarico compare come un blocco di testo centrato, tutto con lo stesso peso. Si perde il dettaglio di cosa c'è scritto. Esempio di come appare ora (dati sostituiti):

> 📋 Incarico da [chi assegna] a [chi riceve]: Fissare un appuntamento con il cliente per quantificare i lavori …
> Risultato desiderato: appuntamento preso per la settimana prossima
> Entro: 20/11 ore 19:00
> Preventivo n. 2026/31 — [cliente] · [pacchetto] (Bozza) 13/11 18:28

Va resa a **scheda**, con un'etichetta in grassetto per ogni concetto e il valore accanto o sotto, una riga per voce, allineata a sinistra:

| Etichetta (grassetto) | Contenuto |
|---|---|
| **Incarico** | Cosa fare |
| **Da → a** | Chi assegna → chi lo riceve |
| **Risultato** | Il risultato desiderato |
| **Entro** | Data e ora della scadenza (evidenziata se scaduta o vicina) |
| **Preventivo** | Numero, cliente, pacchetto, stato, toccabile per aprirlo se oggi lo è |
| **Data** | Quando è stato creato |

- Solo presentazione: dati, permessi e azioni dell'incarico restano come sono. Chi oggi non vede un'informazione non deve vederla per effetto di questa modifica.
- Lo stesso stile, con etichette in grassetto, va bene anche per le altre righe di sistema della chat, quando hanno più di un dato (per esempio «[persona] ha coinvolto [persona]: ti ho messo in copia» o «[persona] ha accettato l'incarico»).

## 3. Le scritte delle «premesse» grandi come i messaggi

- Le righe di sistema (incarico, persone coinvolte, «ha accettato l'incarico» e simili) oggi sono scritte più piccole dei messaggi. Sono importanti e piccole non si leggono.
- Devono avere la **stessa dimensione del testo dei messaggi della chat**. Data e ora possono restare più piccole e grigie, come nei messaggi.

## Come verificare

- Su un telefono, aprire una chat di cantiere che contiene un incarico:
  - il pulsante indietro si tocca al primo colpo;
  - l'incarico si legge come scheda con le etichette;
  - le righe di sistema hanno la stessa grandezza dei messaggi.
- Provare anche su un telefono piccolo: niente testo tagliato, niente scorrimento orizzontale.
- Aggiornare la scheda del Manuale di Radio Cantiere se descrive l'aspetto dell'incarico.
