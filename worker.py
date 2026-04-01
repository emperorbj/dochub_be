import asyncio
import logging
import os
import tempfile
import traceback
from pathlib import Path

from config import close_db, init_db
from services.file_service import save_file_record
from services.job_service import (
    claim_next_pending_job,
    download_input_file,
    mark_job_completed,
    mark_job_failed,
    remove_input_from_storage,
)
from utils.converters import convert_file
from utils.path_upload_file import PathBackedUploadFile, safe_remove

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("worker")

POLL = int(os.getenv("WORKER_POLL_SECONDS", "3"))


async def process_one(job: dict) -> None:
    job_id = job["_id"]
    tmp_in = None
    try:
        raw = await asyncio.to_thread(download_input_file, job["input_storage_path"])
        suffix = Path(job.get("original_filename") or "file").suffix or ".bin"
        fd, tmp_in = tempfile.mkstemp(suffix=suffix)
        try:
            os.write(fd, raw)
        finally:
            os.close(fd)

        wrapped = PathBackedUploadFile(
            tmp_in,
            job.get("original_filename") or "file",
            job.get("content_type"),
        )
        converted_url, new_filename = await convert_file(
            wrapped, job["conversion_type"]
        )
        record = await save_file_record(
            user_id=str(job["user_id"]),
            original_filename=job.get("original_filename") or "file",
            converted_filename=new_filename,
            file_type=job.get("content_type") or "application/octet-stream",
            conversion_type=job["conversion_type"],
            cloud_url=converted_url,
            file_size=int(job.get("input_size") or 0),
        )
        await mark_job_completed(job_id, converted_url, new_filename, record)
        await remove_input_from_storage(job["input_storage_path"])
    except Exception as e:
        log.error("Job %s failed: %s\n%s", job_id, e, traceback.format_exc())
        await mark_job_failed(job_id, f"{type(e).__name__}: {e}")
    finally:
        if tmp_in:
            safe_remove(tmp_in)


async def main() -> None:
    await init_db()
    log.info("Worker started (poll %ss)", POLL)
    try:
        while True:
            job = await claim_next_pending_job()
            if not job:
                await asyncio.sleep(POLL)
                continue
            log.info("Processing job %s (%s)", job["_id"], job.get("conversion_type"))
            await process_one(job)
    finally:
        await close_db()
        log.info("Worker stopped")


if __name__ == "__main__":
    asyncio.run(main())
