import asyncio
import os
import tempfile
import pdfplumber
from PIL import Image
from pdf2image import convert_from_path
import markdown
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from PyPDF2 import PdfReader, PdfWriter
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from supabase import create_client

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

BUCKET_NAME = "docsbucket"


async def convert_extract_pdf_text(file):
    contents = await file.read()
    def _convert():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        extracted_text = ""
        with pdfplumber.open(tmp_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                extracted_text += f"\n--- Page {page_num} ---\n{text}\n"
        
        txt_path = tmp_path.replace(".pdf", ".txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(extracted_text)
        
        return tmp_path, txt_path
    
    tmp_path, txt_path = await asyncio.to_thread(_convert)
    
    try:
        file_name = os.path.basename(txt_path)
        with open(txt_path, "rb") as txt_file:
            supabase.storage.from_(BUCKET_NAME).upload(
                file_name,
                txt_file,
                {"content-type": "text/plain", "upsert": "false"}
            )
        download_url = f"{supabase_url}/storage/v1/object/public/{BUCKET_NAME}/{file_name}"
    except Exception as e:
        print(f"❌ Supabase upload failed: {str(e)}")
        raise
    finally:
        os.remove(tmp_path)
        os.remove(txt_path)
    
    return download_url, file_name