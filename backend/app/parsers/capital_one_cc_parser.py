import re
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import List, Dict
from .pdf_parser import extract_text_from_pdf

MONTH_MAP = {m: i + 1 for i, m in enumerate(
    ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
)}

_MONTHS = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'

# "Aug 20, 2025 - Sep 18, 2025"
PERIOD_RE = re.compile(
    rf'({_MONTHS})\s+\d+,\s+(\d{{4}})\s*[-–]\s*({_MONTHS})\s+(\d+),\s+(\d{{4}})',
    re.IGNORECASE,
)

# Trans date  Post date  Description  (optional minus) $Amount
TXN_RE = re.compile(
    rf'^({_MONTHS})\s+(\d{{1,2}})\s+'   # trans date
    rf'{_MONTHS}\s+\d{{1,2}}\s+'         # post date (skip)
    r'(.+?)\s+'                           # description
    r'(-\s*)?\$\s*([\d,]+\.\d{2})\s*$',  # optional minus + amount
    re.IGNORECASE,
)

PAYMENTS_SECTION_RE = re.compile(r'Payments.*Credits.*Adjustments', re.IGNORECASE)
TXN_SECTION_RE = re.compile(r'#\d+:\s*Transactions\s*$', re.IGNORECASE)
END_RE = re.compile(
    r'^(Total\s+(?:Transactions|Fees|Interest)|Fees\s*$|Interest Charged|Totals Year)',
    re.IGNORECASE,
)
SKIP_RE = re.compile(
    r'^(Trans Date|Post Date|Page \d+|Visit capitalone)',
    re.IGNORECASE,
)


def _year_for(month: int, closing_month: int, closing_year: int) -> int:
    return closing_year if month <= closing_month else closing_year - 1


def parse_capital_one_cc_statement(file_content: bytes) -> List[Dict]:
    pages = extract_text_from_pdf(file_content)
    full_text = '\n'.join(pages)

    # Infer year from "Aug 20, 2025 - Sep 18, 2025"
    closing_year = date.today().year
    closing_month = date.today().month
    pm = PERIOD_RE.search(full_text)
    if pm:
        closing_month = MONTH_MAP.get(pm.group(3).lower(), closing_month)
        closing_year = int(pm.group(5))

    transactions = []
    section = None  # 'payments' | 'transactions' | None

    for line in full_text.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue

        # Section detection
        if PAYMENTS_SECTION_RE.search(stripped):
            section = 'payments'
            continue
        if TXN_SECTION_RE.search(stripped):
            section = 'transactions'
            continue

        # End of transaction data
        if section and END_RE.match(stripped):
            section = None
            continue

        if section is None or SKIP_RE.match(stripped):
            continue

        m = TXN_RE.match(stripped)
        if not m:
            continue

        month_str, day_str, description, minus, amount_str = m.groups()
        month = MONTH_MAP.get(month_str.lower())
        if not month:
            continue

        try:
            txn_date = datetime(_year_for(month, closing_month, closing_year), month, int(day_str))
        except ValueError:
            continue

        try:
            amount = Decimal(amount_str.replace(',', ''))
        except InvalidOperation:
            continue

        if amount == 0:
            continue

        txn_type = 'income' if section == 'payments' else 'expense'

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
