"""
Filtering engine for the ArbitPro bot.

This module provides a single function, ``apply_filters``, which reads user
filter configurations from a JSON file and applies them to a list of ticker
objects returned by the P2P fetcher.  The original implementation from the
repository is included here without modification to preserve semantics.
"""

import json
import logging
from typing import Any, Dict, List


def apply_filters(tickers: List[Dict[str, Any]], filters_file: str) -> List[Dict[str, Any]]:
    """Load user filters from ``filters_file`` and apply them to a list of tickers.

    Each user's filter may define minimum and maximum thresholds for the buy
    (our purchase) and sell (our sale) prices as well as minimum/maximum
    volumes.  The original implementation used simple upper limits; this version
    expands the logic to support ranges.  All numeric values are converted to
    floats to ensure proper comparison.  Unknown values fall back to sensible
    defaults (e.g. no limit).

    Args:
        tickers: A list of ticker dictionaries containing at least the keys
            ``price`` (buy price), ``sell_price``, and ``volume``.  Additional
            fields (e.g. ``url`` or ``symbol``) are preserved.
        filters_file: Path to a JSON file storing per‑chat filter settings.

    Returns:
        A list of ticker entries that satisfy at least one user's filter
        criteria.  Each returned dict includes the additional keys
        ``chat_id`` and ``exchange`` corresponding to the filter that
        matched.
    """
    try:
        with open(filters_file, "r") as f:
            filters = json.load(f)
    except Exception:
        filters = {}

    results: List[Dict[str, Any]] = []
    for chat_id, f in filters.items():
        # Extract filter thresholds.  If a field is missing, use a default that
        # disables the constraint (e.g. -inf for min values, +inf for max).
        buy_min = float(f.get("buy_price_min", float("-inf")))
        buy_max = float(f.get("buy_price_max", float("inf")))
        sell_min = float(f.get("sell_price_min", float("-inf")))
        sell_max = float(f.get("sell_price_max", float("inf")))
        vol_min = float(f.get("volume_min", 0))
        vol_max = float(f.get("volume_max", float("inf")))
        exchange = f.get("exchange", "binance")

        # Optionally filter by bank/payment method.  The ticker dictionaries
        # currently do not include bank information, but this hook allows for
        # future extension.  If the filter specifies banks and the ticker
        # contains a ``bank`` field, only tickers matching one of the banks
        # should pass.
        allowed_banks = f.get("banks", [])

        for t in tickers:
            # Skip malformed ticker objects
            if "price" not in t:
                logging.warning(f"[filter_engine] Нет ключа 'price' в: {t}")
                continue

            price = float(t.get("price", 0))
            sell_price = float(t.get("sell_price", price))
            volume = float(t.get("volume", 0))

            # Apply price and volume range filters.  The ticker must satisfy
            # * buy_min <= price <= buy_max
            # * sell_min <= sell_price <= sell_max
            # * vol_min <= volume <= vol_max
            if not (buy_min <= price <= buy_max):
                continue
            if not (sell_min <= sell_price <= sell_max):
                continue
            if not (vol_min <= volume <= vol_max):
                continue

            # If banks are specified and ticker includes bank info, ensure it
            # matches one of the allowed banks.  Otherwise ignore bank filter.
            bank = t.get("bank")
            if allowed_banks and bank and bank not in allowed_banks:
                continue

            # All checks passed; record the match.  Preserve all ticker fields
            # and annotate with chat_id and exchange.
            results.append({
                **t,
                "chat_id": chat_id,
                "exchange": exchange,
            })

    return results