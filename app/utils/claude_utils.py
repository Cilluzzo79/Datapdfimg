"""
Utilità per formattare e ottimizzare dati per Claude Sonnet 3.7
"""
import re
from typing import Dict, Any, List, Optional, Union

def clean_column_name(name: str) -> str:
    """
    Pulisce un nome di colonna per renderlo più leggibile
    
    Args:
        name: Nome della colonna
        
    Returns:
        Nome della colonna pulito
    """
    if not name:
        return ""
        
    # Gestisci colonne "Unnamed: X"
    if isinstance(name, str) and name.startswith("Unnamed: "):
        try:
            col_num = int(name.replace("Unnamed: ", ""))
            return f"Colonna {col_num+1}"
        except (ValueError, TypeError):
            pass
    
    # Altri casi
    if isinstance(name, str):
        # Capitalizza la prima lettera
        clean_name = name.strip()
        if clean_name:
            clean_name = clean_name[0].upper() + clean_name[1:]
        return clean_name
    
    return str(name)

def extract_table_data(
    extracted_data: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Estrae dati tabellari da un documento
    
    Args:
        extracted_data: Dati estratti dal documento
        metadata: Metadati del documento (opzionale)
        
    Returns:
        Dati tabellari estratti
    """
    result = {
        "headers": [],
        "rows": [],
        "stats": {}
    }
    
    # Estrai le intestazioni
    headers = []
    
    # Cerca le intestazioni nei metadati
    if metadata and "column_names" in metadata:
        if isinstance(metadata["column_names"], dict):
            # Ordina le colonne per indice
            try:
                sorted_cols = sorted(
                    [(int(k.replace("column_", "")) if k.startswith("column_") else int(k), v) 
                     for k, v in metadata["column_names"].items()], 
                    key=lambda x: x[0]
                )
                headers = [col[1] for col in sorted_cols]
            except (ValueError, TypeError):
                # Fallback: usa le chiavi senza ordinamento
                headers = list(metadata["column_names"].values())
        elif isinstance(metadata["column_names"], list):
            headers = metadata["column_names"]
    
    # Se non abbiamo trovato intestazioni, cerchiamo di determinarle
    if not headers:
        col_pattern = r"^Unnamed: \d+$"
        unnamed_cols = []
        
        # Cerca colonne tipo "Unnamed: X"
        for key in extracted_data.keys():
            if isinstance(key, str) and re.match(col_pattern, key):
                unnamed_cols.append(key)
        
        if unnamed_cols:
            # Ordina per numero di colonna
            headers = sorted(
                unnamed_cols,
                key=lambda x: int(x.replace("Unnamed: ", ""))
            )
            
            # Aggiungi "Incidenza" se presente
            if "Incidenza" in extracted_data and "Incidenza" not in headers:
                headers.append("Incidenza")
    
    # Se ancora non abbiamo intestazioni, usa predefinite
    if not headers:
        headers = ["Colonna 1", "Colonna 2", "Colonna 3", "Colonna 4", "Colonna 5"]
    
    # Pulisci le intestazioni
    clean_headers = [clean_column_name(h) for h in headers]
    result["headers"] = clean_headers
    
    # Estrai le righe
    rows = []
    
    # Cerca le righe in diversi formati
    if "rows" in extracted_data:
        if isinstance(extracted_data["rows"], dict):
            rows_data = list(extracted_data["rows"].values())
        else:
            rows_data = extracted_data["rows"]
        
        for row in rows_data:
            if isinstance(row, dict):
                new_row = {}
                for i, header in enumerate(headers):
                    if i < len(clean_headers):
                        clean_header = clean_headers[i]
                        # Cerca il valore in varie posizioni possibili
                        value = row.get(header)
                        if value is None and header.startswith("Unnamed: "):
                            # Prova con l'indice
                            col_idx = int(header.replace("Unnamed: ", ""))
                            value = row.get(col_idx)
                        
                        new_row[clean_header] = value
                
                # Aggiungi la riga solo se ha almeno un valore non nullo
                if any(v is not None for v in new_row.values()):
                    rows.append(new_row)
    
    # Cerca anche in chiavi di tipo "31-05-2025" (nome del foglio)
    if not rows:
        sheet_key = None
        for key in extracted_data.keys():
            if isinstance(key, str) and re.match(r"\d{2}-\d{2}-\d{4}", key):
                sheet_key = key
                break
                
        if sheet_key and isinstance(extracted_data[sheet_key], dict):
            for row_idx, row_data in extracted_data[sheet_key].items():
                if isinstance(row_data, dict):
                    new_row = {}
                    for i, header in enumerate(headers):
                        if i < len(clean_headers):
                            clean_header = clean_headers[i]
                            # Cerca il valore per questa cella
                            value = None
                            if header in row_data:
                                value = row_data[header]
                            elif isinstance(header, str) and header.startswith("Unnamed: "):
                                col_idx = int(header.replace("Unnamed: ", ""))
                                if col_idx in row_data:
                                    value = row_data[col_idx]
                            
                            new_row[clean_header] = value
                    
                    # Aggiungi la riga solo se ha almeno un valore non nullo
                    if any(v is not None for v in new_row.values()):
                        rows.append(new_row)
    
    # Ultimo tentativo: controlla se abbiamo colonne di tipo Unnamed: X con valori
    if not rows:
        col_pattern = r"^Unnamed: \d+$"
        row_pattern = r"^\d+$"
        row_data_map = {}
        
        for col_key, col_values in extracted_data.items():
            if isinstance(col_key, str) and re.match(col_pattern, col_key):
                if isinstance(col_values, dict):
                    col_idx = int(col_key.replace("Unnamed: ", ""))
                    for row_idx, cell_value in col_values.items():
                        if isinstance(row_idx, str) and re.match(row_pattern, row_idx):
                            row_int = int(row_idx)
                            if row_int not in row_data_map:
                                row_data_map[row_int] = {}
                            
                            clean_header = clean_headers[headers.index(col_key)] if col_key in headers and headers.index(col_key) < len(clean_headers) else f"Colonna {col_idx+1}"
                            row_data_map[row_int][clean_header] = cell_value
        
        # Aggiungi le righe ordinate
        for row_idx in sorted(row_data_map.keys()):
            row = row_data_map[row_idx]
            if any(v is not None for v in row.values()):
                rows.append(row)
    
    result["rows"] = rows
    
    # Calcola statistiche
    total_items = len(rows)
    total_value = 0.0
    categories = {}
    
    # Identifica possibili colonne per valori e categorie
    value_col = None
    for col in clean_headers:
        for row in rows:
            if col in row and isinstance(row[col], (int, float)) and col.lower() not in ["incidenza"]:
                value_col = col
                break
        if value_col:
            break
    
    category_col = None
    for col in clean_headers:
        if col.lower() in ["categoria", "descrizione", "colonna 3"]:
            category_col = col
            break
    
    # Se abbiamo trovato colonne, calcola le statistiche
    if value_col and category_col:
        for row in rows:
            if value_col in row and row[value_col] is not None:
                value = row[value_col]
                if isinstance(value, str):
                    try:
                        value = float(value.replace(",", "."))
                    except (ValueError, TypeError):
                        value = 0.0
                elif isinstance(value, (int, float)):
                    value = float(value)
                else:
                    value = 0.0
                
                total_value += value
                
                if category_col in row and row[category_col]:
                    category = str(row[category_col])
                    if category not in categories:
                        categories[category] = {"count": 0, "value": 0.0}
                    
                    categories[category]["count"] += 1
                    categories[category]["value"] += value
    
    # Aggiungi le statistiche calcolate
    result["stats"] = {
        "total_items": total_items,
        "total_value": total_value,
        "categories": [
            {
                "name": cat,
                "count": data["count"],
                "value": data["value"],
                "percentage": round(data["value"] / total_value * 100, 2) if total_value > 0 else 0.0
            }
            for cat, data in categories.items()
        ]
    }
    
    return result

def generate_table_text(headers: List[str], rows: List[Dict[str, Any]]) -> str:
    """
    Genera una rappresentazione testuale di una tabella
    
    Args:
        headers: Intestazioni della tabella
        rows: Righe della tabella
        
    Returns:
        Rappresentazione testuale della tabella
    """
    if not headers or not rows:
        return "Nessun dato tabellare disponibile."
    
    # Determina la larghezza massima per ogni colonna
    col_widths = [len(h) for h in headers]
    
    for row in rows:
        for i, header in enumerate(headers):
            if header in row:
                val = row[header]
                val_str = str(val) if val is not None else ""
                if len(val_str) > col_widths[i]:
                    col_widths[i] = len(val_str)
    
    # Crea la riga di intestazione
    header_row = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    separator = "-" * len(header_row)
    
    # Crea le righe di dati
    data_rows = []
    for row in rows:
        row_str = " | ".join(
            str(row.get(h, "")).ljust(col_widths[i]) if row.get(h) is not None else "".ljust(col_widths[i])
            for i, h in enumerate(headers)
        )
        data_rows.append(row_str)
    
    # Assembla la tabella
    table = f"{header_row}\n{separator}\n" + "\n".join(data_rows)
    
    return table
