"""Unit tests for MCC -> category mapping."""

from finance_api.domains.sync.mcc import MCC_LOOKUP
from finance_api.domains.transactions import categories as cat


def test_common_restaurant_codes() -> None:
    assert MCC_LOOKUP[5812] == cat.FOOD_AND_DRINK
    assert MCC_LOOKUP[5811] == cat.FOOD_AND_DRINK
    assert MCC_LOOKUP[5814] == cat.FOOD_AND_DRINK


def test_grocery_codes() -> None:
    assert MCC_LOOKUP[5411] == cat.GROCERIES
    assert MCC_LOOKUP[5412] == cat.GROCERIES


def test_transportation_codes() -> None:
    assert MCC_LOOKUP[4111] == cat.TRANSPORTATION
    assert MCC_LOOKUP[4121] == cat.TRANSPORTATION  # taxis


def test_airline_range_maps_to_travel() -> None:
    # Airlines: MCC 3000-3299
    for mcc in (3000, 3001, 3100, 3200, 3299):
        assert MCC_LOOKUP.get(mcc) == cat.TRAVEL, f"MCC {mcc} should be Travel"


def test_hotel_range_maps_to_travel() -> None:
    # Hotels: MCC 3500-3826
    for mcc in (3500, 3600, 3700, 3826):
        assert MCC_LOOKUP.get(mcc) == cat.TRAVEL, f"MCC {mcc} should be Travel"


def test_car_rental_range_maps_to_transportation() -> None:
    # Car rentals: MCC 3300-3499
    for mcc in (3300, 3400, 3499):
        assert MCC_LOOKUP.get(mcc) == cat.TRANSPORTATION, (
            f"MCC {mcc} should be Transportation"
        )


def test_atm_codes() -> None:
    assert MCC_LOOKUP[6011] == cat.ATM_CASH
    assert MCC_LOOKUP[6010] == cat.ATM_CASH


def test_utility_codes() -> None:
    assert MCC_LOOKUP[4814] == cat.UTILITIES
    assert MCC_LOOKUP[4911] == cat.UTILITIES


def test_all_values_are_known_categories() -> None:
    for mcc, category in MCC_LOOKUP.items():
        assert category in cat.ALL, f"MCC {mcc} maps to unknown category '{category}'"


def test_no_unknown_mcc_zero() -> None:
    assert 0 not in MCC_LOOKUP
