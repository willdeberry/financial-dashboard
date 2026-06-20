from fastapi import APIRouter, File, UploadFile
from ..parsers.pdf_parser import extract_text_from_pdf

router = APIRouter()


@router.post("/debug/parse-pdf")
async def debug_parse_pdf(file: UploadFile = File(...)):
    content = await file.read()
    pages = extract_text_from_pdf(content)
    return {
        "page_count": len(pages),
        "pages": [{"page": i + 1, "text": text} for i, text in enumerate(pages)],
    }
