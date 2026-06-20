import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Optional
from .pdf_parser import extract_text_from_pdf


DATE_PATTERNS = [
    r'\b(\d{1,2}/\d{1,2}/\d{4})\b',
    r'\b(\d{1,2}/\d{1,2}/\d{2})\b',
    r'\b(\d{1,2}-\d{1,2}-\d{4})\b',
    r'\b(\d{4}-\d{2}-\d{2})\b',
    r'\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b',
]

AMOUNT_PATTERN = r'[-+]?\$?[\d,]+\.\d{2}'

DATE_FORMATS = [
    '%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y',
    '%Y-%m-%d', '%b %d, %Y', '%b %d %Y', '%B %d, %Y', '%B %d %Y',
    '%b. %d, %Y', '%b. %d %Y',
]

INCOME_KEYWORDS = {'CREDIT', 'DEPOSIT', 'DIRECT DEP', 'PAYROLL', 'REFUND', 'INTEREST', 'DIVIDEND'}
SKIP_KEYWORDS = {'BEGINNING BALANCE', 'ENDING BALANCE', 'ACCOUNT NUMBER', 'ROUTING', 'PAGE', 'STATEMENT'}


def parse_date(date_str: str) -> Optional[datetime]:
    date_str = date_str.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def parse_amount(amount_str: str) -> Optional[Decimal]:
    try:
        return Decimal(amount_str.replace('$', '').replace(',', '').strip())
    except InvalidOperation:
        return None


def parse_bank_statement(file_content: bytes) -> List[Dict]:
    pages = extract_text_from_pdf(file_content)
    transactions = []

    for page_text in pages:
        for line in page_text.split('\n'):
            line = line.strip()
            if not line or any(kw in line.upper() for kw in SKIP_KEYWORDS):
                continue

            date = None
            for pattern in DATE_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    date = parse_date(match.group(1))
                    if date:
                        break

            if not date:
                continue

            amounts = re.findall(AMOUNT_PATTERN, line)
            if not amounts:
                continue

            amount = parse_amount(amounts[-1])
            if amount is None:
                continue

            line_upper = line.upper()
            is_income = any(kw in line_upper for kw in INCOME_KEYWORDS)
            transaction_type = "income" if is_income else "expense"
            amount = abs(amount)

            description = re.sub(AMOUNT_PATTERN, '', line)
            for pattern in DATE_PATTERNS:
                description = re.sub(pattern, '', description, flags=re.IGNORECASE)
            description = ' '.join(description.split()).strip()

            if not description or amount == 0:
                continue

            transactions.append({
                "date": date,
                "amount": amount,
                "description": description[:500],
                "payee": description[:255],
                "source": "bank",
                "transaction_type": transaction_type,
                "original_text": line,
            })

    return transactions
