import re
from typing import Optional
from sqlalchemy.orm import Session
from . import models


DEFAULT_CATEGORIES = [
    {"name": "Groceries", "color": "#22c55e", "icon": "shopping-cart"},
    {"name": "Dining", "color": "#f97316", "icon": "utensils"},
    {"name": "Transportation", "color": "#3b82f6", "icon": "car"},
    {"name": "Utilities", "color": "#a855f7", "icon": "zap"},
    {"name": "Rent/Mortgage", "color": "#ef4444", "icon": "home"},
    {"name": "Healthcare", "color": "#ec4899", "icon": "heart"},
    {"name": "Entertainment", "color": "#eab308", "icon": "play"},
    {"name": "Shopping", "color": "#06b6d4", "icon": "bag"},
    {"name": "Salary/Income", "color": "#10b981", "icon": "dollar-sign"},
    {"name": "Transfers", "color": "#6b7280", "icon": "repeat"},
    {"name": "Insurance", "color": "#8b5cf6", "icon": "shield"},
    {"name": "Education", "color": "#f59e0b", "icon": "book"},
    {"name": "Travel", "color": "#14b8a6", "icon": "plane"},
    {"name": "Subscriptions", "color": "#6366f1", "icon": "repeat"},
    {"name": "Other", "color": "#9ca3af", "icon": "circle"},
]

DEFAULT_RULES = [
    {
        "rule_name": "Grocery stores",
        "match_field": "payee",
        "match_pattern": r"(?i)(walmart|target|kroger|safeway|whole foods|trader joe|publix|albertsons|aldi|costco|sam'?s club|food lion|sprouts|wegmans|harris teeter)",
        "category_name": "Groceries",
        "priority": 10,
    },
    {
        "rule_name": "Restaurants & cafes",
        "match_field": "payee",
        "match_pattern": r"(?i)(mcdonald|burger king|wendy|taco bell|subway|starbucks|dunkin|chipotle|panera|pizza|restaurant|grill|cafe|diner|sushi|thai|chinese|mexican|italian|doordash|grubhub|ubereats)",
        "category_name": "Dining",
        "priority": 10,
    },
    {
        "rule_name": "Gas stations",
        "match_field": "payee",
        "match_pattern": r"(?i)(shell|bp|exxon|mobil|chevron|sunoco|marathon|speedway|circle k|wawa|gas station|fuel)",
        "category_name": "Transportation",
        "priority": 10,
    },
    {
        "rule_name": "Ride share",
        "match_field": "payee",
        "match_pattern": r"(?i)(uber|lyft|taxi|cab)",
        "category_name": "Transportation",
        "priority": 10,
    },
    {
        "rule_name": "Electric & gas utility",
        "match_field": "payee",
        "match_pattern": r"(?i)(electric|gas company|pg&e|con ed|national grid|duke energy|dominion|utility|utilities)",
        "category_name": "Utilities",
        "priority": 10,
    },
    {
        "rule_name": "Internet & phone",
        "match_field": "payee",
        "match_pattern": r"(?i)(comcast|verizon|at&t|t-mobile|sprint|xfinity|spectrum|internet|wireless|mobile)",
        "category_name": "Utilities",
        "priority": 9,
    },
    {
        "rule_name": "Rent payment",
        "match_field": "description",
        "match_pattern": r"(?i)(rent|mortgage|lease)",
        "category_name": "Rent/Mortgage",
        "priority": 10,
    },
    {
        "rule_name": "Healthcare",
        "match_field": "payee",
        "match_pattern": r"(?i)(pharmacy|cvs|walgreens|doctor|hospital|clinic|medical|dental|vision|health)",
        "category_name": "Healthcare",
        "priority": 10,
    },
    {
        "rule_name": "Streaming subscriptions",
        "match_field": "payee",
        "match_pattern": r"(?i)(netflix|hulu|disney|spotify|apple music|amazon prime|hbo|paramount|peacock|youtube premium)",
        "category_name": "Subscriptions",
        "priority": 10,
    },
    {
        "rule_name": "Amazon shopping",
        "match_field": "payee",
        "match_pattern": r"(?i)amazon(?!.*prime)",
        "category_name": "Shopping",
        "priority": 8,
    },
    {
        "rule_name": "Payroll direct deposit",
        "match_field": "description",
        "match_pattern": r"(?i)(payroll|direct dep|salary|wages|employer)",
        "category_name": "Salary/Income",
        "priority": 10,
    },
    {
        "rule_name": "Bank deposit (income)",
        "match_field": "description",
        "match_pattern": r"(?i)^deposit from",
        "category_name": "Salary/Income",
        "priority": 11,
    },
    {
        "rule_name": "Interest income",
        "match_field": "description",
        "match_pattern": r"(?i)monthly interest paid",
        "category_name": "Salary/Income",
        "priority": 11,
    },
    {
        "rule_name": "Transfers",
        "match_field": "description",
        "match_pattern": r"(?i)(transfer|zelle|venmo|paypal|cash app)",
        "category_name": "Transfers",
        "priority": 10,
    },
    {
        "rule_name": "Travel",
        "match_field": "payee",
        "match_pattern": r"(?i)(airline|delta|united|american air|southwest|jetblue|hotel|marriott|hilton|hyatt|airbnb|expedia|booking)",
        "category_name": "Travel",
        "priority": 10,
    },
    {
        "rule_name": "Insurance",
        "match_field": "payee",
        "match_pattern": r"(?i)(insurance|geico|state farm|allstate|progressive|liberty mutual)",
        "category_name": "Insurance",
        "priority": 10,
    },
    {
        "rule_name": "Education",
        "match_field": "payee",
        "match_pattern": r"(?i)(tuition|university|college|school|udemy|coursera|chegg|student loan)",
        "category_name": "Education",
        "priority": 10,
    },
]


def seed_default_data(db: Session) -> None:
    category_map: dict[str, int] = {}

    for cat_data in DEFAULT_CATEGORIES:
        existing = db.query(models.Category).filter(models.Category.name == cat_data["name"]).first()
        if not existing:
            category = models.Category(**cat_data)
            db.add(category)
            db.flush()
            category_map[cat_data["name"]] = category.id
        else:
            category_map[cat_data["name"]] = existing.id

    db.commit()

    # Reload IDs after commit
    for cat_data in DEFAULT_CATEGORIES:
        cat = db.query(models.Category).filter(models.Category.name == cat_data["name"]).first()
        if cat:
            category_map[cat_data["name"]] = cat.id

    for rule_data in DEFAULT_RULES:
        category_name = rule_data["category_name"]
        if category_name not in category_map:
            continue
        existing = db.query(models.CategorizationRule).filter(
            models.CategorizationRule.rule_name == rule_data["rule_name"]
        ).first()
        if not existing:
            db.add(models.CategorizationRule(
                rule_name=rule_data["rule_name"],
                match_field=rule_data["match_field"],
                match_pattern=rule_data["match_pattern"],
                category_id=category_map[category_name],
                priority=rule_data["priority"],
            ))

    db.commit()


def categorize_transaction(db: Session, payee: Optional[str], description: Optional[str]) -> Optional[int]:
    rules = (
        db.query(models.CategorizationRule)
        .filter(models.CategorizationRule.active == True)
        .order_by(models.CategorizationRule.priority.desc())
        .all()
    )

    for rule in rules:
        text = payee if rule.match_field == "payee" else description
        if not text:
            continue
        try:
            if re.search(rule.match_pattern, text, re.IGNORECASE):
                return rule.category_id
        except re.error:
            continue

    return None
