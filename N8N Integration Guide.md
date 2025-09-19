# Guida all'integrazione con N8N

Questa guida descrive come integrare il Railway Document Worker con N8N per creare flussi di lavoro automatizzati per l'elaborazione di documenti business.

## Prerequisiti

- Worker Railway Document Worker deployato e funzionante
- Istanza N8N installata e configurata
- Accesso alle API del worker

## Configurazione del webhook in N8N

### 1. Creazione di un nuovo workflow

1. Accedi alla tua istanza N8N
2. Crea un nuovo workflow cliccando su "Create Workflow"
3. Assegna un nome al workflow, ad esempio "Document Processing Workflow"

### 2. Configurazione del trigger

A seconda delle tue esigenze, puoi utilizzare diversi trigger:

#### Opzione A: Trigger quando un file viene caricato in una cartella (consigliato)

1. Aggiungi un nodo "Watch Files" o "Watch Folder"
2. Configura il percorso della cartella da monitorare
3. Imposta l'intervallo di controllo (ad esempio, ogni 1 minuto)
4. Configura il filtro dei file (ad esempio, `*.pdf, *.jpg, *.png, *.webp`)

#### Opzione B: Trigger HTTP Webhook

1. Aggiungi un nodo "Webhook"
2. Seleziona il metodo "POST"
3. Abilita l'opzione "Binary Data" se prevedi di ricevere file binari
4. Salva il workflow per attivare il webhook e copiare l'URL generato

### 3. Preparazione del file per l'elaborazione

1. Aggiungi un nodo "HTTP Request" dopo il trigger
2. Configura il nodo:
   - Metodo: POST
   - URL: `https://tuo-worker-railway.app/process-document`
   - Autenticazione: Nessuna (o configura l'autenticazione se necessario)
   - Formato body: multipart-form-data
   - Opzione "Send Binary Data": Abilitata
   - Parametri:
     - `file`: Seleziona il campo contenente il file binario (dipende dal trigger utilizzato)
     - `document_type`: (Opzionale) Specifica il tipo di documento, ad esempio "fattura", "bilancio", ecc.
     - `custom_metadata`: (Opzionale) Un JSON con metadati personalizzati

### 4. Elaborazione della risposta

1. Aggiungi un nodo "Set" dopo l'HTTP Request per elaborare la risposta
2. Estrai i campi rilevanti dalla risposta:
   ```
   {
     "document_data": {{$node["HTTP Request"].json["result_json"]["extracted_data"]}},
     "document_type": {{$node["HTTP Request"].json["document_type"]}},
     "confidence_score": {{$node["HTTP Request"].json["confidence_score"]}},
     "document_id": {{$node["HTTP Request"].json["document_id"]}}
   }
   ```

### 5. Azioni condizionali in base al tipo di documento

1. Aggiungi un nodo "Switch" per gestire diversi tipi di documento
2. Configura condizioni come:
   - `{{$node["Set"].json["document_type"]}} === "fattura"`
   - `{{$node["Set"].json["document_type"]}} === "bilancio"`
   - ecc.
3. Per ogni condizione, aggiungi i nodi necessari per il flusso specifico

## Esempi di flussi di lavoro completi

### Esempio 1: Elaborazione fatture e inserimento in database

1. **Trigger**: Watch Folder sulla cartella delle fatture
2. **HTTP Request**: Invia i file al Document Worker
3. **Set**: Estrai i dati della fattura
4. **IF**: Verifica se il documento è effettivamente una fattura e se la confidenza è > 0.8
   - Se **Vero**:
     - **HTTP Request** o **Database**: Inserisci i dati della fattura nel tuo sistema
     - **Slack/Email**: Notifica l'elaborazione avvenuta con successo
   - Se **Falso**:
     - **Slack/Email**: Notifica che il documento richiede verifica manuale

### Esempio 2: Flusso di approvazione documenti

1. **Trigger**: HTTP Webhook (quando un documento viene caricato tramite applicazione)
2. **HTTP Request**: Invia il documento al Document Worker
3. **Set**: Estrai i dati e il tipo di documento
4. **Switch**: In base al tipo di documento
   - **Fattura**:
     - **Database**: Registra la fattura
     - **Slack/Teams**: Invia notifica al team finanziario per approvazione
   - **Documento di magazzino**:
     - **Database**: Aggiorna il database inventario
     - **Slack/Teams**: Notifica al team logistica
   - **Default**:
     - **Email**: Invia il documento all'amministrazione per revisione

## Test dell'integrazione

Prima di implementare il flusso di lavoro completo, è consigliabile testare l'integrazione:

1. Crea un workflow semplice con:
   - Trigger manuale (nodo "Execute Workflow")
   - HTTP Request al worker con un file di test
   - Debug per visualizzare la risposta

2. Usa l'endpoint `/test-webhook` del worker:
   ```
   POST https://tuo-worker-railway.app/test-webhook
   Content-Type: application/json
   Body: {"test": "data"}
   ```

## Considerazioni per l'implementazione in produzione

### Gestione degli errori

1. Aggiungi nodi "Error Trigger" per gestire gli errori durante l'esecuzione
2. Implementa tentativi di ripetizione per le chiamate HTTP fallite
3. Configura notifiche in caso di errori persistenti

### Performance e scalabilità

1. Utilizza code per gestire grandi volumi di documenti
2. Imposta un numero massimo di esecuzioni parallele
3. Monitora i tempi di elaborazione e regola di conseguenza

### Sicurezza

1. Utilizza connessioni HTTPS per tutte le chiamate API
2. Configura l'autenticazione per le chiamate al worker
3. Limita l'accesso ai workflow sensibili

## Aggiornamento del workflow

Quando il worker viene aggiornato con nuove funzionalità:

1. Verifica i cambiamenti nella documentazione API
2. Aggiorna i nodi HTTP Request con eventuali nuovi parametri
3. Modifica l'elaborazione della risposta se il formato è cambiato
4. Testa il workflow con dati di esempio prima di metterlo in produzione

## Risoluzione dei problemi comuni

### Il worker non riceve il file correttamente

- Verifica che l'opzione "Send Binary Data" sia abilitata
- Controlla che il nome del parametro sia esattamente "file"
- Verifica che il file non superi la dimensione massima consentita (10MB per default)

### Errori di elaborazione

- Controlla i log del worker per messaggi di errore dettagliati
- Verifica che il tipo di file sia supportato (JPG, PNG, WEBP, PDF)
- Assicurati che l'API key di OpenRouter sia configurata correttamente nel worker

### Bassa qualità dell'estrazione dati

- Controlla il valore "confidence_score" nella risposta
- Per documenti poco chiari, considera il preprocessamento delle immagini
- Se necessario, specifica manualmente il tipo di documento con il parametro "document_type"

## Supporto e risorse aggiuntive

- Documentazione API completa: `/docs` sull'URL del worker
- Repository del progetto: [GitHub Repository URL]
- Problemi e richieste: [GitHub Issues URL]
