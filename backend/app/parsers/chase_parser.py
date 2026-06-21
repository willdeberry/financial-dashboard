import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Optional
from .pdf_parser import extract_text_from_pdf


CLOSING_DATE_RE = re.compile(
    r'(?:Opening/Closing Date\s+[\d/]+\s*-\s*|Statement Date[:\s]+)(\d{1,2}/\d{1,2}/\d{2,4})',
    re.IGNORECASE,
)

SECTION_RE = re.compile(
    r'^(PURCHASE|PAYMENT|CREDIT|FEES?|CASH ADVANCES?|BALANCE TRANSFERS?)S?$',
    re.IGNORECASE,
)

TXN_RE = re.compile(r'^(\d{1,2}/\d{1,2})\s+(.+?)\s+([\d,]+\.\d{2})$')

INCOME_SECTIONS = {'PAYMENT', 'CREDIT', 'REFUND', 'ADJUSTMENT'}

SKIP_LINE_PREFIXES = {'ORDER NUMBER', 'DATE OF', 'MERCHANT NAME', '$ AMOUNT', 'TRANSACTION'}

END_MARKERS = {'INTEREST CHARGES', 'IINNTTEERREESSTT', 'YEAR-TO-DATE', 'TOTALS YEAR', '2021 TOTALS', '2022 TOTALS', '2023 TOTALS', '2024 TOTALS', '2025 TOTALS', '2026 TOTALS'}


def _infer_year(month: int, day: int, closing_date: date) -> int:
    for year in [closing_date.year, closing_date.year - 1]:
        try:
            d = date(year, month, day)
            if d <= closing_date:
                return year
        except ValueError:
            continue
    return closing_date.year


def parse_chase_statement(file_content: bytes) -> List[Dict]:
    pages = extract_text_from_pdf(file_content)
    full_text = '\n'.join(pages)

    # Find closing date for year inference
    closing_date = None
    m = CLOSING_DATE_RE.search(full_text)
    if m:
        for fmt in ['%m/%d/%y', '%m/%d/%Y']:
            try:
                closing_date = datetime.strptime(m.group(1), fmt).date()
                break
            except ValueError:
                continue
    if not closing_date:
        closing_date = date.today()

    transactions = []
    in_activity = False
    current_section = 'PURCHASE'

    for line in full_text.split('\n'):
        stripped = line.strip()
        upper = stripped.upper()

        # Detect start of account activity section
        # Chase headers are often rendered with doubled characters in pdfplumber
        if 'ACCOUNT ACTIVITY' in upper or 'AACCCCOOUUNNTT AACCTTIIVVIITTYY' in upper:
            in_activity = True
            continue

        if not in_activity:
            continue

        # End of transaction section
        if any(marker in upper for marker in END_MARKERS):
            in_activity = False
            continue

        if not stripped:
            continue

        # Section header (PURCHASE, PAYMENT, CREDIT, etc.)
        sm = SECTION_RE.match(stripped)
        if sm:
            current_section = sm.group(1).upper()
            continue

        # Skip non-transaction lines
        if any(upper.startswith(prefix) for prefix in SKIP_LINE_PREFIXES):
            continue

        # Match transaction line: MM/DD  description  amount
        m = TXN_RE.match(stripped)
        if not m:
            continue

        date_str, description, amount_str = m.group(1), m.group(2).strip(), m.group(3)

        try:
            month, day = map(int, date_str.split('/'))
            year = _infer_year(month, day, closing_date)
            txn_date = datetime(year, month, day)
        except (ValueError, IndexError):
            continue

        try:
            amount = Decimal(amount_str.replace(',', ''))
        except InvalidOperation:
            continue

        if amount == 0:
            continue

        txn_type = 'income' if current_section in INCOME_SECTIONS else 'expense'

        transactions.append({
            'date': txn_date,
            'amount': amount,
            'description': description[:500],
            'payee': description[:255],
            'source': 'credit_card',
            'transaction_type': txn_type,
            'original_text': stripped,
        })

    return transactions
