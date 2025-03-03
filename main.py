import random
import string
import sqlite3
import logging
import requests
from bs4 import BeautifulSoup
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os

# Загружаем переменные из .env
load_dotenv()

# Получаем переменные окружения
TOKEN = os.getenv('TOKEN')  # Токен бота
BOOSTY_URL = os.getenv('BOOSTY_URL')  # Ссылка на Boosty

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="bot.log"
)
logger = logging.getLogger(__name__)

# Локализация
messages = {
    "ru": {
        "welcome": "💫 Добро пожаловать!",
        "subscribe": "Оформите подписку",
        "get_code": "Получить код",
        "code_prompt": "Введите код доступа:",
        "code_success": "🎉 Код подтверждён! Доступ к сценариям открыт.",
        "code_fail": "❌ Неверный код или код уже использован.",
        "scenario": "📖 Вот ваш сценарий: ...",
        "not_subscribed": "❌ У вас нет доступа к сценариям. Оформите подписку.",
        "no_events": "❌ Нет доступных мероприятий.",
        "choose_city": "Введите город:",
        "city_selected": "Выбран город: {}",
        "choose_time": "Введите время (например, 18:00):",
        "time_selected": "Выбрано время: {}",
        "choose_mood": "Выберите настроение:",
        "mood_selected": "Выбрано настроение: {}",
        "choose_group_size": "Введите количество человек:",
        "group_size_selected": "Выбрано количество человек: {}",
        "settings": "⚙️ Ваши настройки:\n📍 Город: {}\n⏰ Время: {}\n🎭 Настроение: {}\n👥 Количество человек: {}",
        "scenario_generated": "📅 Ваш сценарий:\n\n{}"
    },
    "en": {
        "welcome": "💫 Welcome!",
        "subscribe": "Subscribe",
        "get_code": "Get code",
        "code_prompt": "Enter access code:",
        "code_success": "🎉 Code confirmed! Access to scenarios granted.",
        "code_fail": "❌ Invalid code or code already used.",
        "scenario": "📖 Here is your scenario: ...",
        "not_subscribed": "❌ You don't have access to scenarios. Please subscribe.",
        "no_events": "❌ No events available.",
        "choose_city": "Enter city:",
        "city_selected": "Selected city: {}",
        "choose_time": "Enter time (e.g., 18:00):",
        "time_selected": "Selected time: {}",
        "choose_mood": "Choose mood:",
        "mood_selected": "Selected mood: {}",
        "choose_group_size": "Enter number of people:",
        "group_size_selected": "Selected number of people: {}",
        "settings": "⚙️ Your settings:\n📍 City: {}\n⏰ Time: {}\n🎭 Mood: {}\n👥 Number of people: {}",
        "scenario_generated": "📅 Your scenario:\n\n{}"
    }
}

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            code TEXT,
            is_subscribed INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            city TEXT DEFAULT 'Польша',
            time TEXT DEFAULT '18:00',
            mood TEXT DEFAULT 'Веселье',
            group_size INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    conn.commit()
    conn.close()

# Добавление пользователя в базу данных
def add_user(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
    cursor.execute('INSERT OR IGNORE INTO user_settings (user_id) VALUES (?)', (user_id,))
    conn.commit()
    conn.close()

# Обновление кода пользователя
def update_code(user_id, code):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET code = ? WHERE user_id = ?', (code, user_id))
    conn.commit()
    conn.close()

# Проверка подписки пользователя
def check_subscription(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT is_subscribed FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else False

# Получение настроек пользователя
def get_user_settings(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT city, time, mood, group_size FROM user_settings WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "city": result[0],
            "time": result[1],
            "mood": result[2],
            "group_size": result[3]
        }
    return None

# Обновление настроек пользователя
def update_user_settings(user_id, key, value):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute(f'UPDATE user_settings SET {key} = ? WHERE user_id = ?', (value, user_id))
    conn.commit()
    conn.close()

# Парсинг афиш
def parse_events(city="Польша"):
    url = f"https://example.com/afisha/{city}"  # Замените на реальный URL
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    events = []
    for event in soup.find_all('div', class_='event'):  # Замените на реальный селектор
        title = event.find('h2').text.strip()
        date = event.find('span', class_='date').text.strip()
        location = event.find('span', class_='location').text.strip()
        events.append({
            "title": title,
            "date": date,
            "location": location
        })
    return events

# Генерация сценария
def generate_scenario(events, user_settings):
    city = user_settings.get("city", "Польша")
    time = user_settings.get("time", "18:00")
    mood = user_settings.get("mood", "Веселье")
    group_size = user_settings.get("group_size", 1)

    scenario = (
        f"📅 Ваш план на {time} в {city}:\n\n"
        f"🎭 Настроение: {mood}\n"
        f"👥 Количество человек: {group_size}\n\n"
        "Мероприятия:\n"
    )

    for event in events:
        scenario += f"🎭 {event['title']}\n"
        scenario += f"📅 Дата: {event['date']}\n"
        scenario += f"📍 Место: {event['location']}\n\n"

    return scenario

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_language = get_user_language(update)
    add_user(update.effective_user.id)

    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton(messages[user_language]["get_code"])],
        [KeyboardButton(messages[user_language]["subscribe"])]
    ], resize_keyboard=True)

    await update.message.reply_text(messages[user_language]["welcome"], reply_markup=keyboard)

# Команда /set_city
async def set_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)
    city = ' '.join(context.args)

    update_user_settings(user_id, "city", city)
    await update.message.reply_text(messages[user_language]["city_selected"].format(city))

# Команда /set_time
async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)
    time = ' '.join(context.args)

    update_user_settings(user_id, "time", time)
    await update.message.reply_text(messages[user_language]["time_selected"].format(time))

# Команда /set_mood
async def set_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)
    mood = ' '.join(context.args)

    update_user_settings(user_id, "mood", mood)
    await update.message.reply_text(messages[user_language]["mood_selected"].format(mood))

# Команда /set_group_size
async def set_group_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)
    group_size = ' '.join(context.args)

    update_user_settings(user_id, "group_size", group_size)
    await update.message.reply_text(messages[user_language]["group_size_selected"].format(group_size))

# Команда /settings
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)

    settings = get_user_settings(user_id)
    if settings:
        settings_text = messages[user_language]["settings"].format(
            settings["city"], settings["time"], settings["mood"], settings["group_size"]
        )
    else:
        settings_text = "Настройки не найдены. Используйте команды для настройки."

    await update.message.reply_text(settings_text)

# Команда /scenario
async def scenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)

    if not check_subscription(user_id):
        await update.message.reply_text(messages[user_language]["not_subscribed"])
        return

    settings = get_user_settings(user_id)
    if not settings:
        await update.message.reply_text("❌ Настройки не найдены. Используйте команды для настройки.")
        return

    events = parse_events(settings["city"])
    if not events:
        await update.message.reply_text(messages[user_language]["no_events"])
        return

    scenario_text = generate_scenario(events, settings)
    await update.message.reply_text(messages[user_language]["scenario_generated"].format(scenario_text))

# Основная функция
def main():
    init_db()  # Инициализация базы данных
    application = Application.builder().token(TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("set_city", set_city))
    application.add_handler(CommandHandler("set_time", set_time))
    application.add_handler(CommandHandler("set_mood", set_mood))
    application.add_handler(CommandHandler("set_group_size", set_group_size))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CommandHandler("scenario", scenario))

    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
