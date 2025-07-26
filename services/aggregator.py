"""
Aggregator service for the ArbitPro Telegram bot.

This module contains a small loop that periodically fetches P2P order data from
supported exchanges, applies user‑defined filters and sends notifications
through the provided bot instance.  It has been slightly refactored to
include order URLs in the message body using HTML hyperlinks when available.

The original repository omitted the hyperlink text and therefore sent
messages without a working link.  Additionally, any unhandled exceptions
during fetching or sending will be logged and the loop will sleep briefly
before retrying.
"""

import asyncio
import logging
from typing import Optional

from aiohttp import ClientSession

from config import FILTERS_FILE
from services.filter_engine import apply_filters
from services.p2p_fetcher import P2PFetcher


async def fetch_p2p_orders(session: ClientSession):
    """Fetch buy/sell orders from supported P2P exchanges.

    This helper instantiates a P2PFetcher and delegates to its fetch_orders
    method.  It exists primarily to simplify unit testing.

    Args:
        session: A shared aiohttp client session.

    Returns:
        A list of ticker dictionaries with order information.
    """
    fetcher = P2PFetcher(session)
    return await fetcher.fetch_orders()


async def start_aggregator(session: ClientSession, bot):
    """Start the P2P aggregating loop.

    This coroutine runs indefinitely, periodically fetching P2P orders,
    applying user filters and dispatching notifications via the provided
    Telegram bot.  It logs useful information for debugging and handles
    network or API errors gracefully by retrying after a short delay.

    Args:
        session: A shared aiohttp client session used for HTTP requests.
        bot: An aiogram Bot instance used for sending messages.
    """
    logging.info("🟢 Агрегатор запущен")

    while True:
        try:
            tickers = await fetch_p2p_orders(session)
            logging.info(f"🟢 P2P вернул {len(tickers)} ордеров")
        except Exception as e:
            logging.error("💥 Ошибка при получении данных P2P", exc_info=e)
            # Sleep and retry if fetching fails
            await asyncio.sleep(15)
            continue

        # Apply user‑defined filters to the returned tickers
        orders = apply_filters(tickers, FILTERS_FILE)

        for order in orders:
            chat_id: int = order["chat_id"]
            symbol: str = order["symbol"]
            buy = order["buy"]
            sell = order["sell"]
            volume = order["volume"]
            url: Optional[str] = order.get("url")

            # Build the notification text with a hyperlink when a URL is provided
            text = (
                f"📢 Найден арбитраж по {symbol} :\n"
                f"💰 Покупка: {buy}\n"
                f"💵 Продажа: {sell}\n"
                f"📦 Объём: {volume}"
            )
            if url:
                # Append HTML link to the order using AIogram's HTML parse mode
                text += f"\n🔗 <a href=\"{url}\">Открыть ордер</a>"

            try:
                await bot.send_message(chat_id, text, parse_mode="HTML")
            except Exception as e:
                logging.error(
                    f"❌ Не удалось отправить сообщение пользователю {chat_id}",
                    exc_info=e,
                )

        logging.info("🔁 Цикл агрегатора завершён, спим 15 секунд")
        await asyncio.sleep(15)