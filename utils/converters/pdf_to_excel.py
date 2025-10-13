import asyncio
import os
import pdfplumber
import cloudinary
import cloudinary.uploader
import tempfile
import pandas as pd

cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

async def convert_pdf_to_excel(file):
    contents= await file.read()
    def _convert():
        with tempfile.NamedTemporaryFile(delete=False,suffix=".pdf") as tmp:
            
            tmp.write(contents)
            tmp_path=tmp.name
        data_frames = []
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    df = pd.DataFrame(table[1:],columns=table[0])
                    data_frames.append(df)
        if not data_frames:
            raise ValueError("There are no tables in the pdf")
        combined = pd.concat(data_frames,ignore_index=True)
        excel_path = tmp_path.replace(".pdf",".xlsx")
        combined.to_excel(excel_path,index=False)
        
        return tmp_path, excel_path
    
    # Run the blocking conversion in a thread
    tmp_path, excel_path = await asyncio.to_thread(_convert)
    
    upload_result = cloudinary.uploader.upload(excel_path,resource_type="raw")
    os.remove(tmp_path)
    os.remove(excel_path)
    
    return upload_result["secure_url"],os.path.basename(excel_path)