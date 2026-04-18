"""
PaisaSense AI — File Parser
Handles CSV and PDF bank statement parsing into normalized DataFrames.
"""

import io
import re
import pandas as pd
from categorizer import extract_merchant, categorize_transaction


def parse_csv(text: str) -> pd.DataFrame:
    """
    Parse CSV text into a normalized DataFrame.
    Supports simple CSVs (Date, Amount, Merchant) and real bank exports
    from HDFC / PNB that carry a Narration or Description column.
    PNB multi-line narrations are merged before parsing.
    """
    # Fix PNB multi-line narrations: continuation lines don't start with a date
    date_start = re.compile(r'^\d{1,2}[\/\-]')
    cleaned_lines = []
    for line in text.splitlines():
        if cleaned_lines and not date_start.match(line.strip()):
            cleaned_lines[-1] += " " + line.strip()
        else:
            cleaned_lines.append(line)
    text = "\n".join(cleaned_lines)

    df = pd.read_csv(io.StringIO(text))
    df.columns = [c.strip() for c in df.columns]

    col_map = {c.lower(): c for c in df.columns}

    # Date
    date_col = next((col_map[k] for k in col_map if "date" in k), None)
    if date_col:
        df["Date"] = pd.to_datetime(df[date_col], dayfirst=True, errors="coerce")

    # Amount — prefer Debit/Withdrawal for expense rows
    amount_col = next(
        (col_map[k] for k in col_map
         if k in ("debit", "withdrawal", "withdrawal amt.", "amount")),
        None
    )
    if amount_col:
        df["Amount"] = pd.to_numeric(
            df[amount_col].astype(str).str.replace(",", ""), errors="coerce"
        ).abs()

    # Narration / Description → merchant + category
    narration_col = next(
        (col_map[k] for k in col_map
         if k in ("narration", "description", "particulars", "remarks", "details")),
        None
    )

    if narration_col:
        df["Narration"] = df[narration_col].astype(str).str.replace("\n", " ").str.strip()
        df["Merchant"]  = df["Narration"].apply(extract_merchant)
        df["Category"]  = df["Narration"].apply(categorize_transaction)
    elif "merchant" in col_map:
        df["Merchant"] = df[col_map["merchant"]].astype(str).str.strip()
        df["Category"] = df["Merchant"].apply(categorize_transaction)
    else:
        df["Merchant"] = "Unknown"
        df["Category"] = "Others"

    df.dropna(subset=["Date", "Amount"], inplace=True)
    df = df[df["Amount"] > 0].copy()
    return df


def parse_pdf(file_bytes: bytes) -> pd.DataFrame:
    """Extract transactions from a PDF bank statement using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        raise ValueError("PDF parsing failed. Try CSV for best results.")

    records = []
    date_pattern   = re.compile(r'(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4}[\/\-]\d{2}[\/\-]\d{2})')
    amount_pattern = re.compile(r'[\d,]+\.\d{2}')

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            # Try structured table extraction first
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    if not row:
                        continue
                    row_text   = [str(c).strip() if c else "" for c in row]
                    row_joined = " ".join(row_text)
                    date_match = date_pattern.search(row_joined)
                    amounts    = amount_pattern.findall(row_joined)
                    if date_match and amounts:
                        try:
                            date_val   = pd.to_datetime(date_match.group(), dayfirst=True, errors="coerce")
                            amount_val = float(amounts[-1].replace(",", ""))
                            merchant   = _extract_merchant_from_row(row_text, date_match.group(), amounts)
                            if pd.notna(date_val) and amount_val > 0:
                                records.append({"Date": date_val, "Amount": amount_val, "Merchant": merchant})
                        except Exception:
                            continue

            # Fallback: line-by-line text parsing
            if not records:
                text = page.extract_text() or ""
                for line in text.split("\n"):
                    date_match = date_pattern.search(line)
                    amounts    = amount_pattern.findall(line)
                    if date_match and amounts:
                        try:
                            date_val   = pd.to_datetime(date_match.group(), dayfirst=True, errors="coerce")
                            amount_val = float(amounts[-1].replace(",", ""))
                            start      = date_match.end()
                            end        = line.rfind(amounts[-1])
                            merchant   = line[start:end].strip() if end > start else "Unknown"
                            merchant   = re.sub(r'[^\w\s]', '', merchant).strip() or "Unknown"
                            if pd.notna(date_val) and amount_val > 0:
                                records.append({"Date": date_val, "Amount": amount_val, "Merchant": merchant})
                        except Exception:
                            continue

    if not records:
        raise ValueError("PDF parsing failed. Try CSV for best results.")

    df = pd.DataFrame(records)
    df["Date"]   = pd.to_datetime(df["Date"], errors="coerce")
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").abs()
    df.dropna(subset=["Date", "Amount"], inplace=True)
    return df


def _extract_merchant_from_row(row_cells: list, date_str: str, amounts: list) -> str:
    """Best-effort merchant name extraction from a table row."""
    candidates = []
    for cell in row_cells:
        cell = cell.strip()
        if not cell or date_str in cell:
            continue
        if re.match(r'^[\d\.,\-\+\s]+$', cell):
            continue
        if len(cell) > 2:
            candidates.append(cell)
    return candidates[0] if candidates else "Unknown"


def parse_file(file) -> pd.DataFrame:
    """Unified file parser — detects CSV vs PDF automatically."""
    filename = file.filename.lower()
    if filename.endswith(".pdf"):
        return parse_pdf(file.read())
    elif filename.endswith(".csv"):
        return parse_csv(file.read().decode("utf-8", errors="ignore"))
    else:
        raise ValueError("Unsupported file type. Please upload a .csv or .pdf file.")
