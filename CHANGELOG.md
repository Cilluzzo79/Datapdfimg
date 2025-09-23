# Changelog

## [1.1.0] - 2025-09-23

### Aggiunto
- Nuovo endpoint `/process-for-claude` che restituisce dati ottimizzati per Claude Sonnet 3.7
- Formattazione specializzata per ciascun tipo di documento business
- Generazione automatica di prompt suggeriti basati sul tipo di documento
- Supporto per l'interpretazione di dati tabellari complessi (Excel/CSV)
- Generazione di statistiche rilevanti per documenti di magazzino e bilancio

### Migliorato
- Gestione più robusta di dati tabellari con colonne "Unnamed"
- Pulizia e normalizzazione dei nomi delle colonne per maggiore leggibilità
- Estrazione automatica di statistiche dai dati tabellari

## [1.0.0] - 2025-09-15

### Prima versione
- Supporto per elaborazione di immagini e PDF
- Classificazione automatica del tipo di documento
- Integrazione con N8N tramite webhook
- Deployment automatico su Railway
