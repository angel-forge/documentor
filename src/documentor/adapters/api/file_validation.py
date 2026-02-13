from pathlib import PurePosixPath

from fastapi import HTTPException, UploadFile

ALLOWED_EXTENSIONS = {".txt", ".md", ".html", ".rst", ".pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


async def validate_upload_file(file: UploadFile) -> bytes:
    """Validate an uploaded file and return its content bytes.

    Checks extension allowlist, file size, non-emptiness,
    and content validity (magic bytes for PDF, UTF-8 for text).
    Raises HTTPException(400) on any validation failure.
    """
    filename = file.filename or ""
    ext = PurePosixPath(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content = await file.read()

    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB",
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    if ext == ".pdf":
        if not content[:4] == b"%PDF":
            raise HTTPException(
                status_code=400, detail="File does not appear to be a valid PDF"
            )
    else:
        try:
            content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=400,
                detail="File is not valid UTF-8 text",
            )

    return content
