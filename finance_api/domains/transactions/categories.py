"""Canonical spending categories shared across all integrations.

Every integration (Monobank, Revolut, etc.) must map its native codes to
one of these strings. Analytics queries and the API surface use only these.
"""

FOOD_AND_DRINK = "Food & Drink"
GROCERIES = "Groceries"
TRANSPORTATION = "Transportation"
HEALTHCARE = "Healthcare"
SHOPPING = "Shopping"
ENTERTAINMENT = "Entertainment"
TRAVEL = "Travel"
SUBSCRIPTIONS = "Subscriptions"
UTILITIES = "Utilities"
ATM_CASH = "ATM & Cash"
FINANCE = "Finance"
EDUCATION = "Education"
PETS = "Pets"
CASHBACK = "Cashback"

ALL: frozenset[str] = frozenset({
    FOOD_AND_DRINK,
    GROCERIES,
    TRANSPORTATION,
    HEALTHCARE,
    SHOPPING,
    ENTERTAINMENT,
    TRAVEL,
    SUBSCRIPTIONS,
    UTILITIES,
    ATM_CASH,
    FINANCE,
    EDUCATION,
    PETS,
    CASHBACK,
})
