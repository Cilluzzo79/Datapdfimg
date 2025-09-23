"""
Servizio per formattare i dati in output ottimizzati per Claude Sonnet
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import re
from app.models.document import DocumentType
from app.utils.logging_utils import get_logger

logger = get_logger(__name__)

class ClaudeFormatter:
    """
    Classe per formattare i dati in un formato ottimale per Claude Sonnet 3.7
    """
    
    @staticmethod
    def format_for_claude(
        document_type: str,
        metadata: Dict[str, Any],
        extracted_data: Dict[str, Any],
        confidence_score: float,
        raw_text: Optional[str] = None,
        processing_notes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Formatta i dati estratti in un formato ottimizzato per Claude
        
        Args:
            document_type: Tipo di documento
            metadata: Metadati del documento
            extracted_data: Dati estratti dal documento
            confidence_score: Punteggio di confidenza
            raw_text: Testo grezzo (opzionale)
            processing_notes: Note di elaborazione (opzionale)
            
        Returns:
            Dati formattati per Claude
        """
        try:
            logger.info(f"Formattazione dati per Claude, tipo documento: {document_type}")
            
            # Struttura di base per tutti i tipi di documento
            claude_format = {
                "metadata": {
                    "document_type": document_type,
                    "file_name": metadata.get("original_filename", "documento.unknown"),
                    "file_type": metadata.get("file_type", "unknown"),
                    "extraction_timestamp": datetime.now().isoformat(),
                    "confidence_score": confidence_score
                },
                "content": {
                    # Sarà popolato in base al tipo di documento
                },
                "summary": "",
                "suggested_prompts": []
            }
            
            # Seleziona il formattatore specifico per il tipo di documento
            if document_type == DocumentType.FATTURA.value:
                return ClaudeFormatter._format_fattura(claude_format, metadata, extracted_data, raw_text)
            elif document_type == DocumentType.BILANCIO.value:
                return ClaudeFormatter._format_bilancio(claude_format, metadata, extracted_data, raw_text)
            elif document_type == DocumentType.MAGAZZINO.value:
                return ClaudeFormatter._format_magazzino(claude_format, metadata, extracted_data, raw_text)
            elif document_type == DocumentType.CORRISPETTIVO.value:
                return ClaudeFormatter._format_corrispettivo(claude_format, metadata, extracted_data, raw_text)
            elif document_type == DocumentType.ANALISI_MERCATO.value:
                return ClaudeFormatter._format_analisi_mercato(claude_format, metadata, extracted_data, raw_text)
            else:
                return ClaudeFormatter._format_generico(claude_format, metadata, extracted_data, raw_text)
        except Exception as e:
            logger.error(f"Errore durante la formattazione per Claude: {e}")
            # Formato di fallback
            return {
                "metadata": {
                    "document_type": document_type,
                    "error": str(e),
                    "confidence_score": 0.0
                },
                "content": {
                    "raw_data": extracted_data or {}
                },
                "summary": "Si è verificato un errore durante la formattazione dei dati per Claude",
                "suggested_prompts": [
                    "Puoi analizzare questi dati grezzi nonostante l'errore di formattazione?",
                    "Come posso migliorare la struttura di questi dati?"
                ]
            }
    
    @staticmethod
    def _format_fattura(
        claude_format: Dict[str, Any],
        metadata: Dict[str, Any],
        extracted_data: Dict[str, Any],
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Formatta i dati di una fattura per Claude"""
        
        # Estrai e struttura i dati della fattura
        fattura_data = {}
        
        # Informazioni di base della fattura
        fattura_data["numero_fattura"] = extracted_data.get("numero_fattura", "N/A")
        fattura_data["data_fattura"] = extracted_data.get("data_fattura", "N/A")
        fattura_data["importo_totale"] = extracted_data.get("importo_totale", 0.0)
        fattura_data["iva"] = extracted_data.get("iva", 0.0)
        
        # Informazioni su mittente e destinatario
        fattura_data["mittente"] = extracted_data.get("mittente", {})
        fattura_data["destinatario"] = extracted_data.get("destinatario", {})
        
        # Voci della fattura
        fattura_data["voci"] = []
        if "voci" in extracted_data and isinstance(extracted_data["voci"], list):
            fattura_data["voci"] = extracted_data["voci"]
        
        # Aggiungi i dati formattati
        claude_format["content"] = {
            "fattura": fattura_data
        }
        
        # Aggiungi un sommario
        emittente = fattura_data["mittente"].get("nome", "Emittente sconosciuto")
        destinatario = fattura_data["destinatario"].get("nome", "Destinatario sconosciuto")
        importo = fattura_data["importo_totale"]
        data = fattura_data["data_fattura"]
        
        claude_format["summary"] = f"Fattura n. {fattura_data['numero_fattura']} emessa da {emittente} a {destinatario} per un importo di {importo} in data {data}."
        
        # Aggiungi prompt suggeriti
        claude_format["suggested_prompts"] = [
            "Verifica la correttezza degli importi in questa fattura",
            "Calcola l'IVA detraibile da questa fattura",
            "Confronta questa fattura con le precedenti dello stesso fornitore",
            "Crea un riassunto dei punti principali di questa fattura",
            "Quali informazioni mancano in questa fattura per essere fiscalmente valida?"
        ]
        
        return claude_format
    
    @staticmethod
    def _format_bilancio(
        claude_format: Dict[str, Any],
        metadata: Dict[str, Any],
        extracted_data: Dict[str, Any],
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Formatta i dati di un bilancio per Claude"""
        
        # Estrai e struttura i dati del bilancio
        bilancio_data = {}
        
        # Informazioni di base
        bilancio_data["azienda"] = extracted_data.get("azienda", "N/A")
        bilancio_data["anno"] = extracted_data.get("anno", "N/A")
        bilancio_data["tipo_bilancio"] = extracted_data.get("tipo_bilancio", "N/A")
        
        # Dati finanziari
        bilancio_data["totale_attivo"] = extracted_data.get("totale_attivo", 0.0)
        bilancio_data["totale_passivo"] = extracted_data.get("totale_passivo", 0.0)
        bilancio_data["patrimonio_netto"] = extracted_data.get("patrimonio_netto", 0.0)
        bilancio_data["ricavi"] = extracted_data.get("ricavi", 0.0)
        bilancio_data["costi"] = extracted_data.get("costi", 0.0)
        bilancio_data["utile_perdita"] = extracted_data.get("utile_perdita", 0.0)
        
        # Voci di bilancio
        bilancio_data["voci_principali"] = []
        if "voci_principali" in extracted_data and isinstance(extracted_data["voci_principali"], list):
            bilancio_data["voci_principali"] = extracted_data["voci_principali"]
        
        # Aggiungi i dati formattati
        claude_format["content"] = {
            "bilancio": bilancio_data
        }
        
        # Aggiungi un sommario
        azienda = bilancio_data["azienda"]
        anno = bilancio_data["anno"]
        tipo = bilancio_data["tipo_bilancio"]
        utile_perdita = bilancio_data["utile_perdita"]
        
        claude_format["summary"] = f"Bilancio {tipo} dell'azienda {azienda} per l'anno {anno}. Risultato economico: {utile_perdita}."
        
        # Aggiungi prompt suggeriti
        claude_format["suggested_prompts"] = [
            "Analizza gli indici di bilancio di questa azienda",
            "Confronta i dati di bilancio con quelli degli anni precedenti",
            "Identifica le voci di bilancio che meritano attenzione",
            "Crea un'analisi finanziaria di questo bilancio",
            "Quali sono i punti di forza e debolezza evidenziati da questo bilancio?"
        ]
        
        return claude_format
    
    @staticmethod
    def _format_magazzino(
        claude_format: Dict[str, Any],
        metadata: Dict[str, Any],
        extracted_data: Dict[str, Any],
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Formatta i dati di un documento di magazzino per Claude"""
        
        # Estrai e struttura i dati del magazzino
        magazzino_data = {
            "tipo_documento": extracted_data.get("tipo_documento", "Inventario"),
            "data": extracted_data.get("data", "N/A"),
            "magazzino_codice": extracted_data.get("magazzino_codice", "N/A"),
        }
        
        # Gestione dei dati tabellari
        headers = []
        rows = []
        
        # Estrai le intestazioni
        if "column_names" in metadata:
            if isinstance(metadata["column_names"], dict):
                # Ordina le colonne per indice
                sorted_cols = sorted(
                    [(int(k.replace("column_", "")) if k.startswith("column_") else int(k), v) 
                     for k, v in metadata["column_names"].items()], 
                    key=lambda x: x[0]
                )
                headers = [col[1] for col in sorted_cols]
            elif isinstance(metadata["column_names"], list):
                headers = metadata["column_names"]
        
        # Se non abbiamo trovato intestazioni, cerchiamo di determinarle
        if not headers:
            col_pattern = r"^Unnamed: \d+$"
            headers = []
            
            # Cerca colonne tipo "Unnamed: X"
            unnamed_cols = sorted(
                [k for k in extracted_data.keys() if isinstance(k, str) and re.match(col_pattern, k)],
                key=lambda x: int(x.replace("Unnamed: ", ""))
            )
            
            if unnamed_cols:
                headers = unnamed_cols
                # Aggiungi "Incidenza" se presente
                if "Incidenza" in extracted_data and "Incidenza" not in headers:
                    headers.append("Incidenza")
        
        # Se ancora non abbiamo intestazioni, usa predefinite
        if not headers:
            headers = ["Categoria", "Descrizione", "Codice", "Valore", "Incidenza"]
        
        # Pulisci le intestazioni per renderle più leggibili
        clean_headers = []
        for h in headers:
            if isinstance(h, str) and h.startswith("Unnamed: "):
                col_num = int(h.replace("Unnamed: ", ""))
                clean_headers.append(f"Colonna {col_num+1}")
            else:
                clean_headers.append(h)
        
        # Estrai le righe
        if "rows" in extracted_data and isinstance(extracted_data["rows"], (list, dict)):
            if isinstance(extracted_data["rows"], dict):
                rows_data = list(extracted_data["rows"].values())
            else:
                rows_data = extracted_data["rows"]
            
            for row in rows_data:
                if not isinstance(row, dict):
                    continue
                    
                new_row = {}
                for i, header in enumerate(headers):
                    if header in row:
                        new_row[clean_headers[i]] = row[header]
                    elif i < len(row) and isinstance(row, list):
                        new_row[clean_headers[i]] = row[i]
                
                # Aggiungi la riga solo se ha valori non nulli
                if any(v is not None for v in new_row.values()):
                    rows.append(new_row)
        
        # Alternativa: cerca chiavi di tipo "31-05-2025" (nome del foglio)
        if not rows and any(k for k in extracted_data.keys() if re.match(r"\d{2}-\d{2}-\d{4}", str(k))):
            sheet_key = next(k for k in extracted_data.keys() if re.match(r"\d{2}-\d{2}-\d{4}", str(k)))
            if isinstance(extracted_data[sheet_key], dict):
                for row_idx, row_data in extracted_data[sheet_key].items():
                    if not isinstance(row_data, dict):
                        continue
                        
                    new_row = {}
                    for i, header in enumerate(headers):
                        header_clean = clean_headers[i]
                        if header in row_data:
                            new_row[header_clean] = row_data[header]
                    
                    # Aggiungi la riga solo se ha valori non nulli
                    if any(v is not None for v in new_row.values()):
                        rows.append(new_row)
        
        # Calcola statistiche
        total_items = len(rows)
        total_value = 0
        categories = {}
        
        # Identifica possibili colonne per valori e categorie
        value_col = next((h for h in clean_headers if h.lower() in ["valore", "importo", "colonna 4"]), None)
        category_col = next((h for h in clean_headers if h.lower() in ["categoria", "descrizione", "colonna 3"]), None)
        
        if value_col and category_col:
            for row in rows:
                if value_col in row and row[value_col] is not None:
                    value = row[value_col]
                    if isinstance(value, str):
                        try:
                            value = float(value.replace(",", "."))
                        except (ValueError, TypeError):
                            value = 0
                    
                    category = row.get(category_col, "Non categorizzato")
                    
                    total_value += value
                    
                    if category not in categories:
                        categories[category] = {"count": 0, "value": 0}
                    
                    categories[category]["count"] += 1
                    categories[category]["value"] += value
        
        # Aggiungi le statistiche
        stats = {
            "total_items": total_items,
            "total_value": total_value,
            "categories": [
                {
                    "name": cat,
                    "count": data["count"],
                    "value": data["value"],
                    "percentage": round(data["value"] / total_value * 100, 2) if total_value > 0 else 0
                }
                for cat, data in categories.items()
            ]
        }
        
        # Aggiungi i dati formattati
        magazzino_data["headers"] = clean_headers
        magazzino_data["rows"] = rows
        magazzino_data["stats"] = stats
        
        claude_format["content"] = {
            "magazzino": magazzino_data
        }
        
        # Aggiungi un sommario
        claude_format["summary"] = f"Documento di magazzino con {total_items} articoli per un valore totale di {total_value:.2f}."
        
        # Aggiungi prompt suggeriti
        claude_format["suggested_prompts"] = [
            "Analizza le categorie di prodotti con maggiore incidenza sul valore totale",
            "Crea una rappresentazione visiva della distribuzione del valore per categoria",
            "Identifica articoli con valori anomali o incongruenze",
            "Come potrei ottimizzare la gestione del magazzino in base a questi dati?",
            "Quali sono le categorie di prodotti che richiedono maggiore attenzione?"
        ]
        
        return claude_format
    
    @staticmethod
    def _format_corrispettivo(
        claude_format: Dict[str, Any],
        metadata: Dict[str, Any],
        extracted_data: Dict[str, Any],
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Formatta i dati di un corrispettivo per Claude"""
        
        # Estrai e struttura i dati del corrispettivo
        corrispettivo_data = {}
        
        # Informazioni di base
        corrispettivo_data["numero_documento"] = extracted_data.get("numero_documento", "N/A")
        corrispettivo_data["data"] = extracted_data.get("data", "N/A")
        corrispettivo_data["importo_totale"] = extracted_data.get("importo_totale", 0.0)
        corrispettivo_data["iva"] = extracted_data.get("iva", 0.0)
        corrispettivo_data["esercente"] = extracted_data.get("esercente", {})
        
        # Prodotti
        corrispettivo_data["prodotti"] = []
        if "prodotti" in extracted_data and isinstance(extracted_data["prodotti"], list):
            corrispettivo_data["prodotti"] = extracted_data["prodotti"]
        
        # Aggiungi i dati formattati
        claude_format["content"] = {
            "corrispettivo": corrispettivo_data
        }
        
        # Aggiungi un sommario
        esercente = corrispettivo_data["esercente"].get("nome", "Esercente sconosciuto")
        importo = corrispettivo_data["importo_totale"]
        data = corrispettivo_data["data"]
        
        claude_format["summary"] = f"Corrispettivo emesso da {esercente} per un importo di {importo} in data {data}."
        
        # Aggiungi prompt suggeriti
        claude_format["suggested_prompts"] = [
            "Analizza le voci di questo scontrino/corrispettivo",
            "Verifica la correttezza degli importi in questo corrispettivo",
            "Categorizza le spese presenti in questo scontrino",
            "Confronta questo scontrino con altri simili",
            "Come potrei utilizzare questi dati per ottimizzare le mie spese?"
        ]
        
        return claude_format
    
    @staticmethod
    def _format_analisi_mercato(
        claude_format: Dict[str, Any],
        metadata: Dict[str, Any],
        extracted_data: Dict[str, Any],
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Formatta i dati di un'analisi di mercato per Claude"""
        
        # Estrai e struttura i dati dell'analisi di mercato
        analisi_data = {}
        
        # Informazioni di base
        analisi_data["titolo"] = extracted_data.get("titolo", "Analisi di mercato")
        analisi_data["periodo"] = extracted_data.get("periodo", "N/A")
        analisi_data["settore"] = extracted_data.get("settore", "N/A")
        
        # Dati analitici
        analisi_data["dati_analitici"] = extracted_data.get("dati_analitici", [])
        analisi_data["grafici_descrizioni"] = extracted_data.get("grafici_descrizioni", [])
        analisi_data["conclusioni"] = extracted_data.get("conclusioni", "")
        
        # Gestisci anche i dati tabellari
        if "tabella" in extracted_data:
            analisi_data["tabella"] = extracted_data["tabella"]
        
        # Aggiungi i dati formattati
        claude_format["content"] = {
            "analisi_mercato": analisi_data
        }
        
        # Aggiungi un sommario
        titolo = analisi_data["titolo"]
        settore = analisi_data["settore"]
        periodo = analisi_data["periodo"]
        
        claude_format["summary"] = f"Analisi di mercato: {titolo}. Settore: {settore}. Periodo: {periodo}."
        
        # Aggiungi prompt suggeriti
        claude_format["suggested_prompts"] = [
            "Riassumi i punti principali di questa analisi di mercato",
            "Quali sono le tendenze chiave evidenziate in questa analisi?",
            "Come potrei utilizzare queste informazioni per decisioni strategiche?",
            "Quali fattori esterni potrebbero influenzare i dati presentati in questa analisi?",
            "Confronta questa analisi con i dati di settore più recenti"
        ]
        
        return claude_format
    
    @staticmethod
    def _format_generico(
        claude_format: Dict[str, Any],
        metadata: Dict[str, Any],
        extracted_data: Dict[str, Any],
        raw_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Formatta i dati di un documento generico per Claude"""
        
        # Per documenti generici, manteniamo la struttura originale ma la ottimizziamo
        generic_data = {}
        
        # Aggiungi tutti i dati estratti
        for key, value in extracted_data.items():
            generic_data[key] = value
        
        # Se abbiamo dati tabellari, formattali in modo leggibile
        if "rows" in extracted_data and isinstance(extracted_data["rows"], (list, dict)):
            if isinstance(extracted_data["rows"], dict):
                generic_data["rows_formatted"] = list(extracted_data["rows"].values())
            else:
                generic_data["rows_formatted"] = extracted_data["rows"]
        
        # Aggiungi il testo grezzo se disponibile
        if raw_text:
            generic_data["raw_text"] = raw_text
        
        # Aggiungi i dati formattati
        claude_format["content"] = {
            "generic_document": generic_data
        }
        
        # Aggiungi un sommario
        file_name = metadata.get("original_filename", "documento")
        file_type = metadata.get("file_type", "sconosciuto")
        
        claude_format["summary"] = f"Documento generico: {file_name} (tipo: {file_type})."
        
        # Aggiungi prompt suggeriti
        claude_format["suggested_prompts"] = [
            "Analizza i dati contenuti in questo documento",
            "Riassumi le informazioni chiave presenti in questo documento",
            "Quale tipo di documento potrebbe essere questo in base ai dati estratti?",
            "Come potrei utilizzare queste informazioni per scopi aziendali?",
            "Identifica pattern o tendenze in questi dati"
        ]
        
        return claude_format
