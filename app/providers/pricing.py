import json
import math
import os


def configured_prices():
    raw = os.getenv("MODEL_PRICES_JSON", "").strip()
    try:
        prices = json.loads(raw) if raw else {}
        if not isinstance(prices, dict):
            raise ValueError
        for rates in prices.values():
            if not isinstance(rates, dict):
                raise ValueError
            for direction in ("input", "output"):
                value = rates.get(direction)
                if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                    raise ValueError
    except (ValueError, OverflowError):
        raise ValueError(
            "MODEL_PRICES_JSON must map model identifiers to finite nonnegative input and output rates"
        ) from None
    return prices
