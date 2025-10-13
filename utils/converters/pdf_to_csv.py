import asyncio
import os
import pdfplumber
import tempfile
import pandas as pd
from supabase import create_client


supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

BUCKET_NAME="docsbucket"


async def convert_pdf_to_csv(file):
    contents = await file.read()
    def _convert():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        data_frames = []
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    data_frames.append(df)
        if not data_frames:
            raise ValueError("There are no tables in the pdf")
        combined = pd.concat(data_frames, ignore_index=True)
        csv_path = tmp_path.replace(".pdf", ".csv")
        combined.to_csv(csv_path, index=False)
        return tmp_path, csv_path
    
    tmp_path, csv_path = await asyncio.to_thread(_convert)
    
    try:
        file_name = os.path.basename(csv_path)
        with open(csv_path, "rb") as csv_file:
            supabase.storage.from_(BUCKET_NAME).upload(
                file_name,
                csv_file,
                {"content-type": "text/csv", "upsert": "false"}
            )
        download_url = f"{supabase_url}/storage/v1/object/public/{BUCKET_NAME}/{file_name}"
    except Exception as e:
        print(f"❌ Supabase upload failed: {str(e)}")
        raise
    finally:
        os.remove(tmp_path)
        os.remove(csv_path)
    
    return download_url, file_name