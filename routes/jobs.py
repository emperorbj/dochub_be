from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from services.job_service import (
    enqueue_conversion_job,
    get_job_for_user,
    list_jobs_for_user,
)
from utils.auth import get_current_user

jobs_router = APIRouter()


@jobs_router.post("/api/convert/jobs")
async def create_conversion_job(
    file: UploadFile = File(...),
    conversion_type: str = Form(
        ...,
        description="e.g. pdf_to_excel, excel_to_json, pdf_to_docx, docx_to_pdf",
    ),
    current_user: dict = Depends(get_current_user),
):
    """
    Queue a file conversion. Poll GET /api/jobs/{job_id} until status is done or failed.
    """
    try:
        job = await enqueue_conversion_job(current_user, file, conversion_type)
        return {
            "success": True,
            "message": "Conversion queued. Poll GET /api/jobs/{job_id} for status.",
            "job": job,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@jobs_router.get("/api/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: dict = Depends(get_current_user),
):
    job = await get_job_for_user(job_id, str(current_user["_id"]))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, "job": job}


@jobs_router.get("/api/jobs")
async def list_user_jobs(
    current_user: dict = Depends(get_current_user),
):
    jobs = await list_jobs_for_user(str(current_user["_id"]))
    return {"success": True, "count": len(jobs), "jobs": jobs}
