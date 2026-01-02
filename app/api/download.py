import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["Downloads"])


ALLOWED_BASE_DIRS = [
    "outputs",
    "temp_uploads",
]


@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """
    Secure file download endpoint.

    Example:
    /download/outputs/plots/countplot.png
    """

    
    safe_path = os.path.normpath(file_path)

    
    if ".." in safe_path or safe_path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid file path")

    
    if not any(safe_path.startswith(base) for base in ALLOWED_BASE_DIRS):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=safe_path,
        filename=os.path.basename(safe_path),
        media_type="application/octet-stream",
    )
