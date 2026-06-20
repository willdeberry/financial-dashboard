import re
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from .pdf_parser import extract_text_from_pdf

# Closing date to determine year: "Closing Date01/02/26"
CLOSING_DATE_RE = re.compile(r'Closing Date\s*(\d{2}/\d{2}/(\d{2}))', re.IGNORECASE)

# Transaction line: MM/DD/YY[*] Description $Amount or -$Amount
TX_RE = re.compile(
    r'^(\d{2}/\d{2}/\d{2})\*?\s+'   # date (with optional * for posting date)
    r'(.+?)\s+'                        # description
    r'(-?\$[\d,]+\.\d{2})\s*$'        # amount (positive = charge, negative = payment/credit)
)

# Lines that signal we've left the transaction detail section
SECTION_BREAK_RE = re.compile(
    r'^(?:Fees|Interest Charged|About Trailing|Total Fees|Total Interest|'
    r'2026 Fees|2025 Fees|Interest Charge Calculation|SkyMiles|'
    r'Delta SkyMiles|IMPORTANT NOTICES|Payments and Credits|'
    r'New Charges|Summary|Detail\s*\*|Payments\s+Amount|'
    r'Card Ending\s*\d)',
    re.IGNORECASE,
)

# Lines to skip entirely
SKIP_RE = re.compile(
    r'^(?:Continued on|See page|See reverse|Please refer|Pay Your Bill|'
    r'Change of Address|Visit americanexpress|For information|'
    r'Please do not|WILLIAM D DEBERRY II\s+Account Ending|'
    r'Delta SkyMiles.*p\.\s*\d)',
    re.IGNORECASE,
)

# Payment lines — skip these (paying off the card balance, not real spending)
PAYMENT_RE = re.compile(r'PAYMENT\s*-\s*THANK YOU', re.IGNORECASE)

# Amex inline category hints (appear on lines below the transaction)
# Maps hint keywords to our category names
HINT_MAP = {
    'grocery': 'Groceries',
    'supermarket': 'Groceries',
    'food & bev': 'Dining',
    'food&bev': 'Dining',
    'restaurant': 'Dining',
    'fast food': 'Dining',
    'dining': 'Dining',
    'pharmacy': 'Healthcare',
    'pharmacies': 'Healthcare',
    'health': 'Healthcare',
    'medical': 'Healthcare',
    'drug store': 'Healthcare',
    'merchandise': 'Shopping',
    'discount store': 'Shopping',
    'retail': 'Shopping',
    'clothing': 'Shopping',
    'hardware': 'Shopping',
    'home improvement': 'Shopping',
    'wholesale': 'Shopping',
    'digital goods': 'Subscriptions',
    'streaming': 'Subscriptions',
    'utility': 'Utilities',
    'utilities': 'Utilities',
    'electric': 'Utilities',
    'gas service': 'Utilities',
    'telecom': 'Utilities',
    'parking': 'Transportation',
    'fuel': 'Transportation',
    'auto': 'Transportation',
    'airline': 'Travel',
    'hotel': 'Travel',
    'travel': 'Travel',
    'entertainment': 'Entertainment',
    'amusement': 'Entertainment',
    'charity': 'Other',
    'charities': 'Other',
    'education': 'Education',
    'government': 'Other',
    'insurance': 'Insurance',
}


def _parse_hint(line: str) -> Optional[str]:
    """Try to map an Amex MCC hint line to one of our categories."""
    lower = line.lower().strip()
    for key, cat in HINT_MAP.items():
        if key in lower:
            return cat
    return None


def _parse_date(date_str: str, base_year: int) -> Optional[datetime]:
    """Parse MM/DD/YY using base_year to resolve the century."""
    try:
        m, d, yy = date_str.split('/')
        # 25 → 2025, 26 → 2026, etc.
        year = 2000 + int(yy)
        return datetime(year, int(m), int(d))
    except (ValueError, TypeError):
        return None


def parse_amex_monthly(file_content: bytes) -> List[Dict]:
    pages = extract_text_from_pdf(file_content)
    full_text = '\n'.join(pages)

    # Determine base year from closing date
    cd_match = CLOSING_DATE_RE.search(full_text)
    base_year = 2000 + int(cd_match.group(2)) if cd_match else datetime.utcnow().year

    transactions: List[Dict] = []
    lines = full_text.split('\n')
    in_detail = False  # True once we're past the "Detail" header

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if not line or SKIP_RE.match(line):
            continue

        # Enter detail section when we see "Detail" header
        if re.match(r'^Detail\b', line, re.IGNORECASE):
            in_detail = True
            continue

        if SECTION_BREAK_RE.match(line) and in_detail:
            # "Fees" and "Interest" mark end of charges; stop parsing
            if re.match(r'^(?:Fees|Interest Charged)', line, re.IGNORECASE):
                break
            continue

        if not in_detail:
            continue

        m = TX_RE.match(line)
        if not m:
            continue

        date_str, description, amount_str = m.groups()

        # Skip payment lines
        if PAYMENT_RE.search(description):
            continue

        date = _parse_date(date_str, base_year)
        if not date:
            continue

        raw_amount = Decimal(amount_str.replace('$', '').replace(',', ''))

        # Negative = credit/refund → income; positive = charge → expense
        if raw_amount < 0:
            amount = abs(raw_amount)
            transaction_type = 'income'
        else:
            amount = raw_amount
            transaction_type = 'expense'

        if amount == 0:
            continue

        # Look ahead up to 3 lines for an Amex category hint
        amex_category = None
        for j in range(i, min(i + 3, len(lines))):
            next_line = lines[j].strip()
            if not next_line or TX_RE.match(next_line) or SECTION_BREAK_RE.match(next_line):
                break
            hint = _parse_hint(next_line)
            if hint:
                amex_category = hint
                break

        transactions.append({
            'date': date,
            'amount': amount,
            'description': description.strip()[:500],
            'payee': description.strip()[:255],
            'source': 'credit_card',
            'transaction_type': transaction_type,
            'amex_category': amex_category,
            'original_text': line,
        })

    return transactions
