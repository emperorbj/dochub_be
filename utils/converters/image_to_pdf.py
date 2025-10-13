import asyncio
import os
import tempfile
from PIL import Image
from supabase import create_client

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

BUCKET_NAME = "docsbucket"




async def convert_image_to_pdf(file):
    contents = await file.read()
    def _convert():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        image = Image.open(tmp_path)
        
        # Convert RGBA to RGB if necessary
        if image.mode in ('RGBA', 'LA', 'P'):
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = rgb_image
        
        pdf_path = tmp_path.replace(os.path.splitext(tmp_path)[1], ".pdf")
        image.save(pdf_path, "PDF")
        
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
