import re
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Optional
from .pdf_parser import extract_text_from_pdf

MONTHS = r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'

TX_RE = re.compile(
    r'^(\d{2}/\d{2}/\d{4})\s+'      # date
    r'(?:' + MONTHS + r')\s+'        # month billed (ignored)
    r'(.+?)\s+'                       # description
    r'\$([\d,]+\.\d{2})'             # charge
    r'(?:\s+\$([\d,]+\.\d{2}))?'     # optional credit
    r'\s*$'
)

SKIP_RE = re.compile(
    r'^(?:Date\s+Month|Subtotal\s+\$|Card Member\s+(?:Summary|Account)|'
    r'Account Number\s+Spending|Individual Spending|Activity by Card|'
    r'Details of Spending|Combined Spending|Account Summary|'
    r'\d{4}\s+Year-End|Includes charges|Prepared for|Page \d+|'
    r'Any charges processed|Total Spending|Monthly Totals|'
    r'(?:January|February|March|April|May|June|July|August|September|October|November|December)'
    r'\s+(?:January|February))',  # month header row in summary table
    re.IGNORECASE,
)

# Every Amex sub-category and which of our categories it maps to
CATEGORY_MAP = {
    # Groceries
    'groceries': 'Groceries',
    # Dining
    'restaurant': 'Dining',
    'bar & café': 'Dining',
    'bar & cafe': 'Dining',
    'fast food': 'Dining',
    # Transportation
    'transportation': 'Transportation',
    'auto services': 'Transportation',
    'fuel': 'Transportation',
    'parking charges': 'Transportation',
    'rideshare': 'Transportation',
    # Travel
    'travel': 'Travel',
    'airline': 'Travel',
    'hotels': 'Travel',
    'car rental': 'Travel',
    'cruises': 'Travel',
    # Entertainment
    'entertainment': 'Entertainment',
    'general events': 'Entertainment',
    'theatrical events': 'Entertainment',
    'theme parks': 'Entertainment',
    'music & video': 'Entertainment',
    'sports': 'Entertainment',
    # Subscriptions
    'cable & internet comm': 'Subscriptions',
    'cable & internet': 'Subscriptions',
    # Utilities
    'communications': 'Utilities',
    'utilities': 'Utilities',
    # Healthcare
    'health care services': 'Healthcare',
    'health care': 'Healthcare',
    'pharmacies': 'Healthcare',
    # Shopping
    'merchandise & supplies': 'Shopping',
    'clothing stores': 'Shopping',
    'computer supplies': 'Shopping',
    'general retail': 'Shopping',
    'office supplies': 'Shopping',
    'business services': 'Shopping',
    'hardware supplies': 'Shopping',
    'internet purchase': 'Shopping',
    'wholesale stores': 'Shopping',
    'sporting goods': 'Shopping',
    'home furnishings': 'Shopping',
    # Education
    'education': 'Education',
    # Other
    'other services': 'Other',
    'other': 'Other',
    'fees & adjustments': 'Other',
    'fees & adjustments': 'Other',
    'charities': 'Other',
    'government services': 'Other',
    'miscellaneous': 'Other',
    'insurance': 'Insurance',
}

# Noise lines that reset category context
NOISE_RE = re.compile(
    r'^(?:\d{4}\s+Year-End|Includes charges|Prepared for|Page \d+|'
    r'capitalone\.com|P\.O\. Box)',
    re.IGNORECASE,
)


def _match_category(line: str) -> Optional[str]:
    """Return our category name if line is an Amex section header, else None."""
    # Skip subtotal/total lines — they contain $ amounts
    if '$' in line:
        return None
    lower = line.strip().lower()
    # Exact match first (longest key wins via sorted order)
    for key in sorted(CATEGORY_MAP, key=len, reverse=True):
        if lower == key or lower.startswith(key + ' '):
            return CATEGORY_MAP[key]
    return None


def parse_amex_year_end(file_content: bytes) -> List[Dict]:
    pages = extract_text_from_pdf(file_content)
    transactions: List[Dict] = []
    current_category: Optional[str] = None

    for page_text in pages:
        for line in page_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            if NOISE_RE.match(line):
                continue

            if SKIP_RE.match(line):
                continue

            # Check for section/sub-section category header
            cat = _match_category(line)
            if cat:
                current_category = cat
                continue

            m = TX_RE.match(line)
            if not m:
                continue

            date_str, description, charge_str, credit_str = m.groups()

            try:
                date = datetime.strptime(date_str, '%m/%d/%Y')
            except ValueError:
                continue

            charge = Decimal(charge_str.replace(',', ''))
            credit = Decimal(credit_str.replace(',', '')) if credit_str else Decimal('0')

            if credit > 0 and charge == 0:
                amount = credit
                transaction_type = 'income'
            else:
                amount = charge
                transaction_type = 'expense'

            if amount == 0:
                continue

            transactions.append({
                'date': date,
                'amount': amount,
                'description': description.strip()[:500],
                'payee': description.strip()[:255],
                'source': 'credit_card',
                'transaction_type': transaction_type,
                'amex_category': current_category,
                'original_text': line,
            })

    return transactions
