import os
import tempfile


async def stream_upload_to_temp(upload, max_bytes: int) -> tuple[str, int]:
    """
    Write an UploadFile to a temp file without holding the full body in memory at once.
    Returns (path, total_bytes).
    """
    fd, path = tempfile.mkstemp(suffix=".upload")
    os.close(fd)
    total = 0
    try:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(
                    f"File exceeds maximum size of {max_bytes // (1024 * 1024)} MB"
                )
            with open(path, "ab") as out:
                out.write(chunk)
        return path, total
    except Exception:
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass
        raise
