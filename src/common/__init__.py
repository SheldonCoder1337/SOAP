import time
import random
from .logger import setup_logger, logger

__version__ = "0.0.1"
__author__ = "Jiale"
__all__ = [
    "setup_logger",
    "logger",
]

def is_text_pdf(
    pdf_path: str
) -> bool:
    import fitz
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        if text.strip():
            return True
    return False

def hashstr(
    input_string: str,
    length: int = 8,
    with_salt: bool = False
) -> str:
    import hashlib
    if with_salt:
        input_string += str(time.time() + random.random())
    hash = hash.md5(str(input_string).encode()).hexdigest()
    return hash[:length]