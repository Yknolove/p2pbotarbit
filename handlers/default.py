# tweak for CI run
from bot import dp
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.filters.state import StateFilter
import json
import os

# FSM states for interactive filter
class FilterStates(StatesGroup):
    waiting_for_choice = State()
    waiting_buy_max = State()
    waiting_sell_min = State()
    waiting_sell_max = State()
    waiting_volume_min = State()
    waiting_banks = State()
    waiting_exchanges = State()

# Utility: load/save filter
def filter_file_path(user_id: int) -> str:
    return os.path.join(os.getcwd(), f"filters_{user_id}.json")

def load_filter(user_id: int) -> dict:
    path = filter_file_path(user_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "buy_price_max": None,
        "sell_price_min": None,
        "sell_price_max": None,
        "volume_min": None,
        "banks": [],
        "exchanges": []
    }

def save_filter(user_id: int, data: dict):
    path = filter_file_path(user_id)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def update_filter(user_id: int, **kwargs):
    data = load_filter(user_id)
    data.update(kwargs)
    save_filter(user_id, data)

async def toggle_filter_list_item(user_id: int, key: str, item: str):
    data = load_filter(user_id)
    items = data.get(key, [])
    if item in items:
        items.remove(item)
    else:
        items.append(item)
    data[key] = items
    save_filter(user_id, data)

# Main menu
@dp.message(Command("start"))
async def cmd_start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск арбитража", callback_data="start_arbitrage")],
        [InlineKeyboardButton(text="⚙️ Изменить фильтр", callback_data="filter_menu")],
        [InlineKeyboardButton(text="💱 Курс валют", callback_data="currency_rate")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
        [InlineKeyboardButton(text="👑 Перейти в PRO", callback_data="go_pro")]
    ])
    await message.answer("Добро пожаловать! Выберите действие:", reply_markup=kb)

# Show filter menu
@dp.callback_query(lambda c: c.data == "filter_menu")
async def filter_menu(callback: CallbackQuery, state: FSMContext):
    current = load_filter(callback.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(f"Покупка до ({current['buy_price_max']})", callback_data="set_buy_max")],
        [InlineKeyboardButton(f"Продажа от ({current['sell_price_min']})", callback_data="set_sell_min"),
         InlineKeyboardButton(f"до ({current['sell_price_max']})", callback_data="set_sell_max")],
        [InlineKeyboardButton(f"Мин. объём ({current['volume_min']})", callback_data="set_volume_min")],
        [InlineKeyboardButton("Банки…", callback_data="set_banks")],
        [InlineKeyboardButton("Биржи…", callback_data="set_exchanges")],
        [InlineKeyboardButton("Готово", callback_data="finish_filter")]
    ])
    await callback.message.edit_text("Что хотите изменить?", reply_markup=kb)
    await state.set_state(FilterStates.waiting_for_choice)

