import re
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from .pdf_parser import extract_text_from_pdf

YEAR_RE = re.compile(
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s*-\s*'
    r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+(\d{4})',
    re.IGNORECASE,
)

DATE_RE = re.compile(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\b', re.IGNORECASE)

# Credit/Debit + direction + amount + balance at end of line
TX_TAIL_RE = re.compile(
    r'(Credit|Debit)\s+([+-])\s+\$([\d,]+\.\d{2})\s+\$([\d,]+\.\d{2})\s*$',
    re.IGNORECASE,
)

# Lines to discard before accumulating descriptions
RESET_PATTERNS = [
    re.compile(r'^DATE\s+DESCRIPTION', re.IGNORECASE),
    re.compile(r'^Page \d+ of \d+', re.IGNORECASE),
    re.compile(r'capitalone\.com', re.IGNORECASE),
    re.compile(r'^Fees Summary', re.IGNORECASE),
    re.compile(r'TOTAL FOR THIS', re.IGNORECASE),
    re.compile(r'TOTAL YEAR-TO', re.IGNORECASE),
    re.compile(r'ANNUAL PERCENTAGE', re.IGNORECASE),
    re.compile(r'^(Total Overdraft|Total Return)', re.IGNORECASE),
    re.compile(r'STATEMENT PERIOD', re.IGNORECASE),
    re.compile(r'P\.O\. Box', re.IGNORECASE),
]

SKIP_DESCRIPTIONS = {'opening balance', 'closing balance'}

MONTH_MAP = {m: i + 1 for i, m in enumerate(
    ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
)}


def _is_noise(line: str) -> bool:
    return any(p.search(line) for p in RESET_PATTERNS)


def _parse_date(month_str: str, day_str: str, year: int) -> datetime:
    return datetime(year, MONTH_MAP[month_str.lower()[:3]], int(day_str))


def parse_capital_one_statement(file_content: bytes) -> List[Dict]:
    pages = extract_text_from_pdf(file_content)
    full_text = '\n'.join(pages)

    year_match = YEAR_RE.search(full_text)
    year = int(year_match.group(1)) if year_match else datetime.utcnow().year

    transactions: List[Dict] = []

    for page_text in pages:
        lines = page_text.split('\n')
        pre_desc: List[str] = []   # description lines appearing before the tx line
        expecting_post = False     # True when the last tx had no inline description

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Noise lines reset the pre-description buffer and post-desc expectation
            if _is_noise(line):
                pre_desc = []
                expecting_post = False
                continue

            tail_match = TX_TAIL_RE.search(line)

            if not tail_match:
                # Not a transaction line
                if expecting_post:
                    # This line is the trailing part of the previous transaction's description
                    if transactions:
                        transactions[-1]['description'] = (transactions[-1]['description'] + ' ' + line).strip()[:500]
                        transactions[-1]['payee'] = transactions[-1]['description'][:255]
                    expecting_post = False
                else:
                    pre_desc.append(line)
                continue

            # --- Transaction line ---
            expecting_post = False
            tx_type_str, direction, amount_str, _ = tail_match.groups()
            before_tail = line[:tail_match.start()].strip()

            date_match = DATE_RE.match(before_tail)
            if not date_match:
                pre_desc = []
                continue

            date = _parse_date(date_match.group(1), date_match.group(2), year)
            desc_inline = before_tail[date_match.end():].strip()

            if desc_inline:
                # Full description is on this line; pre_desc lines are unrelated header text
                description = desc_inline
                expecting_post = False
            else:
                # Description was on the line(s) before this one
                description = ' '.join(pre_desc).strip()
                expecting_post = True  # continuation may follow on next line

            pre_desc = []

            if not description or description.lower() in SKIP_DESCRIPTIONS:
                continue

            amount = Decimal(amount_str.replace(',', ''))
            if direction == '+':
                transaction_type = 'income'
            else:
                transaction_type = 'transfer' if any(
                    kw in description.upper() for kw in (
                        'TRANSFER', 'ZELLE', 'VENMO', 'WEBXFR', 'P2P',
                        # Credit card payments — avoid double-counting charges from CC statements
                        'AMERICAN EXPRESS', 'AMEX', 'COMENITY', 'DISCOVER', 'CHASE',
                        'CITIBANK', 'CITI CARD', 'CAPITAL ONE PYMT', 'SYNCHRONY',
                        'BARCLAYS', 'BANK OF AMERICA', 'WELLS FARGO', 'US BANK',
                    )
                ) else 'expense'

            transactions.append({
                'date': date,
                'amount': amount,
                'description': description[:500],
                'payee': description[:255],
                'source': 'bank',
                'transaction_type': transaction_type,
                'original_text': line,
            })

    return transactions
