from .docx_to_pdf import convert_docx_to_pdf
from .excel_to_json import convert_excel_to_json
from .pdf_to_csv import convert_pdf_to_csv
from .pdf_to_docx import convert_pdf_to_docx
from .pdf_to_excel import convert_pdf_to_excel
from .image_to_pdf import convert_image_to_pdf
from .compress_pdf import convert_compress_pdf
from .extract_pdf_text import convert_extract_pdf_text
from .markdown_to_pdf import convert_markdown_to_pdf
from .pdf_to_powerpoint import convert_pdf_to_powerpoint

conversion_map = {
    "docx_to_pdf":convert_docx_to_pdf,
    "excel_to_json":convert_excel_to_json,
    "pdf_to_csv":convert_pdf_to_csv,
    "pdf_to_docx":convert_pdf_to_docx,
    "pdf_to_excel":convert_pdf_to_excel,
    "image_to_pdf":convert_image_to_pdf,
    "compress_pdf":convert_compress_pdf,
    "extract_pdf_text":convert_extract_pdf_text,
    "markdown_to_pdf":convert_markdown_to_pdf,
    "pdf_to_powerpoint":convert_pdf_to_powerpoint
}


async def convert_file(file,conversion_type:str):
    if conversion_type not in conversion_map:
        raise ValueError(f"Unsupported file type for : {conversion_type}")
    
    return await conversion_map[conversion_type](file)