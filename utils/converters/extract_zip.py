import asyncio
import os
import tempfile
import zipfile
import json
import shutil
from supabase import create_client

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

BUCKET_NAME = "docsbucket"

async def convert_extract_zip(file):
    contents = await file.read()
    def _convert():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Create extraction directory
        extract_dir = tempfile.mkdtemp()
        
        # Extract zip file
        with zipfile.ZipFile(tmp_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Create manifest of extracted files
        file_manifest = {
            "total_files": 0,
            "files": [],
            "folder_structure": {}
        }
        
        for root, dirs, files in os.walk(extract_dir):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(file_path, extract_dir)
                file_size = os.path.getsize(file_path)
                
                file_manifest["files"].append({
                    "name": file_name,
                    "path": relative_path,
                    "size": file_size
                })
                file_manifest["total_files"] += 1
        
        # Create manifest JSON
        manifest_path = os.path.join(extract_dir, "manifest.json")
        with open(manifest_path, "w") as f:
            json.dump(file_manifest, f, indent=2)
        
        # Create zip of extracted contents
        output_zip = tmp_path.replace(".zip", "_extracted.zip")
        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(extract_dir):
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    arcname = os.path.relpath(file_path, extract_dir)
                    zipf.write(file_path, arcname)
        
        return tmp_path, output_zip, extract_dir
    
    tmp_path, output_zip, extract_dir = await asyncio.to_thread(_convert)
    
    try:
        file_name = os.path.basename(output_zip)
        with open(output_zip, "rb") as zip_file:
            supabase.storage.from_(BUCKET_NAME).upload(
                file_name,
                zip_file,
                {"content-type": "application/zip", "upsert": "false"}
            )
        download_url = f"{supabase_url}/storage/v1/object/public/{BUCKET_NAME}/{file_name}"
    except Exception as e:
        print(f"❌ Supabase upload failed: {str(e)}")
        raise
    finally:
        os.remove(tmp_path)
        os.remove(output_zip)
        # Clean up extraction directory
        if os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
    
    return download_url, file_name