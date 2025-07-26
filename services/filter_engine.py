"""
Модуль фильтрации для ArbitPro.

Функция `apply_filters` читает сохранённые фильтры пользователей из JSON‑файла
и применяет их к списку ордеров, полученных от бирж. Возвращает список ордеров,
удовлетворяющих хотя бы одному фильтру, с указанием `chat_id` пользователя и
биржи.
"""
import json
import logging
from typing import Any, Dict, List

def apply_filters(tickers: List[Dict[str, Any]], filters_file: str) -> List[Dict[str, Any]]:
    """Загрузить фильтры из filters_file и применить их к списку тикеров."""
    try:
        with open(filters_file, "r") as f:
            filters = json.load(f)
    except Exception:
        filters = {}

    results: List[Dict[str, Any]] = []
    for chat_id, f in filters.items():
        buy_limit = float(f.get("buy_price", 0))
        sell_limit = float(f.get("sell_price", 999_999))
        vol_limit = float(f.get("volume", 100))
        exchange = f.get("exchange", "bybit")

        for t in tickers:
            if "price" not in t:
                logging.warning(f"[filter_engine] Нет ключа 'price' в: {t}")
                continue
            if (
                t["price"] <= buy_limit and
                t.get("sell_price", t["price"]) >= sell_limit and
                t.get("volume", 0) <= vol_limit
            ):
                results.append({
                    **t,
                    "chat_id": chat_id,
                    "exchange": exchange,
                })
    return results
