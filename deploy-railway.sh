#!/bin/bash
# Script per il deployment su Railway con diverse configurazioni

# Funzione di aiuto
function show_help {
  echo "Uso: ./deploy-railway.sh [opzione]"
  echo "Opzioni:"
  echo "  -h, --help      Mostra questo messaggio"
  echo "  --all           Deploy con tutte le funzionalità abilitate"
  echo "  --minimal       Deploy con solo elaborazione Excel/CSV"
  echo "  --standard      Deploy con Excel/CSV e PDF base (default)"
  echo "  --pdf-only      Deploy con solo PDF base"
  echo "  --advanced      Deploy con Excel/CSV, PDF e funzionalità avanzate"
}

# Impostazione default
CONFIG="standard"

# Parsing dei parametri
for arg in "$@"
do
  case $arg in
    -h|--help)
      show_help
      exit 0
      ;;
    --all)
      CONFIG="all"
      ;;
    --minimal)
      CONFIG="minimal"
      ;;
    --standard)
      CONFIG="standard"
      ;;
    --pdf-only)
      CONFIG="pdf-only"
      ;;
    --advanced)
      CONFIG="advanced"
      ;;
    *)
      echo "Opzione sconosciuta: $arg"
      show_help
      exit 1
      ;;
  esac
done

# Imposta variabili di ambiente in base alla configurazione
case $CONFIG in
  all)
    echo "Deploying con tutte le funzionalità abilitate..."
    railway variables set \
      ENABLE_TABULAR_PROCESSING=true \
      ENABLE_PDF_PROCESSING=true \
      ENABLE_ADVANCED_PDF=true \
      ENABLE_OCR=true \
      ENABLE_IMAGE_PROCESSING=true
    ;;
  minimal)
    echo "Deploying con solo elaborazione Excel/CSV..."
    railway variables set \
      ENABLE_TABULAR_PROCESSING=true \
      ENABLE_PDF_PROCESSING=false \
      ENABLE_ADVANCED_PDF=false \
      ENABLE_OCR=false \
      ENABLE_IMAGE_PROCESSING=false
    ;;
  standard)
    echo "Deploying con Excel/CSV e PDF base (configurazione standard)..."
    railway variables set \
      ENABLE_TABULAR_PROCESSING=true \
      ENABLE_PDF_PROCESSING=true \
      ENABLE_ADVANCED_PDF=false \
      ENABLE_OCR=false \
      ENABLE_IMAGE_PROCESSING=false
    ;;
  pdf-only)
    echo "Deploying con solo PDF base..."
    railway variables set \
      ENABLE_TABULAR_PROCESSING=false \
      ENABLE_PDF_PROCESSING=true \
      ENABLE_ADVANCED_PDF=false \
      ENABLE_OCR=false \
      ENABLE_IMAGE_PROCESSING=false
    ;;
  advanced)
    echo "Deploying con funzionalità avanzate..."
    railway variables set \
      ENABLE_TABULAR_PROCESSING=true \
      ENABLE_PDF_PROCESSING=true \
      ENABLE_ADVANCED_PDF=true \
      ENABLE_OCR=true \
      ENABLE_IMAGE_PROCESSING=false
    ;;
esac

# Deploy su Railway
echo "Avvio deploy su Railway..."
railway up
