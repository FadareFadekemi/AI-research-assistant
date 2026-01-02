import os
import shutil
import logging
import pandas as pd
from fastapi import UploadFile, HTTPException
from uuid import uuid4
from io import BytesIO


UPLOAD_DIR = "temp_uploads"
MAX_FILE_SIZE_MB = 50
os.makedirs(UPLOAD_DIR, exist_ok=True)

logger = logging.getLogger(__name__)


async def get_dataset_metadata(dataset: UploadFile) -> dict | None:
    """
    Returns basic metadata of an uploaded dataset without fully processing it.

    Args:
        dataset: UploadFile or similar object with `.read()` and `.filename`

    Returns:
        dict: {
            'filename': str,
            'num_rows': int,
            'num_columns': int,
            'columns': list[str]
        } or None if no dataset provided
    """
    if not dataset:
        return None

   
    content = await dataset.read()
    dataset.file.seek(0)  

   
    try:
        if dataset.filename.lower().endswith(".csv"):
            df = pd.read_csv(BytesIO(content))
        else:
            df = pd.read_excel(BytesIO(content))
    except Exception as e:
        logger.warning("Failed to read dataset for metadata: %s", e)
        return None

    return {
        "filename": dataset.filename,
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "columns": list(df.columns)
    }


async def save_and_load_dataset(file: UploadFile) -> tuple[str, pd.DataFrame]:
    """
    Save uploaded file to temp folder and load as DataFrame.
    Supports CSV and Excel (.xls, .xlsx). Handles encoding and engine fallbacks.
    """
    if getattr(file, "size", None) and file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    ext = (file.filename or "").split(".")[-1].lower()
    path = os.path.join(UPLOAD_DIR, f"{uuid4()}.{ext or 'dat'}")

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        
        df = None
        if ext == "csv":
            try:
                df = pd.read_csv(path)
            except (UnicodeDecodeError, ValueError):
                df = pd.read_csv(path, encoding="latin1")
        elif ext in {"xls", "xlsx"}:
            last_exc = None
            for engine in (None, "openpyxl", "xlrd"):
                try:
                    df = pd.read_excel(path, engine=engine)
                    break
                except Exception as e:
                    last_exc = e
                    continue
            if df is None:
                msg = f"Failed to parse Excel file: {last_exc}"
                raise Exception(msg)
        else:
            # unknown extension: try CSV then Excel
            try:
                df = pd.read_csv(path)
            except Exception as e_csv:
                last_exc = None
                for engine in (None, "openpyxl", "xlrd"):
                    try:
                        df = pd.read_excel(path, engine=engine)
                        break
                    except Exception as e_xl:
                        last_exc = e_xl
                        continue
                else:
                    msg = f"Could not parse file as CSV ({e_csv}) or Excel ({last_exc})"
                    raise Exception(msg)
    except Exception as e:
        try:
            os.remove(path)
        except Exception:
            logger.debug("Failed to remove file after parse failure: %s", path, exc_info=True)
        logger.exception("Failed to parse uploaded dataset %s: %s", file.filename, e)
        raise HTTPException(status_code=400, detail=f"Invalid dataset format: {str(e)}")

    if df.empty:
        logger.warning("Uploaded dataset parsed but is empty: %s", file.filename)
        raise HTTPException(status_code=400, detail="Dataset is empty")

    df.columns = [str(col) for col in df.columns]

    return path, df


def export_results_to_excel(results: dict, excel_path: str = "analysis_results.xlsx") -> str:
    """
    Export analysis results (dicts/lists) to a multi-sheet Excel workbook.

    Args:
        results: dictionary of analysis results
        excel_path: target Excel file path

    Returns:
        path to generated Excel file
    """
    with pd.ExcelWriter(excel_path) as writer:
        for key, value in results.items():
            try:
                if isinstance(value, dict) and "result" in value:
                    df_out = pd.DataFrame(value["result"])
                elif isinstance(value, dict):
                    df_out = pd.DataFrame([value])
                else:
                    df_out = pd.DataFrame([value])
                df_out.to_excel(writer, sheet_name=key[:31], index=False)
            except Exception as e:
                logger.warning("Failed to write sheet %s: %s", key, e)

    return excel_path
