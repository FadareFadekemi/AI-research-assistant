import os
import shutil
import logging
import pandas as pd
from fastapi import UploadFile, HTTPException
from uuid import uuid4

UPLOAD_DIR = "temp_uploads"
MAX_FILE_SIZE_MB = 50

os.makedirs(UPLOAD_DIR, exist_ok=True)

import pandas as pd
from io import BytesIO

async def get_dataset_metadata(dataset):
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

    # Read the dataset content
    content = await dataset.read()
    dataset.file.seek(0)  # reset stream pointer

    # Load into DataFrame
    try:
        if dataset.filename.lower().endswith(".csv"):
            df = pd.read_csv(BytesIO(content))
        else:
            df = pd.read_excel(BytesIO(content))
    except Exception:
        return None

    return {
        "filename": dataset.filename,
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "columns": list(df.columns)
    }

async def save_and_load_dataset(file: UploadFile) -> tuple[str, pd.DataFrame]:
    logger = logging.getLogger(__name__)

    if getattr(file, "size", None) and file.size > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    ext = (file.filename or "").split(".")[-1].lower()
    path = f"{UPLOAD_DIR}/{uuid4()}.{ext or 'dat'}"

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # Try parsing with sensible fallbacks
        if ext == "csv":
            try:
                df = pd.read_csv(path)
            except (UnicodeDecodeError, ValueError):
                df = pd.read_csv(path, encoding="latin1")
        elif ext in {"xls", "xlsx"}:
            last_exc = None
            for engine in (None, "openpyxl", "xlrd"):
                try:
                    if engine is None:
                        df = pd.read_excel(path)
                    else:
                        df = pd.read_excel(path, engine=engine)
                    break
                except Exception as e:
                    last_exc = e
                    continue
            else:
                msg = str(last_exc) if last_exc else "Failed to parse Excel file"
                if "Excel file format cannot be determined" in msg or "engine" in msg.lower():
                    msg += " — try installing 'openpyxl' (`pip install openpyxl`) for .xlsx files or 'xlrd' for .xls, or save the file as CSV."
                raise Exception(msg)
        else:
            # unknown extension: try CSV then Excel
            try:
                df = pd.read_csv(path)
            except Exception as e_csv:
                last_exc = None
                for engine in (None, "openpyxl", "xlrd"):
                    try:
                        if engine is None:
                            df = pd.read_excel(path)
                        else:
                            df = pd.read_excel(path, engine=engine)
                        break
                    except Exception as e_xl:
                        last_exc = e_xl
                        continue
                else:
                    msg = f"Could not parse file as CSV ({e_csv}) or Excel ({last_exc})"
                    if last_exc and ("Excel file format cannot be determined" in str(last_exc) or "engine" in str(last_exc).lower()):
                        msg += " — try installing 'openpyxl' (`pip install openpyxl`) for .xlsx files or 'xlrd' for .xls, or save the file as CSV."
                    raise Exception(msg)
    except Exception as e:
        try:
            os.remove(path)
        except Exception:
            logger.debug("Failed to remove path after parse failure: %s", path, exc_info=True)
        logger.exception("Failed to parse uploaded dataset %s: %s", file.filename, e)
        raise HTTPException(status_code=400, detail=f"Invalid dataset format: {str(e)}")

    if df.empty:
        logger.warning("Uploaded dataset parsed but is empty: %s", file.filename)
        raise HTTPException(status_code=400, detail="Dataset is empty")

    # Normalize column names
    df.columns = [str(col) for col in df.columns]

    return path, df
