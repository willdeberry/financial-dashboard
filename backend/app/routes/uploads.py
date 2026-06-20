from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..categorizer import categorize_transaction
from ..parsers.bank_parser import parse_bank_statement
from ..parsers.credit_card_parser import parse_credit_card_statement
from ..parsers.payroll_parser import parse_payroll_stub
from ..utils import logger

router = APIRouter()

PARSERS = {
    "bank": parse_bank_statement,
    "credit_card": parse_credit_card_statement,
    "payroll": parse_payroll_stub,
}


@router.post("/upload", response_model=schemas.UploadHistoryResponse)
async def upload_file(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    db: Session = Depends(get_db),
):
    if source_type not in PARSERS:
        raise HTTPException(status_code=400, detail="source_type must be bank, credit_card, or payroll")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    upload = models.UploadHistory(filename=file.filename, source_type=source_type, status="pending")
    db.add(upload)
    db.commit()
    db.refresh(upload)

    try:
        content = await file.read()
        raw_transactions = PARSERS[source_type](content)

        count = 0
        for tx in raw_transactions:
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
