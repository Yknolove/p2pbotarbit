"""
Агрегатор для ArbitPro.

Этот модуль запускает бесконечный цикл, который запрашивает P2P‑ордера на биржах,
применяет фильтры пользователей и отправляет уведомления через Telegram‑бот.
Если ордер содержит ссылку, она добавляется в сообщение как HTML‑ссылка.
"""
import asyncio
import logging
from typing import Optional

from aiohttp import ClientSession
from config import FILTERS_FILE
from services.filter_engine import apply_filters
from services.p2p_fetcher import P2PFetcher

async def fetch_p2p_orders(session: ClientSession):
    """Получить ордера с поддерживаемых P2P‑бирж."""
    fetcher = P2PFetcher(session)
    return await fetcher.fetch_orders()

async def start_aggregator(session: ClientSession, bot):
    """Запустить цикл агрегатора: получение ордеров, фильтрация, уведомления."""
    logging.info("🟢 Агрегатор запущен")

    while True:
        try:
            tickers = await fetch_p2p_orders(session)
            logging.info(f"🟢 P2P вернул {len(tickers)} ордеров")
        except Exception as e:
            logging.error("💥 Ошибка при получении данных P2P", exc_info=e)
            await asyncio.sleep(15)
            continue

        orders = apply_filters(tickers, FILTERS_FILE)

        for order in orders:
            chat_id: int = order["chat_id"]
            symbol: str = order["symbol"]
            buy = order["buy"]
            sell = order["sell"]
            volume = order["volume"]
            url: Optional[str] = order.get("url")

            # формируем текст уведомления
            text = (
                f"📢 Найден арбитраж по {symbol}:\n"
                f"💰 Покупка: {buy}\n"
                f"💵 Продажа: {sell}\n"
                f"📦 Объём: {volume}"
            )
            if url:
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
