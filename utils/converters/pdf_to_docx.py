import os
import pdfplumber
import cloudinary
import cloudinary.uploader
import tempfile
import asyncio
from docx import Document

cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

async def convert_pdf_to_docx(file):
    contents = await file.read()
    
    def _convert():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
            
        doc = Document()
            
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    doc.add_paragraph(text)
                    doc.add_page_break()
                
        docx_path = tmp_path.replace(".pdf",".docx")
        doc.save(docx_path)
        
        return tmp_path,docx_path
    
    tmp_path,docx_path = await asyncio.to_thread(_convert)
    upload_result = cloudinary.uploader.upload(docx_path,resource_type="raw")
    os.remove(tmp_path)
    os.remove(docx_path)
    
    return upload_result["secure_url"],os.path.basename(docx_path)