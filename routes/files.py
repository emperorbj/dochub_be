from bson import ObjectId
import cloudinary
from fastapi import UploadFile,File,HTTPException,Depends,APIRouter,Form
from utils.auth import get_current_user
from services.file_service import delete_file, get_file_by_id, get_user_files,save_file_record
from utils.converters import convert_file

files_router = APIRouter()

@files_router.post("/api/convert")
async def convert_documents(
    file:UploadFile=File(...),
    conversion_type:str = Form("e.g. pdf_to_excel, excel_to_json, pdf_to_docx, docx_to_pdf"),
    current_user:dict = Depends(get_current_user)
    ):
    """
    Upload a file and convert it based on the conversion_type.
    Supported types: pdf_to_excel, excel_to_json, pdf_to_docx, docx_to_pdf
    """
    
    try:
        converted_url,new_filename = await convert_file(file,conversion_type)
        
        record = await save_file_record(
            user_id=current_user["_id"],
            original_filename=file.filename,
            converted_filename=new_filename,
            file_type=file.content_type,
            conversion_type=conversion_type,
            cloud_url=converted_url
        )
        return {
            "success":True,
            "message": f"File converted successfully to {conversion_type}",
            "file":record
        }
        
    except ValueError as e:
        # For known conversion errors
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
        

@files_router.get("/api/files")
async def get_converted_files(current_user:dict = Depends(get_current_user)):
    """
    Fetch all converted files belonging to the logged-in user
    """
    files = await get_user_files(current_user["_id"])
    return {
        "success":True,
        "count":len(files),
        "files":files
    }
    
    



@files_router.delete("/api/files/{file_id}")
async def delete_converted_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a converted file record and remove it from Cloudinary storage.
    """
    # Validate ObjectId
    if not ObjectId.is_valid(file_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid file ID format"
        )

    # Check if file exists and belongs to the user
    file_record = await get_file_by_id(file_id)
    if not file_record or file_record["user_id"] != current_user["_id"]:
        raise HTTPException(
            status_code=404,
            detail="File not found or not owned by user"
        )

    # Extract public_id from Cloudinary URL
    file_url = file_record["cloud_url"]
    public_id = file_url.split("/")[-1].split(".")[0]

    # Delete from Cloudinary
    try:
        cloudinary.uploader.destroy(public_id, resource_type="raw")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete file from Cloudinary: {str(e)}"
        )

    # Delete from DB
    deleted = await delete_file(file_id, current_user["_id"])
    if not deleted:
        raise HTTPException(
            status_code=500,
            detail="File deletion failed from database"
        )

    return {
        "success": True,
        "message": "File deleted successfully from Cloudinary and database",
        "file_id": file_id
    }