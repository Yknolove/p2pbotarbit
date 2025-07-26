"""
Динамический поиск арбитражных сделок.

Этот модуль отвечает за обработку колбека, который отображает
подходящие сделки согласно фильтрам пользователя. Чтобы избежать
конфликта с главным меню, используется уникальное значение
`callback_data` — ``arbitrage_deals``.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
import json
from config import FILTERS_FILE


# Роутер для динамического арбитража.
router = Router()


@router.callback_query(F.data == "arbitrage_deals")
async def show_arbitrage_deals(call: CallbackQuery) -> None:
    """
    Отображает список сделок, подходящих под фильтр пользователя. Если
    фильтр не настроен, предлагает воспользоваться командой /filter.
    """
    user_id = str(call.from_user.id)
    try:
        with open(FILTERS_FILE, "r") as f:
            filters = json.load(f)
        user_filter = filters.get(user_id)
    except (FileNotFoundError, json.JSONDecodeError):
        user_filter = None

    if not user_filter:
        await call.message.edit_text(
            "📊 Арбитраж \n\n"
            "❗ У вас не настроен фильтр.\n"
            "Используйте команду /filter, чтобы его создать.",
            parse_mode="HTML",
        )
        return

    # Заглушка — пример сделок
    example_deals = [
        {"buy": 41.10, "sell": 42.85, "volume": 95, "url": "https://example.com/deal1"},
        {"buy": 40.90, "sell": 43.00, "volume": 100, "url": "https://example.com/deal2"},
    ]

    matched: list[dict] = []
    for deal in example_deals:
        if (
            deal["buy"] <= user_filter["buy_price"]
            and deal["sell"] >= user_filter["sell_price"]
            and deal["volume"] <= user_filter["volume"]
        ):
            matched.append(deal)

    if not matched:
        await call.message.edit_text(
            "📊 Арбитраж \n\n"
            "⚠️ Сейчас нет подходящих сделок по вашему фильтру.",
            parse_mode="HTML",
        )
        return

    text = "📊 Найдено сделок: \n\n"
    for deal in matched:
        url_text = f"🔗 <a href=\"{deal['url']}\">Открыть ордер</a>" if deal.get("url") else ""
        text += (
            f"🟢 Купить по: {deal['buy']} \n"
            f"🔴 Продать по: {deal['sell']} \n"
            f"💵 Объём: ${deal['volume']}\n"
            f"{url_text}\n\n"
        )

    await call.message.edit_text(text, parse_mode="HTML")