import os
import pdfplumber
import tempfile
import asyncio
from docx import Document
from supabase import create_client


supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

BUCKET_NAME="docsbucket"

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
    
    
    try:
        file_name = os.path.basename(docx_path)
        with open(docx_path, "rb") as docx_file:
            supabase.storage.from_(BUCKET_NAME).upload(
                file_name,
                docx_file,
                {"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "upsert": "false"}
            )
        download_url = f"{supabase_url}/storage/v1/object/public/{BUCKET_NAME}/{file_name}"
        
    except Exception as e:
        print(f"❌ Supabase upload failed: {str(e)}")
        raise
    
    finally:
        os.remove(tmp_path)
        os.remove(docx_path)

    return download_url, file_name