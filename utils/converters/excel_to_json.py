import asyncio
import os
import json
import cloudinary
import cloudinary.uploader
import tempfile
import pandas as pd


cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


async def convert_excel_to_json(file):
    contents = await file.read()
    def _convert():
           # ✅ Determine file extension from original filename
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        # ✅ Use appropriate suffix
        suffix = file_ext if file_ext in ['.xlsx', '.xls'] else '.xlsx'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            
            tmp.write(contents)
            tmp_path = tmp.name
             # ✅ Try to read with appropriate engine
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
    
    upload_results = cloudinary.uploader.upload(json_path,resource_type="raw")
    os.remove(tmp_path)
    os.remove(json_path)
    
    return upload_results["secure_url"],os.path.basename(json_path)