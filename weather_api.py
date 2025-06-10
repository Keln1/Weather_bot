import aiohttp
from config import OPENWEATHER_API_KEY, OPENWEATHER_BASE_URL
from datetime import datetime
import pytz

def get_weather_emoji(weather_id: int) -> str:
    """Повертає емодзі відповідно до погодних умов."""
    if weather_id >= 200 and weather_id < 300:
        return "⛈"  # Гроза
    elif weather_id >= 300 and weather_id < 400:
        return "🌧"  # Мряка
    elif weather_id >= 500 and weather_id < 600:
        return "🌧"  # Дощ
    elif weather_id >= 600 and weather_id < 700:
        return "❄️"  # Сніг
    elif weather_id >= 700 and weather_id < 800:
        return "🌫"  # Туман
    elif weather_id == 800:
        return "☀️"  # Ясно
    elif weather_id > 800:
        return "☁️"  # Хмарно
    return "🌤"

def format_wind_direction(degrees: float) -> str:
    """Конвертує градуси в напрямок вітру."""
    directions = ['Пн', 'ПнСх', 'Сх', 'ПдСх', 'Пд', 'ПдЗх', 'Зх', 'ПнЗх']
    index = round(degrees / 45) % 8
    return directions[index]

async def get_current_weather(city: str, lang: str = "uk") -> str:
    """Запитує поточну погоду в місті."""
    url = f"{OPENWEATHER_BASE_URL}/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": lang
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                data = await response.json()
                if response.status != 200:
                    return f"⚠️ Помилка: {data.get('message', 'Не вдалося отримати погоду')}"
                
                weather_id = data["weather"][0]["id"]
                weather_emoji = get_weather_emoji(weather_id)
                weather_desc = data["weather"][0]["description"].capitalize()
                temp = round(data["main"]["temp"])
                feels_like = round(data["main"]["feels_like"])
                humidity = data["main"]["humidity"]
                pressure = round(data["main"]["pressure"] * 0.750062)  # Конвертуємо в мм рт.ст.
                wind_speed = round(data["wind"]["speed"], 1)
                wind_deg = data["wind"]["deg"]
                wind_dir = format_wind_direction(wind_deg)
                clouds = data["clouds"]["all"]
                
                # Конвертуємо час сходу/заходу сонця
                sunrise = datetime.fromtimestamp(data["sys"]["sunrise"])
                sunset = datetime.fromtimestamp(data["sys"]["sunset"])
                timezone = pytz.timezone('Europe/Kiev')
                sunrise = sunrise.astimezone(timezone)
                sunset = sunset.astimezone(timezone)
                
                return (
                    f"{weather_emoji} *Погода в місті {city.title()}*\n\n"
                    f"*{weather_desc}*\n\n"
                    f"🌡 *Температура:*\n"
                    f"• Зараз: {temp}°C\n"
                    f"• Відчувається як: {feels_like}°C\n\n"
                    f"💨 *Вітер:*\n"
                    f"• Швидкість: {wind_speed} м/с\n"
                    f"• Напрямок: {wind_dir}\n\n"
                    f"💧 *Вологість:* {humidity}%\n"
                    f"☁️ *Хмарність:* {clouds}%\n"
                    f"🌡 *Тиск:* {pressure} мм рт.ст.\n\n"
                    f"🌅 *Схід сонця:* {sunrise.strftime('%H:%M')}\n"
                    f"🌇 *Захід сонця:* {sunset.strftime('%H:%M')}\n"
                )
    except aiohttp.ClientError:
        return "⚠️ Помилка при підключенні до сервісу погоди."

async def get_forecast_5days(city: str, lang: str = "uk") -> str:
    """Запитує 5-денний прогноз погоди та групує дані за днями."""
    url = f"{OPENWEATHER_BASE_URL}/forecast"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
        "lang": lang
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                data = await response.json()
                if response.status != 200:
                    return f"⚠️ Помилка: {data.get('message', 'Не вдалося отримати прогноз')}"
                
                forecast_list = data.get("list", [])
                if not forecast_list:
                    return "⚠️ Немає даних прогнозу."

                from collections import defaultdict
                grouped = defaultdict(list)
                for entry in forecast_list:
                    date = entry["dt_txt"].split(" ")[0]
                    grouped[date].append(entry)

                days = sorted(grouped.keys())
                from datetime import datetime
                lines = [f"📅 *Прогноз погоди на 5 днів у {city.title()}*\n"]
                
                for day in days[:5]:
                    entries = grouped[day]
                    chosen = next((entry for entry in entries if "12:00:00" in entry["dt_txt"]), entries[0])
                    dt_obj = datetime.strptime(day, "%Y-%m-%d")
                    formatted_date = dt_obj.strftime("%d.%m.%Y")
                    weather_id = chosen["weather"][0]["id"]
                    weather_emoji = get_weather_emoji(weather_id)
                    desc = chosen["weather"][0]["description"].capitalize()
                    temp = round(chosen["main"]["temp"])
                    temp_min = round(chosen["main"]["temp_min"])
                    temp_max = round(chosen["main"]["temp_max"])
                    wind_speed = round(chosen["wind"]["speed"], 1)
                    wind_deg = chosen["wind"]["deg"]
                    wind_dir = format_wind_direction(wind_deg)
                    humidity = chosen["main"]["humidity"]
                    clouds = chosen["clouds"]["all"]
                    
                    lines.append(
                        f"\n{weather_emoji} *{formatted_date}*\n"
                        f"*{desc}*\n"
                        f"🌡 Температура: {temp}°C\n"
                        f"   Мін: {temp_min}°C, Макс: {temp_max}°C\n"
                        f"💨 Вітер: {wind_speed} м/с ({wind_dir})\n"
                        f"💧 Вологість: {humidity}%\n"
                        f"☁️ Хмарність: {clouds}%\n"
                        f"{'─' * 20}"
                    )
                return "\n".join(lines)
    except aiohttp.ClientError:
        return "⚠️ Помилка при підключенні до сервісу прогнозу погоди."
