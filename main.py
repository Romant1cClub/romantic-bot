import random
import string
import sqlite3
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
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
        "choose_city": "Выберите город:",
        "city_selected": "Выбран город: {}",
        "settings": "⚙️ Ваши настройки:\n📍 Локация: {}\n⏰ Время: {}\n👥 С кем: {}\n🎭 Настроение: {}\n📝 Нюансы: {}",
        "location_updated": "📍 Локация изменена на: {}",
        "time_updated": "⏰ Время изменено на: {}",
        "company_updated": "👥 Компания изменена на: {}",
        "mood_updated": "🎭 Настроение изменено на: {}",
        "notes_updated": "📝 Нюансы изменены на: {}"
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
        "choose_city": "Choose city:",
        "city_selected": "Selected city: {}",
        "settings": "⚙️ Your settings:\n📍 Location: {}\n⏰ Time: {}\n👥 Company: {}\n🎭 Mood: {}\n📝 Notes: {}",
        "location_updated": "📍 Location updated to: {}",
        "time_updated": "⏰ Time updated to: {}",
        "company_updated": "👥 Company updated to: {}",
        "mood_updated": "🎭 Mood updated to: {}",
        "notes_updated": "📝 Notes updated to: {}"
    },
    "uk": {
        "welcome": "💫 Ласкаво просимо!",
        "subscribe": "Оформити підписку",
        "get_code": "Отримати код",
        "code_prompt": "Введіть код доступу:",
        "code_success": "🎉 Код підтверджено! Доступ до сценаріїв відкрито.",
        "code_fail": "❌ Невірний код або код вже використано.",
        "scenario": "📖 Ось ваш сценарій: ...",
        "not_subscribed": "❌ У вас немає доступу до сценаріїв. Оформіть підписку.",
        "no_events": "❌ Немає доступних заходів.",
        "choose_city": "Виберіть місто:",
        "city_selected": "Обране місто: {}",
        "settings": "⚙️ Ваші налаштування:\n📍 Локація: {}\n⏰ Час: {}\n👥 З ким: {}\n🎭 Настрій: {}\n📝 Нюанси: {}",
        "location_updated": "📍 Локація змінена на: {}",
        "time_updated": "⏰ Час змінено на: {}",
        "company_updated": "👥 Компанія змінена на: {}",
        "mood_updated": "🎭 Настрій змінено на: {}",
        "notes_updated": "📝 Нюанси змінено на: {}"
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
            location TEXT DEFAULT 'Польша',
            time TEXT DEFAULT 'Вечер',
            company TEXT DEFAULT 'Друзья',
            mood TEXT DEFAULT 'Веселье',
            notes TEXT DEFAULT '',
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

# Генерация уникального кода
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Получение языка пользователя
def get_user_language(update: Update):
    lang = update.effective_user.language_code
    return lang if lang in messages else "en"

# Получение настроек пользователя
def get_user_settings(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT location, time, company, mood, notes FROM user_settings WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "location": result[0],
            "time": result[1],
            "company": result[2],
            "mood": result[3],
            "notes": result[4]
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
    location = user_settings.get("location", "Польша")
    time = user_settings.get("time", "Вечер")
    company = user_settings.get("company", "Друзья")
    mood = user_settings.get("mood", "Веселье")
    notes = user_settings.get("notes", "")

    scenario = (
        f"📅 Ваш план на {time} в {location}:\n\n"
        f"👥 С кем: {company}\n"
        f"🎭 Настроение: {mood}\n"
        f"📝 Нюансы: {notes}\n\n"
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

# Команда /settings
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)

    settings = get_user_settings(user_id)
    if settings:
        settings_text = messages[user_language]["settings"].format(
            settings["location"], settings["time"], settings["company"], settings["mood"], settings["notes"]
        )
    else:
        settings_text = "Настройки не найдены. Используйте команды для настройки."

    await update.message.reply_text(settings_text)

# Команда /set_location
async def set_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)
    location = ' '.join(context.args)

    update_user_settings(user_id, "location", location)
    await update.message.reply_text(messages[user_language]["location_updated"].format(location))

# Команда /set_time
async def set_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)
    time = ' '.join(context.args)

    update_user_settings(user_id, "time", time)
    await update.message.reply_text(messages[user_language]["time_updated"].format(time))

# Команда /set_company
async def set_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)
    company = ' '.join(context.args)

    update_user_settings(user_id, "company", company)
    await update.message.reply_text(messages[user_language]["company_updated"].format(company))

# Команда /set_mood
async def set_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)
    mood = ' '.join(context.args)

    update_user_settings(user_id, "mood", mood)
    await update.message.reply_text(messages[user_language]["mood_updated"].format(mood))

# Команда /set_notes
async def
