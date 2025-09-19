"""
Servizio per l'elaborazione di file Excel
"""
import io
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from fastapi import UploadFile

from app.utils.logging_utils import get_logger

logger = get_logger(__name__)


class ExcelProcessor:
    """
    Classe per l'elaborazione di file Excel
    """
    
    @staticmethod
    async def process_excel(
        file: UploadFile, 
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Elabora un file Excel e lo converte in formato JSON
        
        Args:
            file: File Excel caricato
            document_type: Tipo di documento (opzionale)
            
        Returns:
            Dizionario con i dati estratti dal file Excel
        """
        logger.info(f"Elaborazione file Excel: {file.filename}")
        
        # Leggi il contenuto del file
        content = await file.read()
        
        # Converti in formato JSON
        result = ExcelProcessor._excel_to_json(content, file.filename, document_type)
        
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
            logger.info(f"Elaborazione foglio: {sheet_name}")
            
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
        detected_type = document_type or ExcelProcessor._detect_document_type(sheets_dict, filename)
        
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
    def _detect_document_type(sheets_dict: Dict[str, List[Dict]], filename: str) -> str:
        """
        Tenta di rilevare il tipo di documento in base al contenuto
        
        Args:
            sheets_dict: Dizionario con i dati dei fogli
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
            for sheet_name, sheet_data in sheets_dict.items():
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
