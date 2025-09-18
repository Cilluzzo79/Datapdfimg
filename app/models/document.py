from pydantic import BaseModel, Field, validator, RootModel
from typing import List, Dict, Any, Optional, Literal
from enum import Enum
from datetime import datetime
import uuid


class DocumentType(str, Enum):
    FATTURA = "fattura"
    BILANCIO = "bilancio"
    MAGAZZINO = "magazzino"
    CORRISPETTIVO = "corrispettivo"
    ANALISI_MERCATO = "analisi_mercato"
    SCONOSCIUTO = "sconosciuto"


class FileType(str, Enum):
    PDF = "pdf"
    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"


class DocumentMetadata(BaseModel):
    original_filename: str
    file_type: FileType
    file_size: int = Field(..., description="Dimensione del file in bytes")
    pages_processed: int = Field(1, description="Numero di pagine processate")
    processing_time_ms: Optional[int] = None
    md5_hash: Optional[str] = None


class ProcessingRequest(BaseModel):
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_type_hint: Optional[DocumentType] = None
    custom_metadata: Optional[Dict[str, Any]] = None


class FatturaData(BaseModel):
    numero_fattura: Optional[str] = None
    data_fattura: Optional[str] = None
    importo_totale: Optional[float] = None
    iva: Optional[float] = None
    mittente: Optional[Dict[str, str]] = None
    destinatario: Optional[Dict[str, str]] = None
    righe_fattura: Optional[List[Dict[str, Any]]] = None
    valuta: Optional[str] = "EUR"


class BilancioData(BaseModel):
    tipo_bilancio: Optional[str] = None
    periodo: Optional[str] = None
    attivita: Optional[Dict[str, float]] = None
    passivita: Optional[Dict[str, float]] = None
    patrimonio_netto: Optional[float] = None
    ricavi: Optional[float] = None
    costi: Optional[float] = None
    utile_perdita: Optional[float] = None


class MagazzinoData(BaseModel):
    tipo_documento: Optional[str] = None
    data: Optional[str] = None
    articoli: Optional[List[Dict[str, Any]]] = None
    totale_quantita: Optional[float] = None
    totale_valore: Optional[float] = None
    magazzino_codice: Optional[str] = None


class CorrispettivoData(BaseModel):
    numero_documento: Optional[str] = None
    data: Optional[str] = None
    importo_totale: Optional[float] = None
    iva: Optional[float] = None
    esercente: Optional[Dict[str, str]] = None
    prodotti: Optional[List[Dict[str, Any]]] = None


class AnalisiMercatoData(BaseModel):
    titolo: Optional[str] = None
    periodo: Optional[str] = None
    settore: Optional[str] = None
    dati_analitici: Optional[Dict[str, Any]] = None
    grafici_descrizioni: Optional[List[str]] = None
    conclusioni: Optional[str] = None


class ExtractedData(BaseModel):
    """Dati estratti dal documento, la struttura dipende dal tipo di documento"""
    data: Dict[str, Any] = Field(default_factory=dict)
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
    
    def __contains__(self, key):
        return key in self.data
    
    def dict(self):
        return self.data
        
    def model_dump(self):
        return self.data


class ProcessingNote(BaseModel):
    """Nota sul processo di elaborazione"""
    type: Literal["info", "warning", "error"]
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)


class DocumentProcessingResult(BaseModel):
    """Risultato del processamento del documento"""
    document_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    processing_timestamp: datetime = Field(default_factory=datetime.now)
    document_type: DocumentType = DocumentType.SCONOSCIUTO
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    metadata: DocumentMetadata
    extracted_data: Dict[str, Any] = {}
    raw_text: str
    processing_notes: List[str] = []
    llm_ready: bool = True

    def get_typed_extracted_data(self):
        """Restituisce i dati estratti tipizzati in base al tipo di documento"""
        if self.document_type == DocumentType.FATTURA:
            return FatturaData(**self.extracted_data)
        elif self.document_type == DocumentType.BILANCIO:
            return BilancioData(**self.extracted_data)
        elif self.document_type == DocumentType.MAGAZZINO:
            return MagazzinoData(**self.extracted_data)
        elif self.document_type == DocumentType.CORRISPETTIVO:
            return CorrispettivoData(**self.extracted_data)
        elif self.document_type == DocumentType.ANALISI_MERCATO:
            return AnalisiMercatoData(**self.extracted_data)
        else:
            return self.extracted_data





