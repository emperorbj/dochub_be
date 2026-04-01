import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from bson import ObjectId
from pymongo import ReturnDocument
from supabase import create_client

from config import SUPABASE_BUCKET_NAME, get_jobs_collection
from utils.converters import is_supported_conversion
from utils.upload_stream import stream_upload_to_temp

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
DEFAULT_MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "50"))


def _supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def max_upload_bytes() -> int:
    return DEFAULT_MAX_UPLOAD_MB * 1024 * 1024


def job_to_dict(doc: Optional[dict]) -> Optional[dict]:
    if not doc:
        return None
    out = dict(doc)
    out["_id"] = str(out["_id"])
    out["user_id"] = str(out["user_id"])
    fr = out.get("file_record")
    if fr and isinstance(fr, dict):
        fr = dict(fr)
        if fr.get("_id") is not None:
            fr["_id"] = str(fr["_id"])
        if fr.get("user_id") is not None:
            fr["user_id"] = str(fr["user_id"])
        out["file_record"] = fr
    return out


async def enqueue_conversion_job(
    user: dict,
    upload,
    conversion_type: str,
) -> dict:
    if not is_supported_conversion(conversion_type):
        raise ValueError(f"Unsupported conversion_type: {conversion_type}")

    user_id = str(user["_id"])
    max_bytes = max_upload_bytes()
    content_type = upload.content_type or "application/octet-stream"
    local_path, file_size = await stream_upload_to_temp(upload, max_bytes)

    ext = Path(upload.filename or "file").suffix[:32]
    if not ext:
        ext = ""
    remote_key = f"inputs/{user_id}/{uuid.uuid4().hex}{ext}"

    try:
        with open(local_path, "rb") as f:
            _supabase().storage.from_(SUPABASE_BUCKET_NAME).upload(
                remote_key,
                f,
                {
                    "content-type": content_type,
                    "upsert": "false",
                },
            )
    finally:
        try:
            os.remove(local_path)
        except OSError:
            pass

    collection = get_jobs_collection()
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": ObjectId(user_id),
        "status": "pending",
        "conversion_type": conversion_type,
        "original_filename": upload.filename,
        "content_type": content_type,
        "input_storage_path": remote_key,
        "input_size": file_size,
        "output_url": None,
        "converted_filename": None,
        "file_record": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    result = await collection.insert_one(doc)
    saved = await collection.find_one({"_id": result.inserted_id})
    return job_to_dict(saved)  # type: ignore


async def get_job_for_user(job_id: str, user_id: str) -> Optional[dict]:
    if not ObjectId.is_valid(job_id):
        return None
    collection = get_jobs_collection()
    doc = await collection.find_one(
        {"_id": ObjectId(job_id), "user_id": ObjectId(user_id)}
    )
    return job_to_dict(doc)


async def list_jobs_for_user(user_id: str, limit: int = 50) -> List[dict]:
    collection = get_jobs_collection()
    cursor = (
        collection.find({"user_id": ObjectId(user_id)})
        .sort("created_at", -1)
        .limit(limit)
    )
    out: List[dict] = []
    async for doc in cursor:
        jd = job_to_dict(doc)
        if jd:
            out.append(jd)
    return out


async def claim_next_pending_job() -> Optional[dict]:
    collection = get_jobs_collection()
    now = datetime.now(timezone.utc)
    doc = await collection.find_one_and_update(
        {"status": "pending"},
        {"$set": {"status": "processing", "updated_at": now}},
        sort=[("created_at", 1)],
        return_document=ReturnDocument.AFTER,
    )
    return doc


async def mark_job_failed(job_id: ObjectId, error_message: str) -> None:
    collection = get_jobs_collection()
    now = datetime.now(timezone.utc)
    await collection.update_one(
        {"_id": job_id},
        {
            "$set": {
                "status": "failed",
                "error": error_message[:4000],
                "updated_at": now,
            }
        },
    )


async def mark_job_completed(
    job_id: ObjectId,
    output_url: str,
    converted_filename: str,
    file_record: dict,
) -> None:
    collection = get_jobs_collection()
    now = datetime.now(timezone.utc)
    await collection.update_one(
        {"_id": job_id},
        {
            "$set": {
                "status": "done",
                "output_url": output_url,
                "converted_filename": converted_filename,
                "file_record": file_record,
                "error": None,
                "updated_at": now,
            }
        },
    )


def download_input_file(storage_path: str) -> bytes:
    return _supabase().storage.from_(SUPABASE_BUCKET_NAME).download(storage_path)


async def remove_input_from_storage(storage_path: str) -> None:
    if os.getenv("DELETE_INPUT_AFTER_JOB", "true").lower() not in (
        "1",
        "true",
        "yes",
    ):
        return
    try:
        _supabase().storage.from_(SUPABASE_BUCKET_NAME).remove([storage_path])
    except Exception:
        pass
