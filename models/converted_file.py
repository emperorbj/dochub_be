from pydantic import BaseModel,Field
from typing import Optional
from datetime import datetime,timezone
from bson import ObjectId

class PyObjectId(str):
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
        
    @classmethod
    def validate(cls,v,*args,**kwargs):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid Objectid")
        return str(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_name, **kwargs):
        return {"type": "string"}
    
class ConvertedFile(BaseModel):
    id: PyObjectId = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    user_id: PyObjectId = Field(..., description="ID of the user who owns the file")
    original_filename: str = Field(..., description="Original file name")
    converted_filename: str = Field(..., description="Converted file name")
    file_type: str = Field(..., description="Original file type, e.g. PDF")
    conversion_type: str = Field(..., description="e.g. pdf_to_csv")
    file_size: Optional[int] = Field(default=None, description="Size in bytes")
    cloud_url: Optional[str] = Field(default=None, description="Cloud storage URL")
    status: str = Field(default="completed")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId:str}
        
