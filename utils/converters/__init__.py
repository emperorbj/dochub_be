import asyncio
from .docx_to_pdf import convert_docx_to_pdf
from .excel_to_json import convert_excel_to_json
from .pdf_to_csv import convert_pdf_to_csv
from .pdf_to_docx import convert_pdf_to_docx
from .pdf_to_excel import convert_pdf_to_excel


conversion_map = {
    "docx_to_pdf":convert_docx_to_pdf,
    "excel_to_json":convert_excel_to_json,
    "pdf_to_csv":convert_pdf_to_csv,
    "pdf_to_docx":convert_pdf_to_docx,
    "pdf_to_excel":convert_pdf_to_excel
}


async def convert_file(file,conversion_type:str):
    if conversion_type not in conversion_map:
        raise ValueError(f"Unsupported file type for : {conversion_type}")
    
    return await conversion_map[conversion_type](file)