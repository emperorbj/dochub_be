import asyncio
import os
import pdfplumber
import cloudinary
import cloudinary.uploader
import tempfile
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from supabase import create_client


supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

BUCKET_NAME="docsbucket"



async def convert_docx_to_pdf(file):
    contents = await file.read()
    
    def _convert():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        doc = Document(tmp_path)
        pdf_path = tmp_path.replace(".docx", ".pdf")
        
        # Use SimpleDocTemplate for better formatting
        pdf_doc = SimpleDocTemplate(pdf_path, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                #Use Paragraph for proper text wrapping
                p = Paragraph(text, styles['Normal'])
                story.append(p)
                story.append(Spacer(1, 0.2 * inch))
        
        #Build the PDF
        pdf_doc.build(story)
        
        return tmp_path, pdf_path
    
    tmp_path, pdf_path = await asyncio.to_thread(_convert)
    
    try:
        with open(pdf_path, "rb") as pdf_file:
            file_name = os.path.basename(pdf_path)
            
            # Upload file to Supabase Storage bucket
            response = supabase.storage.from_(BUCKET_NAME).upload(
                path=file_name,
                file=pdf_file,
                file_options={
                    "content-type": "application/pdf",
                    "cache-control": "3600",
                    "upsert": "false"
                }
            )
        
        # Generate public download URL following Supabase format
        download_url = f"{supabase_url}/storage/v1/object/public/{BUCKET_NAME}/{file_name}"
        
        print(f"File uploaded successfully: {download_url}")
        
    except Exception as e:
        print(f"❌ Supabase upload failed: {str(e)}")
        raise
    
    finally:
        # Cleanup temporary files
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
    return download_url,file_name