# Script per configurare e avviare l'applicazione con feature flags su Windows

# Valori di default
$TABULAR = $true
$PDF = $true
$ADVANCED_PDF = $false
$OCR = $false
$IMAGE = $false
$PORT = 8080

# Funzione di aiuto
function Show-Help {
  Write-Host "Uso: .\run-app.ps1 [opzioni]"
  Write-Host "Opzioni:"
  Write-Host "  -Help                   Mostra questo messaggio"
  Write-Host "  -Tabular <$true|$false>   Abilita/disabilita elaborazione Excel/CSV"
  Write-Host "  -PDF <$true|$false>       Abilita/disabilita elaborazione PDF base"
  Write-Host "  -AdvancedPDF <$true|$false> Abilita/disabilita elaborazione PDF avanzata"
  Write-Host "  -OCR <$true|$false>       Abilita/disabilita OCR"
  Write-Host "  -Image <$true|$false>     Abilita/disabilita elaborazione immagini"
  Write-Host "  -All                    Abilita tutte le funzionalità"
  Write-Host "  -Minimal                Abilita solo elaborazione Excel/CSV"
  Write-Host "  -NoPDF                  Disabilita tutte le funzionalità PDF"
  Write-Host "  -Port <numero>          Imposta la porta (default: 8080)"
}

# Parsing dei parametri
param (
  [switch]$Help,
  [bool]$Tabular = $TABULAR,
  [bool]$PDF = $PDF,
  [bool]$AdvancedPDF = $ADVANCED_PDF,
  [bool]$OCR = $OCR,
  [bool]$Image = $IMAGE,
  [switch]$All,
  [switch]$Minimal,
  [switch]$NoPDF,
  [int]$Port = $PORT
)

if ($Help) {
  Show-Help
  exit 0
}

if ($All) {
  $Tabular = $true
  $PDF = $true
  $AdvancedPDF = $true
  $OCR = $true
  $Image = $true
}

if ($Minimal) {
  $Tabular = $true
  $PDF = $false
  $AdvancedPDF = $false
  $OCR = $false
  $Image = $false
}

if ($NoPDF) {
  $PDF = $false
  $AdvancedPDF = $false
  $OCR = $false
}

# Impostazione delle variabili d'ambiente
$env:ENABLE_TABULAR_PROCESSING = $Tabular.ToString().ToLower()
$env:ENABLE_PDF_PROCESSING = $PDF.ToString().ToLower()
$env:ENABLE_ADVANCED_PDF = $AdvancedPDF.ToString().ToLower()
$env:ENABLE_OCR = $OCR.ToString().ToLower()
$env:ENABLE_IMAGE_PROCESSING = $Image.ToString().ToLower()
$env:PORT = $Port

Write-Host "Avvio dell'applicazione con feature flags:"
Write-Host "- ENABLE_TABULAR_PROCESSING=$env:ENABLE_TABULAR_PROCESSING"
Write-Host "- ENABLE_PDF_PROCESSING=$env:ENABLE_PDF_PROCESSING"
Write-Host "- ENABLE_ADVANCED_PDF=$env:ENABLE_ADVANCED_PDF"
Write-Host "- ENABLE_OCR=$env:ENABLE_OCR"
Write-Host "- ENABLE_IMAGE_PROCESSING=$env:ENABLE_IMAGE_PROCESSING"
Write-Host "- PORT=$env:PORT"

# Avvio dell'applicazione
& python -m uvicorn app.main:app --host 0.0.0.0 --port $env:PORT --log-level debug