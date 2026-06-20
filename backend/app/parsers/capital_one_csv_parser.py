import csv
import io
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import List, Dict

# Keywords on a Debit row that mean it's a transfer, not an expense
DEBIT_TRANSFER_KW = (
    'TRANSFER', 'ZELLE', 'VENMO', 'WEBXFR', 'P2P',
    # Internal Capital One accounts (masked with XXXXXXX)
    'XXXXXXX',
    # Credit card payments
    'AMERICAN EXPRESS', 'AMEX EPAYMENT', 'APPLECARD',
    'COMENITY', 'DISCOVER', 'CHASE CREDIT', 'CITIBANK',
    'SYNCHRONY', 'BARCLAYS',
)

# Keywords on a Credit row that mean it's an internal transfer, not income
CREDIT_TRANSFER_KW = (
    'XXXXXXX',            # internal savings/money accounts
    'APPLE CASH BANK XFER',
    'APPLE GS SAVINGS',
)

EXPECTED_HEADER = {'account number', 'transaction description', 'transaction date',
                   'transaction type', 'transaction amount', 'balance'}


def _parse_date(date_str: str) -> datetime:
    date_str = date_str.strip()
    for fmt in ('%m/%d/%y', '%m/%d/%Y', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str!r}")


def parse_capital_one_csv(content: bytes) -> List[Dict]:
    text = content.decode('utf-8-sig', errors='replace')
    reader = csv.reader(io.StringIO(text))

    header = next(reader, None)
    if header is None:
        return []

    # Normalise header names
    cols = [h.strip().lower() for h in header]
    if not EXPECTED_HEADER.issubset(set(cols)):
        raise ValueError(f"Unexpected CSV columns: {cols}")

    idx = {name: cols.index(name) for name in EXPECTED_HEADER}

    transactions: List[Dict] = []

    for row in reader:
        if not row or all(c.strip() == '' for c in row):
            continue
        if len(row) <= max(idx.values()):
            continue

        description = row[idx['transaction description']].strip()
        date_str    = row[idx['transaction date']].strip()
        tx_type     = row[idx['transaction type']].strip().lower()   # 'credit' or 'debit'
        amount_str  = row[idx['transaction amount']].strip()

        if not description or not date_str or not amount_str:
            continue

        try:
            amount = abs(Decimal(amount_str.replace('$', '').replace(',', '')))
        except InvalidOperation:
            continue

        if amount == 0:
            continue

        try:
            date = _parse_date(date_str)
        except ValueError:
            continue

        desc_upper = description.upper()

        if tx_type == 'credit':
            is_transfer = any(kw in desc_upper for kw in CREDIT_TRANSFER_KW)
            transaction_type = 'transfer' if is_transfer else 'income'
        else:
            is_transfer = any(kw in desc_upper for kw in DEBIT_TRANSFER_KW)
            transaction_type = 'transfer' if is_transfer else 'expense'

        transactions.append({
            'date': date,
            'amount': amount,
            'description': description[:500],
            'payee': description[:255],
            'source': 'bank',
            'transaction_type': transaction_type,
            'original_text': ','.join(row),
        })

    return transactions