# Change buy_max
@dp.callback_query(lambda c: c.data == "set_buy_max", StateFilter(FilterStates.waiting_for_choice))
async def ask_buy_max(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите максимальную цену покупки (число):")
    await state.set_state(FilterStates.waiting_buy_max)

@dp.message(StateFilter(FilterStates.waiting_buy_max))
async def process_buy_max(message: Message, state: FSMContext):
    try:
        val = float(message.text.replace(',', '.'))
    except ValueError:
        return await message.answer("Неверный формат, введите число, например 41.2")
    await update_filter(message.from_user.id, buy_price_max=val)
    await message.answer(f"✅ Цена покупки до {val} грн сохранена.")
    await filter_menu(message, state)

# Change sell_min
@dp.callback_query(lambda c: c.data == "set_sell_min", StateFilter(FilterStates.waiting_for_choice))
async def ask_sell_min(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите минимальную цену продажи (число):")
    await state.set_state(FilterStates.waiting_sell_min)

@dp.message(StateFilter(FilterStates.waiting_sell_min))
async def process_sell_min(message: Message, state: FSMContext):
    try:
        val = float(message.text.replace(',', '.'))
    except ValueError:
        return await message.answer("Неверный формат, введите число, например 42.5")
    await update_filter(message.from_user.id, sell_price_min=val)
    await message.answer(f"✅ Цена продажи от {val} грн сохранена.")
    await filter_menu(message, state)

# Change sell_max
@dp.callback_query(lambda c: c.data == "set_sell_max", StateFilter(FilterStates.waiting_for_choice))
async def ask_sell_max(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите максимальную цену продажи (число):")
    await state.set_state(FilterStates.waiting_sell_max)

@dp.message(StateFilter(FilterStates.waiting_sell_max))
async def process_sell_max(message: Message, state: FSMContext):
    try:
        val = float(message.text.replace(',', '.'))
    except ValueError:
        return await message.answer("Неверный формат, введите число, например 43.0")
    await update_filter(message.from_user.id, sell_price_max=val)
    await message.answer(f"✅ Цена продажи до {val} грн сохранена.")
    await filter_menu(message, state)

# Change volume_min
@dp.callback_query(lambda c: c.data == "set_volume_min", StateFilter(FilterStates.waiting_for_choice))
async def ask_volume(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите минимальный объём сделки (USD):")
    await state.set_state(FilterStates.waiting_volume_min)

@dp.message(StateFilter(FilterStates.waiting_volume_min))
async def process_volume(message: Message, state: FSMContext):
    try:
        val = float(message.text.replace(',', '.'))
    except ValueError:
        return await message.answer("Неверный формат, введите число, например 250")
    await update_filter(message.from_user.id, volume_min=val)
    await message.answer(f"✅ Мин. объём {val} USD сохранён.")
    await filter_menu(message, state)

# Change banks
@dp.callback_query(lambda c: c.data == "set_banks", StateFilter(FilterStates.waiting_for_choice))
async def ask_banks(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Monobank", callback_data="bank_Monobank")],
        [InlineKeyboardButton("Raiffeisen", callback_data="bank_Raiffeisen")],
        [InlineKeyboardButton("Готово", callback_data="banks_done")]
    ])
    await callback.message.edit_text("Выберите банки (нажмите для переключения):", reply_markup=kb)
    await state.set_state(FilterStates.waiting_banks)

@dp.callback_query(lambda c: c.data.startswith("bank_"), StateFilter(FilterStates.waiting_banks))
async def toggle_bank(callback: CallbackQuery, state: FSMContext):
    bank = callback.data.split("_", 1)[1]
    await toggle_filter_list_item(callback.from_user.id, 'banks', bank)
    await ask_banks(callback, state)

@dp.callback_query(lambda c: c.data == "banks_done", StateFilter(FilterStates.waiting_banks))
async def banks_done(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✅ Банки сохранены.")
    await filter_menu(callback, state)

# Change exchanges
@dp.callback_query(lambda c: c.data == "set_exchanges", StateFilter(FilterStates.waiting_for_choice))
async def ask_exchanges(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Bybit", callback_data="exch_Bybit")],
        [InlineKeyboardButton("Binance", callback_data="exch_Binance")],
        [InlineKeyboardButton("Bitget", callback_data="exch_Bitget")],
        [InlineKeyboardButton("Готово", callback_data="exch_done")]
    ])
    await callback.message.edit_text("Выберите биржи (нажмите для переключения):", reply_markup=kb)
    await state.set_state(FilterStates.waiting_exchanges)

@dp.callback_query(lambda c: c.data.startswith("exch_"), StateFilter(FilterStates.waiting_exchanges))
async def toggle_exchange(callback: CallbackQuery, state: FSMContext):
    exch = callback.data.split("_", 1)[1]
    await toggle_filter_list_item(callback.from_user.id, 'exchanges', exch)
    await ask_exchanges(callback, state)

@dp.callback_query(lambda c: c.data == "exch_done", StateFilter(FilterStates.waiting_exchanges))
async def exchanges_done(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✅ Биржи сохранены.")
    await filter_menu(callback, state)

# Finish filter
@dp.callback_query(lambda c: c.data == "finish_filter", StateFilter(FilterStates.waiting_for_choice))
async def finish_filter(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Фильтр обновлён. Возвращаемся в меню.")
    await state.clear()
    await cmd_start(callback.message)
