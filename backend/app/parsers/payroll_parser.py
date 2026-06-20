import re
from datetime import datetime
from typing import List, Dict
from .pdf_parser import extract_text_from_pdf
from .bank_parser import parse_date, parse_amount, DATE_PATTERNS, AMOUNT_PATTERN

INCOME_KEYWORDS = {'GROSS', 'NET PAY', 'EARNINGS', 'SALARY', 'WAGES', 'BONUS', 'OVERTIME', 'COMMISSION'}
DEDUCTION_KEYWORDS = {'FEDERAL TAX', 'STATE TAX', 'FICA', 'MEDICARE', 'DEDUCTION', '401K', 'HEALTH', 'DENTAL', 'VISION', 'SS TAX'}


def parse_payroll_stub(file_content: bytes) -> List[Dict]:
    pages = extract_text_from_pdf(file_content)
    transactions = []

    full_text = '\n'.join(pages)

    # Find pay date
    pay_date = None
    for pattern in DATE_PATTERNS:
        for match in re.finditer(pattern, full_text, re.IGNORECASE):
            d = parse_date(match.group(1))
            if d:
                pay_date = d
                break
        if pay_date:
            break

    if not pay_date:
        pay_date = datetime.utcnow()

    for page_text in pages:
        for line in page_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            line_upper = line.upper()
            is_income = any(kw in line_upper for kw in INCOME_KEYWORDS)
            is_deduction = any(kw in line_upper for kw in DEDUCTION_KEYWORDS)

            if not (is_income or is_deduction):
                continue

            amounts = re.findall(AMOUNT_PATTERN, line)
            if not amounts:
                continue

            amount = parse_amount(amounts[-1])
            if amount is None or amount == 0:
                continue

            amount = abs(amount)
            transaction_type = "income" if is_income else "expense"

            description = re.sub(AMOUNT_PATTERN, '', line).strip()
            description = ' '.join(description.split())

            transactions.append({
                "date": pay_date,
                "amount": amount,
                "description": description[:500] or "Payroll",
                "payee": "Employer" if is_income else description[:255],
                "source": "payroll",
                "transaction_type": transaction_type,
                "original_text": line,
            })

    return transactions
