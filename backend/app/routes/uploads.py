from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..categorizer import categorize_transaction
from ..parsers.bank_parser import parse_bank_statement
from ..parsers.credit_card_parser import parse_credit_card_statement
from ..parsers.payroll_parser import parse_payroll_stub
from ..parsers.capital_one_csv_parser import parse_capital_one_csv
from ..utils import logger

router = APIRouter()

PDF_PARSERS = {
    "bank": parse_bank_statement,
    "credit_card": parse_credit_card_statement,
    "payroll": parse_payroll_stub,
}

CSV_PARSERS = {
    "bank": parse_capital_one_csv,
}


@router.post("/upload", response_model=schemas.UploadHistoryResponse)
async def upload_file(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    db: Session = Depends(get_db),
):
    if source_type not in PDF_PARSERS:
        raise HTTPException(status_code=400, detail="source_type must be bank, credit_card, or payroll")

    fname = file.filename.lower()
    if fname.endswith('.csv'):
        if source_type not in CSV_PARSERS:
            raise HTTPException(status_code=400, detail=f"CSV upload not supported for source type '{source_type}'")
    elif not fname.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF and CSV files are supported")

    upload = models.UploadHistory(filename=file.filename, source_type=source_type, status="pending")
    db.add(upload)
    db.commit()
    db.refresh(upload)

    try:
        content = await file.read()
        if fname.endswith('.csv'):
            raw_transactions = CSV_PARSERS[source_type](content)
        else:
            raw_transactions = PDF_PARSERS[source_type](content)

        # Cache category name→id for parsers that pre-classify (e.g. Amex)
        category_cache: dict = {}

        count = 0
        for tx in raw_transactions:
            amex_category = tx.get("amex_category")
            if amex_category:
                if amex_category not in category_cache:
                    cat = db.query(models.Category).filter(models.Category.name == amex_category).first()
                    category_cache[amex_category] = cat.id if cat else None
                category_id = category_cache[amex_category]
            else:
                category_id = categorize_transaction(db, tx.get("payee"), tx.get("description"))

            db.add(models.Transaction(
                date=tx["date"],
                amount=tx["amount"],
                description=tx.get("description"),
                payee=tx.get("payee"),
                source=tx["source"],
                transaction_type=tx["transaction_type"],
                original_text=tx.get("original_text"),
                category_id=category_id,
            ))
            count += 1

        db.commit()
        upload.status = "processed"
        upload.transaction_count = count
        db.commit()
        db.refresh(upload)

        logger.info(f"Processed {count} transactions from {file.filename}")
        return upload

    except Exception as e:
        logger.error(f"Error processing {file.filename}: {e}")
        upload.status = "failed"
        upload.error_message = str(e)
        db.commit()
        db.refresh(upload)
        raise HTTPException(status_code=500, detail=f"Failed to process file: {e}")


@router.get("/uploads", response_model=List[schemas.UploadHistoryResponse])
def list_uploads(db: Session = Depends(get_db)):
    return db.query(models.UploadHistory).order_by(models.UploadHistory.upload_date.desc()).all()
