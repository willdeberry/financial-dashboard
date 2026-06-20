import io
from typing import List
import pdfplumber


def extract_text_from_pdf(file_content: bytes) -> List[str]:
    pages = []
    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return pages
