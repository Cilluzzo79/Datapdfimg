"""
Servizio per l'elaborazione di file tabulari (Excel e CSV)
"""
import io
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from fastapi import UploadFile

from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class TabularProcessor:
    """
    Classe per l'elaborazione di file tabulari (Excel e CSV)
    """
    
    @staticmethod
    async def process_tabular(
        file: UploadFile, 
        file_type: str,
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Elabora un file tabellare (Excel o CSV) e lo converte in formato JSON
        
        Args:
            file: File tabellare caricato
            file_type: Tipo di file ('excel' o 'csv')
            document_type: Tipo di documento (opzionale)
            
        Returns:
            Dizionario con i dati estratti dal file
        """
        logger.info(f"Elaborazione file tabellare: {file.filename}, tipo: {file_type}")
        
        # Leggi il contenuto del file
        content = await file.read()
        
        # Converti in formato JSON
        if file_type == "excel":
            result = TabularProcessor._excel_to_json(content, file.filename, document_type)
        elif file_type == "csv":
            result = TabularProcessor._csv_to_json(content, file.filename, document_type)
        else:
            logger.error(f"Tipo di file non supportato: {file_type}")
            result = {
                "document_type": "error",
                "metadata": {
                    "original_filename": file.filename,
                    "file_type": file_type,
                    "error": f"Tipo di file non supportato: {file_type}"
                },
                "processing_notes": ["Tipo di file non supportato"]
            }
        
        # Riposiziona il cursore all'inizio del file
        await file.seek(0)
        
        return result
    
    @staticmethod
    def _excel_to_json(
        file_content: bytes, 
        filename: str, 
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Converte un file Excel in formato JSON
        
        Args:
            file_content: Contenuto del file Excel
            filename: Nome del file
            document_type: Tipo di documento (opzionale)
            
        Returns:
            Dizionario con i dati estratti dal file Excel
        """
        # Crea un BytesIO object dal contenuto del file
        excel_data = io.BytesIO(file_content)
        
        # Leggi tutti i fogli del file Excel in un dizionario di DataFrame
        sheets_dict = {}
        excel_file = pd.ExcelFile(excel_data)
        
        # Informazioni sui fogli
        sheet_info = []
        
        for sheet_name in excel_file.sheet_names:
            logger.info(f"Elaborazione foglio Excel: {sheet_name}")
            
            # Leggi il foglio
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            
            # Converti il DataFrame in una lista di dizionari
            sheet_data = df.to_dict(orient='records')
            
            # Salva il foglio nel dizionario
            sheets_dict[sheet_name] = sheet_data
            
            # Aggiungi informazioni sul foglio
            sheet_info.append({
                "name": sheet_name,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist()
            })
        
        # Analisi del tipo di documento
        detected_type = document_type or TabularProcessor._detect_document_type(sheets_dict, filename)
        
        # Crea il risultato
        result = {
            "document_type": detected_type,
            "metadata": {
                "original_filename": filename,
                "file_type": "excel",
                "sheet_count": len(sheets_dict),
                "sheets": sheet_info
            },
            "extracted_data": sheets_dict,
            "processing_notes": []
        }
        
        return result
    
    @staticmethod
    def _csv_to_json(
        file_content: bytes, 
        filename: str, 
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Converte un file CSV in formato JSON
        
        Args:
            file_content: Contenuto del file CSV
            filename: Nome del file
            document_type: Tipo di documento (opzionale)
            
        Returns:
            Dizionario con i dati estratti dal file CSV
        """
        logger.info(f"Elaborazione file CSV: {filename}")
        
        # Converti il contenuto in stringa
        try:
            # Prova con codifica UTF-8
            file_content_str = file_content.decode('utf-8')
        except UnicodeDecodeError:
            # Se fallisce, prova con codifica ISO-8859-1 (Latin-1)
            try:
                file_content_str = file_content.decode('iso-8859-1')
            except UnicodeDecodeError:
                # Se fallisce ancora, prova con codifica Windows-1252
                file_content_str = file_content.decode('cp1252')
        
        # Rileva automaticamente il separatore
        first_line = file_content_str.split('\n')[0]
        separator = ','  # Default a virgola
        
        if ';' in first_line:
            separator = ';'
        elif '\t' in first_line:
            separator = '\t'
        elif '|' in first_line:
            separator = '|'
        
        logger.info(f"Separatore rilevato per CSV: '{separator}'")
        
        # Crea un DataFrame dal contenuto CSV
        df = pd.read_csv(
            io.StringIO(file_content_str), 
            sep=separator,
            encoding='utf-8',
            engine='python',
            error_bad_lines=False,  # Ignora righe con errori
            on_bad_lines='skip',    # Ignora righe malformate
            dtype=str              # Legge tutto come stringhe inizialmente
        )
        
        # Converti il DataFrame in una lista di dizionari
        data = df.to_dict(orient='records')
        
        # Analisi del tipo di documento
        table_data = {"main": data}
        detected_type = document_type or TabularProcessor._detect_document_type(table_data, filename)
        
        # Informazioni sul foglio
        sheet_info = [{
            "name": "main",
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist()
        }]
        
        # Crea il risultato
        result = {
            "document_type": detected_type,
            "metadata": {
                "original_filename": filename,
                "file_type": "csv",
                "separator": separator,
                "sheet_count": 1,
                "sheets": sheet_info
            },
            "extracted_data": {"main": data},
            "processing_notes": []
        }
        
        return result
    
    @staticmethod
    def _detect_document_type(data_dict: Dict[str, List[Dict]], filename: str) -> str:
        """
        Tenta di rilevare il tipo di documento in base al contenuto
        
        Args:
            data_dict: Dizionario con i dati dei fogli/CSV
            filename: Nome del file
            
        Returns:
            Tipo di documento rilevato
        """
        # Implementazione semplice basata sul nome del file
        filename_lower = filename.lower()
        
        if any(keyword in filename_lower for keyword in ["fattura", "invoice"]):
            return "fattura"
        elif any(keyword in filename_lower for keyword in ["bilancio", "balance"]):
            return "bilancio"
        elif any(keyword in filename_lower for keyword in ["magazzino", "inventory", "stock"]):
            return "magazzino"
        elif any(keyword in filename_lower for keyword in ["corrispettivo", "receipt"]):
            return "corrispettivo"
        elif any(keyword in filename_lower for keyword in ["analisi", "report", "analysis"]):
            return "analisi_mercato"
        else:
            # Analisi basata sulle intestazioni delle colonne
            for sheet_name, sheet_data in data_dict.items():
                if not sheet_data:
                    continue
                
                # Prendi le chiavi del primo record
                columns = sheet_data[0].keys()
                columns_str = " ".join(str(col).lower() for col in columns)
                
                if any(keyword in columns_str for keyword in ["fattura", "invoice", "importo", "iva"]):
                    return "fattura"
                elif any(keyword in columns_str for keyword in ["bilancio", "balance", "attivo", "passivo"]):
                    return "bilancio"
                elif any(keyword in columns_str for keyword in ["magazzino", "inventory", "stock", "quantità"]):
                    return "magazzino"
                elif any(keyword in columns_str for keyword in ["corrispettivo", "receipt", "scontrino"]):
                    return "corrispettivo"
                elif any(keyword in columns_str for keyword in ["analisi", "report", "mercato", "trend"]):
                    return "analisi_mercato"
        
        # Default
        return "documento_generico"
