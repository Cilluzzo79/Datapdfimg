# Script PowerShell per il deployment su Railway con diverse configurazioni

# Funzione di aiuto
function Show-Help {
  Write-Host "Uso: .\deploy-railway.ps1 [opzione]"
  Write-Host "Opzioni:"
  Write-Host "  -Help         Mostra questo messaggio"
  Write-Host "  -All          Deploy con tutte le funzionalità abilitate"
  Write-Host "  -Minimal      Deploy con solo elaborazione Excel/CSV"
  Write-Host "  -Standard     Deploy con Excel/CSV e PDF base (default)"
  Write-Host "  -PdfOnly      Deploy con solo PDF base"
  Write-Host "  -Advanced     Deploy con Excel/CSV, PDF e funzionalità avanzate"
}

# Parsing dei parametri
param (
  [switch]$Help,
  [switch]$All,
  [switch]$Minimal,
  [switch]$Standard,
  [switch]$PdfOnly,
  [switch]$Advanced
)

if ($Help) {
  Show-Help
  exit 0
}

# Impostazione default
$Config = "standard"

if ($All) { $Config = "all" }
if ($Minimal) { $Config = "minimal" }
if ($Standard) { $Config = "standard" }
if ($PdfOnly) { $Config = "pdf-only" }
if ($Advanced) { $Config = "advanced" }

# Imposta variabili di ambiente in base alla configurazione
switch ($Config) {
  "all" {
    Write-Host "Deploying con tutte le funzionalità abilitate..."
    & railway variables set `
      ENABLE_TABULAR_PROCESSING=true `
      ENABLE_PDF_PROCESSING=true `
      ENABLE_ADVANCED_PDF=true `
      ENABLE_OCR=true `
      ENABLE_IMAGE_PROCESSING=true
  }
  "minimal" {
    Write-Host "Deploying con solo elaborazione Excel/CSV..."
    & railway variables set `
      ENABLE_TABULAR_PROCESSING=true `
      ENABLE_PDF_PROCESSING=false `
      ENABLE_ADVANCED_PDF=false `
      ENABLE_OCR=false `
      ENABLE_IMAGE_PROCESSING=false
  }
  "standard" {
    Write-Host "Deploying con Excel/CSV e PDF base (configurazione standard)..."
    & railway variables set `
      ENABLE_TABULAR_PROCESSING=true `
      ENABLE_PDF_PROCESSING=true `
      ENABLE_ADVANCED_PDF=false `
      ENABLE_OCR=false `
      ENABLE_IMAGE_PROCESSING=false
  }
  "pdf-only" {
    Write-Host "Deploying con solo PDF base..."
    & railway variables set `
      ENABLE_TABULAR_PROCESSING=false `
      ENABLE_PDF_PROCESSING=true `
      ENABLE_ADVANCED_PDF=false `
      ENABLE_OCR=false `
      ENABLE_IMAGE_PROCESSING=false
  }
  "advanced" {
    Write-Host "Deploying con funzionalità avanzate..."
    & railway variables set `
      ENABLE_TABULAR_PROCESSING=true `
      ENABLE_PDF_PROCESSING=true `
      ENABLE_ADVANCED_PDF=true `
      ENABLE_OCR=true `
      ENABLE_IMAGE_PROCESSING=false
  }
}

# Deploy su Railway
Write-Host "Avvio deploy su Railway..."
& railway up
