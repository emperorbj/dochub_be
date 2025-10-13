import asyncio
import os
import json
import tempfile
import pandas as pd

from supabase import create_client


supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

BUCKET_NAME="docsbucket"





async def convert_excel_to_json(file):
    contents = await file.read()
    def _convert():
           #Determine file extension from original filename
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        #Use appropriate suffix
        suffix = file_ext if file_ext in ['.xlsx', '.xls'] else '.xlsx'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            
            tmp.write(contents)
            tmp_path = tmp.name
            # Try to read with appropriate engine
        try:
            if suffix == '.xlsx':
                df = pd.read_excel(tmp_path, engine='openpyxl')
            else:  # .xls
                df = pd.read_excel(tmp_path, engine='xlrd')
        except Exception as e:
            # ✅ Try alternative engine if first fails
            try:
                df = pd.read_excel(tmp_path, engine='openpyxl')
            except:
                df = pd.read_excel(tmp_path, engine='xlrd')
            # df=pd.read_excel(tmp_path)
        json_data=df.to_dict(orient="records")
            
        json_path = tmp_path.replace(suffix,".json")
        with open(json_path,"w") as f:
            json.dump(json_data,f,indent=2)
        return tmp_path,json_path
    
    # Run the blocking conversion in a thread
    tmp_path, json_path = await asyncio.to_thread(_convert)
    
    try:
        file_name = os.path.basename(json_path)
        with open(json_path, "rb") as json_file:
            supabase.storage.from_(BUCKET_NAME).upload(
                file_name,
                json_file,
                {"content-type": "application/json", "upsert": "false"}
            )
        download_url = f"{supabase_url}/storage/v1/object/public/{BUCKET_NAME}/{file_name}"
        
    except Exception as e:
        print(f"❌ Supabase upload failed: {str(e)}")
        raise
    
    finally:
        os.remove(tmp_path)
        os.remove(json_path)

    return download_url, file_name