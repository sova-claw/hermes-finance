"""Unit tests for the canonical categories module."""

from finance_api.domains.transactions import categories as cat


def test_all_contains_every_constant() -> None:
    constants = {
        cat.FOOD_AND_DRINK,
        cat.GROCERIES,
        cat.TRANSPORTATION,
        cat.HEALTHCARE,
        cat.SHOPPING,
        cat.ENTERTAINMENT,
        cat.TRAVEL,
        cat.SUBSCRIPTIONS,
        cat.UTILITIES,
        cat.ATM_CASH,
        cat.FINANCE,
        cat.EDUCATION,
        cat.PETS,
        cat.CASHBACK,
    }
    assert constants == cat.ALL


def test_all_is_frozen() -> None:
    assert isinstance(cat.ALL, frozenset)


def test_no_duplicates() -> None:
    # frozenset deduplifies, so if len differs the constants list has dupes
    constants_list = [
        cat.FOOD_AND_DRINK,
        cat.GROCERIES,
        cat.TRANSPORTATION,
        cat.HEALTHCARE,
        cat.SHOPPING,
        cat.ENTERTAINMENT,
        cat.TRAVEL,
        cat.SUBSCRIPTIONS,
        cat.UTILITIES,
        cat.ATM_CASH,
        cat.FINANCE,
        cat.EDUCATION,
        cat.PETS,
        cat.CASHBACK,
    ]
    assert len(constants_list) == len(cat.ALL)


def test_all_are_strings() -> None:
    for c in cat.ALL:
        assert isinstance(c, str)
        assert len(c) > 0
