import importlib
from typing import Any, Callable, Awaitable

# Lazy-loaded converters: (module_path, function_name)
CONVERSION_MODULES: dict[str, tuple[str, str]] = {
    "docx_to_pdf": ("utils.converters.docx_to_pdf", "convert_docx_to_pdf"),
    "excel_to_json": ("utils.converters.excel_to_json", "convert_excel_to_json"),
    "pdf_to_csv": ("utils.converters.pdf_to_csv", "convert_pdf_to_csv"),
    "pdf_to_docx": ("utils.converters.pdf_to_docx", "convert_pdf_to_docx"),
    "pdf_to_excel": ("utils.converters.pdf_to_excel", "convert_pdf_to_excel"),
    "image_to_pdf": ("utils.converters.image_to_pdf", "convert_image_to_pdf"),
    "compress_pdf": ("utils.converters.compress_pdf", "convert_compress_pdf"),
    "extract_pdf_text": ("utils.converters.extract_pdf_text", "convert_extract_pdf_text"),
    "markdown_to_pdf": ("utils.converters.markdown_to_pdf", "convert_markdown_to_pdf"),
    "pdf_to_powerpoint": ("utils.converters.pdf_to_powerpoint", "convert_pdf_to_powerpoint"),
    "extract_zip": ("utils.converters.extract_zip", "convert_extract_zip"),
}


def is_supported_conversion(conversion_type: str) -> bool:
    return conversion_type in CONVERSION_MODULES


def supported_conversion_types() -> frozenset[str]:
    return frozenset(CONVERSION_MODULES.keys())


async def convert_file(file: Any, conversion_type: str):
    if conversion_type not in CONVERSION_MODULES:
        raise ValueError(f"Unsupported file type for : {conversion_type}")
    module_path, fn_name = CONVERSION_MODULES[conversion_type]
    mod = importlib.import_module(module_path)
    fn: Callable[..., Awaitable[Any]] = getattr(mod, fn_name)
    return await fn(file)
