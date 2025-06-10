import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import set_city, set_notify_time, get_user_settings
from weather_api import get_current_weather, get_forecast_5days
from scheduler import scheduler, send_daily_weather

router = Router()


# Состояния FSM
class CityState(StatesGroup):
    waiting_for_city = State()


class NotifyTimeState(StatesGroup):
    waiting_for_time = State()


# Клавиатуры
def main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌦 Дізнатися погоду", callback_data="menu_weather")],
        [InlineKeyboardButton(text="🏙 Встановити місто", callback_data="menu_set_city")],
        [InlineKeyboardButton(text="⏰ Встановити сповіщення", callback_data="menu_set_notify")]
    ])
    return kb


def weather_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌤 Погода зараз", callback_data="weather_current"),
         InlineKeyboardButton(text="📅 Прогноз на 5 днів", callback_data="weather_5days")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_main")]
    ])
    return kb


# Хендлеры команд
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "👋 *Вітаю!*\n\n"
        "Я — ваш погодний бот, який допоможе дізнатися поточну погоду 🌤 "
        "та отримати прогноз на 5 днів 📅.\n\n"
        "Також можу надсилати щоденні сповіщення з інформацією про погоду ⏰.\n\n"
        "Виберіть, що хочете зробити:"
    )
    await message.answer(welcome_text, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "back_to_main")
async def callback_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Виберіть дію:", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu_weather")
async def callback_menu_weather(call: CallbackQuery):
    await call.message.edit_text("Виберіть, яку погоду показати:", reply_markup=weather_menu_keyboard())


@router.callback_query(F.data == "menu_set_city")
async def callback_menu_set_city(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Введіть назву міста (наприклад: Київ, London, Paris)")
    await state.set_state(CityState.waiting_for_city)


@router.callback_query(F.data == "menu_set_notify")
async def callback_menu_set_notify(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text("Вкажіть час у форматі HH:MM (24-годинний). Приклад: 09:00")
    await state.set_state(NotifyTimeState.waiting_for_time)


@router.callback_query(F.data == "weather_current")
async def callback_weather_current(call: CallbackQuery):
    user_id = call.from_user.id
    city, _ = get_user_settings(user_id)
    if not city:
        await call.message.edit_text("Спочатку потрібно встановити місто!", reply_markup=main_menu_keyboard())
        return
    weather_text = await get_current_weather(city)
    await call.message.edit_text(text=weather_text, parse_mode="Markdown", reply_markup=weather_menu_keyboard())


@router.callback_query(F.data == "weather_5days")
async def callback_weather_5days(call: CallbackQuery):
    user_id = call.from_user.id
    city, _ = get_user_settings(user_id)
    if not city:
        await call.message.edit_text("Спочатку потрібно встановити місто!", reply_markup=main_menu_keyboard())
        return
    forecast_text = await get_forecast_5days(city)
    await call.message.edit_text(text=forecast_text, parse_mode="Markdown", reply_markup=weather_menu_keyboard())


@router.message(CityState.waiting_for_city)
async def city_input(message: Message, state: FSMContext):
    city = message.text.strip()
    set_city(message.from_user.id, city)
    await message.answer(f"Місто *{city.title()}* збережено! Тепер можна дізнатися погоду.",
                         reply_markup=main_menu_keyboard())
    await state.clear()


@router.message(NotifyTimeState.waiting_for_time)
async def notify_time_input(message: Message, state: FSMContext):
    time_str = message.text.strip()
    pattern = r"^([0-1]\d|2[0-3]):([0-5]\d)$"
    if not re.match(pattern, time_str):
        await message.answer("Невірний формат часу. Спробуйте ще раз (приклад: 09:00).")
        return
    set_notify_time(message.from_user.id, time_str)
    job_id = f"user_{message.from_user.id}"
    try:
        scheduler.remove_job(job_id)
    except:
        pass
    hour, minute = time_str.split(":")
    scheduler.add_job(
        send_daily_weather,
        trigger='cron',
        hour=int(hour),
        minute=int(minute),
        args=[message.bot, message.from_user.id],
        id=job_id,
        replace_existing=True
    )
    await message.answer(f"Сповіщення встановлено на {time_str} щодня!", reply_markup=main_menu_keyboard())
    await state.clear()
