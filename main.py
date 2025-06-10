import logging
import asyncio
from aiogram.client.bot import Bot, DefaultBotProperties
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from database import init_db
from config import BOT_TOKEN
from handlers import router
from scheduler import start_scheduler

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Ініціалізація бази даних
        init_db()
        logger.info("База даних ініціалізована")

        # Створення бота та диспетчера
        bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="Markdown"))
        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(router)
        logger.info("Бот та диспетчер створені")

        # Запуск планувальника
        start_scheduler(bot)
        logger.info("Планувальник запущено")

        # Запуск бота
        logger.info("Бот запущено")
        await dp.start_polling(bot)

    except Exception as e:
        logger.error(f"Помилка при запуску бота: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот зупинено")
    except Exception as e:
        logger.error(f"Критична помилка: {e}")
