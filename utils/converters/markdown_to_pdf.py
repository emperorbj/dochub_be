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




async def convert_markdown_to_pdf(file):
    contents = await file.read()
    def _convert():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md", mode='w', encoding='utf-8') as tmp:
            tmp.write(contents.decode('utf-8'))
            tmp_path = tmp.name
        
        # Read markdown
        with open(tmp_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # Convert markdown to HTML
        html_content = markdown.markdown(md_content)
        
        # Create PDF from HTML content
        pdf_path = tmp_path.replace(".md", ".pdf")
        pdf_doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Parse HTML and add to PDF
        paragraphs = html_content.split('<p>')
        for para in paragraphs:
            para = para.replace('</p>', '').strip()
            if para:
                p = Paragraph(para, styles['Normal'])
                story.append(p)
                story.append(Spacer(1, 0.2 * inch))
        
        pdf_doc.build(story)
        
        return tmp_path, pdf_path
    
    tmp_path, pdf_path = await asyncio.to_thread(_convert)
    
    try:
        file_name = os.path.basename(pdf_path)
        with open(pdf_path, "rb") as pdf_file:
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
        os.remove(pdf_path)
    
    return download_url, file_name