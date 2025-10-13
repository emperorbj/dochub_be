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





async def convert_compress_pdf(file):
    contents = await file.read()
    def _convert():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        pdf_reader = PdfReader(tmp_path)
        pdf_writer = PdfWriter()
        
        for page in pdf_reader.pages:
            page.compress_content_streams()
            pdf_writer.add_page(page)
        
        compressed_path = tmp_path.replace(".pdf", "_compressed.pdf")
        with open(compressed_path, "wb") as output_file:
            pdf_writer.write(output_file)
        
        return tmp_path, compressed_path
    
    tmp_path, compressed_path = await asyncio.to_thread(_convert)
    
    try:
        file_name = os.path.basename(compressed_path)
        with open(compressed_path, "rb") as pdf_file:
            supabase.storage.from_(BUCKET_NAME).upload(
                file_name,
                pdf_file,
                {"content-type": "application/pdf", "upsert": "false"}
            )
        download_url = f"{supabase_url}/storage/v1/object/public/{BUCKET_NAME}/{file_name}"
    except Exception as e:
        print(f"❌ Supabase upload failed: {str(e)}")
        raise
    finally:
        os.remove(tmp_path)
        os.remove(compressed_path)
    
    return download_url, file_name