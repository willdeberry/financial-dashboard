import re
from typing import List, Dict
from .pdf_parser import extract_text_from_pdf
from .bank_parser import parse_date, parse_amount, DATE_PATTERNS, AMOUNT_PATTERN, SKIP_KEYWORDS
from .amex_parser import parse_amex_year_end

CC_DETECTORS = [
    (re.compile(r'year-end summary', re.IGNORECASE), parse_amex_year_end),
    (re.compile(r'american express', re.IGNORECASE), parse_amex_year_end),
]

CREDIT_INCOME_KEYWORDS = {'PAYMENT', 'CREDIT', 'REFUND', 'RETURN', 'ADJUSTMENT', 'REVERSAL'}
CC_SKIP_KEYWORDS = SKIP_KEYWORDS | {'MINIMUM PAYMENT', 'CREDIT LIMIT', 'AVAILABLE CREDIT', 'ACCOUNT SUMMARY'}


def parse_credit_card_statement(file_content: bytes) -> List[Dict]:
    pages = extract_text_from_pdf(file_content)
    full_text = '\n'.join(pages)

    for pattern, parser in CC_DETECTORS:
        if pattern.search(full_text):
            return parser(file_content)

    transactions = []

    for page_text in pages:
        for line in page_text.split('\n'):
            line = line.strip()
            if not line or any(kw in line.upper() for kw in CC_SKIP_KEYWORDS):
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
            if amount is None or amount == 0:
                continue

            line_upper = line.upper()
            is_income = any(kw in line_upper for kw in CREDIT_INCOME_KEYWORDS)
            transaction_type = "income" if is_income else "expense"
            amount = abs(amount)

            description = re.sub(AMOUNT_PATTERN, '', line)
            for pattern in DATE_PATTERNS:
                description = re.sub(pattern, '', description, flags=re.IGNORECASE)
            description = ' '.join(description.split()).strip()

            if not description:
                continue

            transactions.append({
                "date": date,
                "amount": amount,
                "description": description[:500],
                "payee": description[:255],
                "source": "credit_card",
                "transaction_type": transaction_type,
                "original_text": line,
            })

    return transactions
