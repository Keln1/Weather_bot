from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz
from database import get_user_settings, get_user_notify_days
from weather_api import get_current_weather, get_forecast_5days
from aiogram import Bot

scheduler = AsyncIOScheduler()


async def send_daily_weather(bot, user_id: int):
    """Надсилає щоденний прогноз погоди користувачу."""
    city, notify_time = get_user_settings(user_id)
    if not city:
        return
    
    # Перевіряємо, чи потрібно надсилати сповіщення сьогодні
    notify_days = get_user_notify_days(user_id)
    if notify_days:
        today = datetime.now(pytz.timezone('Europe/Kiev')).isoweekday()
        if today not in notify_days:
            return
    
    try:
        # Отримуємо прогноз погоди
        weather_text = await get_current_weather(city)
        forecast_text = await get_forecast_5days(city)
        
        # Надсилаємо повідомлення
        await bot.send_message(
            user_id,
            f"🌅 *Доброго ранку!*\n\n"
            f"Ось ваш щоденний прогноз погоди:\n\n"
            f"{weather_text}\n\n"
            f"{forecast_text}"
        )
    except Exception as e:
        print(f"Помилка при надсиланні сповіщення користувачу {user_id}: {e}")


def setup_notifications(bot):
    """Налаштовує сповіщення для всіх користувачів."""
    from database import get_all_users
    
    # Отримуємо всіх користувачів
    users = get_all_users()
    
    # Налаштовуємо сповіщення для кожного користувача
    for user_id, city, notify_time, notify_days in users:
        if notify_time:
            try:
                # Видаляємо старе завдання, якщо воно існує
                job_id = f"user_{user_id}"
                try:
                    scheduler.remove_job(job_id)
                except:
                    pass
                
                # Створюємо нове завдання
                hour, minute = notify_time.split(":")
                scheduler.add_job(
                    send_daily_weather,
                    trigger=CronTrigger(hour=int(hour), minute=int(minute)),
                    args=[bot, user_id],
                    id=job_id,
                    replace_existing=True
                )
            except Exception as e:
                print(f"Помилка при налаштуванні сповіщень для користувача {user_id}: {e}")


def start_scheduler(bot):
    """Запускає планувальник."""
    setup_notifications(bot)
    scheduler.start()
