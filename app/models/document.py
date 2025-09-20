"""
Modelli Pydantic per documenti
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class DocumentRequest(BaseModel):
    """
    Modello per la richiesta di elaborazione documento
    """
    document_type: Optional[str] = None
    

class SheetInfo(BaseModel):
    """
    Informazioni su un foglio di dati tabulari (Excel o CSV)
    """
    name: str
    rows: int
    columns: int
    column_names: List[str]


class TabularMetadata(BaseModel):
    """
    Metadati di un file tabellare (Excel o CSV)
    """
    original_filename: str
    file_type: str
    sheet_count: int
    sheets: List[SheetInfo]
    separator: Optional[str] = None  # Solo per CSV


class TabularDocument(BaseModel):
    """
    Documento tabellare (Excel o CSV) elaborato
    """
    document_type: str
    metadata: TabularMetadata
    extracted_data: Dict[str, List[Dict[str, Any]]]
    processing_notes: List[str] = []
