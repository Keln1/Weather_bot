# Погодний Telegram Бот 🌤

Цей бот дозволяє отримувати інформацію про поточну погоду та прогноз на 5 днів для будь-якого міста.

## Функціональність

- 🌤 Отримання поточної погоди
- 📅 Прогноз погоди на 5 днів
- ⏰ Щоденні сповіщення про погоду
- 🏙 Можливість зміни міста
- 🌍 Підтримка української мови

## Встановлення

1. Клонуйте репозиторій:
```bash
git clone https://github.com/your-username/weather-bot.git
cd weather-bot
```

2. Встановіть залежності:
```bash
pip install -r requirements.txt
```

3. Створіть файл `config.py` на основі `config.example.py`:
```bash
cp config.example.py config.py
```

4. Відредагуйте `config.py` та додайте свої ключі:
- Отримайте токен бота у [@BotFather](https://t.me/BotFather)
- Отримайте API ключ на [OpenWeatherMap](https://openweathermap.org/api)

5. Запустіть бота:
```bash
python main.py
```

## Використання

1. Почніть чат з ботом
2. Відправте команду `/start`
3. Використовуйте кнопки меню для навігації

## Технічні деталі

- Python 3.7+
- aiogram 3.x
- APScheduler
- SQLite3
- OpenWeatherMap API 