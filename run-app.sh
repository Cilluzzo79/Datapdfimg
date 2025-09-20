#!/bin/bash
# Script per configurare e avviare l'applicazione con feature flags

# Valori di default
TABULAR=true
PDF=true
ADVANCED_PDF=false
OCR=false
IMAGE=false

# Funzione di aiuto
function show_help {
  echo "Uso: ./run-app.sh [opzioni]"
  echo "Opzioni:"
  echo "  -h, --help                 Mostra questo messaggio"
  echo "  --tabular=true|false       Abilita/disabilita elaborazione Excel/CSV"
  echo "  --pdf=true|false           Abilita/disabilita elaborazione PDF base"
  echo "  --advanced-pdf=true|false  Abilita/disabilita elaborazione PDF avanzata"
  echo "  --ocr=true|false           Abilita/disabilita OCR"
  echo "  --image=true|false         Abilita/disabilita elaborazione immagini"
  echo "  --all                      Abilita tutte le funzionalità"
  echo "  --minimal                  Abilita solo elaborazione Excel/CSV"
  echo "  --no-pdf                   Disabilita tutte le funzionalità PDF"
  echo "  --port=XXXX                Imposta la porta (default: 8080)"
}

# Parsing dei parametri
for arg in "$@"
do
  case $arg in
    -h|--help)
      show_help
      exit 0
      ;;
    --tabular=*)
      TABULAR="${arg#*=}"
      ;;
    --pdf=*)
      PDF="${arg#*=}"
      ;;
    --advanced-pdf=*)
      ADVANCED_PDF="${arg#*=}"
      ;;
    --ocr=*)
      OCR="${arg#*=}"
      ;;
    --image=*)
      IMAGE="${arg#*=}"
      ;;
    --all)
      TABULAR=true
      PDF=true
      ADVANCED_PDF=true
      OCR=true
      IMAGE=true
      ;;
    --minimal)
      TABULAR=true
      PDF=false
      ADVANCED_PDF=false
      OCR=false
      IMAGE=false
      ;;
    --no-pdf)
      PDF=false
      ADVANCED_PDF=false
      OCR=false
      ;;
    --port=*)
      PORT="${arg#*=}"
      ;;
    *)
      echo "Opzione sconosciuta: $arg"
      show_help
      exit 1
      ;;
  esac
done

# Impostazione delle variabili d'ambiente
export ENABLE_TABULAR_PROCESSING=$TABULAR
export ENABLE_PDF_PROCESSING=$PDF
export ENABLE_ADVANCED_PDF=$ADVANCED_PDF
export ENABLE_OCR=$OCR
export ENABLE_IMAGE_PROCESSING=$IMAGE
export PORT=${PORT:-8080}

echo "Avvio dell'applicazione con feature flags:"
echo "- ENABLE_TABULAR_PROCESSING=$ENABLE_TABULAR_PROCESSING"
echo "- ENABLE_PDF_PROCESSING=$ENABLE_PDF_PROCESSING"
echo "- ENABLE_ADVANCED_PDF=$ENABLE_ADVANCED_PDF"
echo "- ENABLE_OCR=$ENABLE_OCR"
echo "- ENABLE_IMAGE_PROCESSING=$ENABLE_IMAGE_PROCESSING"
echo "- PORT=$PORT"

# Avvio dell'applicazione
uvicorn app.main:app --host 0.0.0.0 --port $PORT --log-level debug