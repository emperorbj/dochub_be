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

async def convert_pdf_to_csv(file):
    with tempfile.NamedTemporaryFile(delete=False,suffix=".pdf") as tmp:
        contents= await file.read()
        tmp.write(contents)
        tmp_path=tmp.name