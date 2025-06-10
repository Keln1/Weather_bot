import re
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

from database import set_city, set_notify_time, get_user_settings, get_all_users
from weather_api import get_current_weather, get_forecast_5days
from scheduler import scheduler, send_daily_weather

router = Router()


# Состояния FSM
class CityState(StatesGroup):
    waiting_for_city = State()


class NotifyTimeState(StatesGroup):
    waiting_for_time = State()


class NotifyDaysState(StatesGroup):
    waiting_for_days = State()


# Клавиатуры
def main_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌦 Погода", callback_data="menu_weather")],
        [InlineKeyboardButton(text="🏙 Змінити місто", callback_data="menu_set_city")],
        [InlineKeyboardButton(text="⏰ Сповіщення", callback_data="menu_notifications")]
    ])
    return kb


def weather_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌤 Зараз", callback_data="weather_current"),
         InlineKeyboardButton(text="📅 5 днів", callback_data="weather_5days")],
        [InlineKeyboardButton(text="⬅ Назад", callback_data="back_to_main")]
    ])
    return kb


def notifications_menu_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏰ Час сповіщень", callback_data="menu_set_notify")],
        [InlineKeyboardButton(text="📅 Дні сповіщень", callback_data="menu_set_days")],
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
        "🔹 *Основні можливості:*\n"
        "• Поточна погода з детальною інформацією\n"
        "• Прогноз погоди на 5 днів\n"
        "• Щоденні сповіщення про погоду\n"
        "• Гнучкі налаштування часу та днів сповіщень\n\n"
        "Виберіть, що хочете зробити:"
    )
    await message.answer(welcome_text, reply_markup=main_menu_keyboard())


@router.message(Command("weather"))
async def cmd_weather(message: Message):
    user_id = message.from_user.id
    city, _ = get_user_settings(user_id)
    if not city:
        await message.answer("Спочатку потрібно встановити місто!", reply_markup=main_menu_keyboard())
        return
    weather_text = await get_current_weather(city)
    await message.answer(weather_text, reply_markup=weather_menu_keyboard())


@router.callback_query(F.data == "back_to_main")
async def callback_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Виберіть дію:", reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "menu_weather")
async def callback_menu_weather(call: CallbackQuery):
    await call.message.edit_text("Виберіть, яку погоду показати:", reply_markup=weather_menu_keyboard())


@router.callback_query(F.data == "menu_set_city")
async def callback_menu_set_city(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "🏙 *Введіть назву міста*\n\n"
        "Наприклад:\n"
        "• Київ\n"
        "• Львів\n"
        "• Харків\n"
        "• Одеса\n\n"
        "Можна вводити міста українською або англійською мовою."
    )
    await state.set_state(CityState.waiting_for_city)


@router.callback_query(F.data == "menu_notifications")
async def callback_menu_notifications(call: CallbackQuery):
    await call.message.edit_text("🔔 *Налаштування сповіщень*", reply_markup=notifications_menu_keyboard())


@router.callback_query(F.data == "menu_set_notify")
async def callback_menu_set_notify(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "⏰ *Вкажіть час сповіщень*\n\n"
        "Формат: HH:MM (24-годинний)\n"
        "Наприклад:\n"
        "• 09:00\n"
        "• 18:30\n\n"
        "Бот буде надсилати прогноз погоди щодня в зазначений час."
    )
    await state.set_state(NotifyTimeState.waiting_for_time)


@router.callback_query(F.data == "menu_set_days")
async def callback_menu_set_days(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        "📅 *Вкажіть дні тижня для сповіщень*\n\n"
        "Введіть дні через кому (1-7):\n"
        "1 - Понеділок\n"
        "2 - Вівторок\n"
        "3 - Середа\n"
        "4 - Четвер\n"
        "5 - П'ятниця\n"
        "6 - Субота\n"
        "7 - Неділя\n\n"
        "Наприклад: 1,2,3,4,5"
    )
    await state.set_state(NotifyDaysState.waiting_for_days)


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
    await message.answer(
        f"✅ Місто *{city.title()}* збережено!\n\n"
        f"Тепер ви можете дізнатися погоду для цього міста.",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()


@router.message(NotifyTimeState.waiting_for_time)
async def notify_time_input(message: Message, state: FSMContext):
    time_str = message.text.strip()
    pattern = r"^([0-1]\d|2[0-3]):([0-5]\d)$"
    if not re.match(pattern, time_str):
        await message.answer(
            "❌ Невірний формат часу!\n\n"
            "Будь ласка, використовуйте формат HH:MM\n"
            "Наприклад: 09:00"
        )
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
    
    await message.answer(
        f"✅ Сповіщення встановлено!\n\n"
        f"Бот буде надсилати прогноз погоди щодня о {time_str}.",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()


@router.message(NotifyDaysState.waiting_for_days)
async def notify_days_input(message: Message, state: FSMContext):
    days_str = message.text.strip()
    try:
        days = [int(d.strip()) for d in days_str.split(",")]
        if not all(1 <= d <= 7 for d in days):
            raise ValueError
    except ValueError:
        await message.answer(
            "❌ Невірний формат днів!\n\n"
            "Будь ласка, введіть числа від 1 до 7 через кому.\n"
            "Наприклад: 1,2,3,4,5"
        )
        return
    
    # Тут можна додати логіку збереження днів у базу даних
    days_names = {
        1: "Понеділок",
        2: "Вівторок",
        3: "Середа",
        4: "Четвер",
        5: "П'ятниця",
        6: "Субота",
        7: "Неділя"
    }
    days_text = ", ".join(days_names[d] for d in sorted(days))
    
    await message.answer(
        f"✅ Дні сповіщень встановлено!\n\n"
        f"Бот буде надсилати прогноз погоди в такі дні:\n"
        f"{days_text}",
        reply_markup=main_menu_keyboard()
    )
    await state.clear()
