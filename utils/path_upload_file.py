import asyncio
import os
from typing import Optional


class PathBackedUploadFile:
    """
    Minimal UploadFile-like object for converter functions that call await file.read()
    and use file.filename / file.content_type.
    """

    __slots__ = ("_path", "filename", "content_type")

    def __init__(self, path: str, filename: str, content_type: Optional[str]):
        self._path = path
        self.filename = filename
        self.content_type = content_type or "application/octet-stream"

    async def read(self) -> bytes:
        return await asyncio.to_thread(_read_bytes, self._path)


def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as f:
        return f.read()


def safe_remove(path: str) -> None:
    if path and os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass
