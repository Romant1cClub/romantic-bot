import random
import string
import sqlite3
import logging
import requests
from bs4 import BeautifulSoup
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
        "no_events": "❌ Нет доступных мероприятий."
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
        "no_events": "❌ No events available."
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
        "no_events": "❌ Немає доступних заходів."
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
    conn.commit()
    conn.close()

# Добавление пользователя в базу данных
def add_user(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id) VALUES (?)', (user_id,))
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

# Парсинг афиш
def parse_events(city="Москва"):
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
def generate_scenario(events):
    scenario = "📅 Ваш план на день:\n\n"
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

# Обработка нажатия кнопки "Получить код"
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)

    if not check_subscription(user_id):
        await update.message.reply_text(messages[user_language]["not_subscribed"])
        return

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT code FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0]:
        await update.message.reply_text(f"📌 Ваш код уже сгенерирован: {result[0]}")
    else:
        new_code = generate_code()
        update_code(user_id, new_code)
        await update.message.reply_text(f"✅ Ваш уникальный код: {new_code}\n\n{messages[user_language]['code_prompt']}")

# Команда /scenario
async def scenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)

    if not check_subscription(user_id):
        await update.message.reply_text(messages[user_language]["not_subscribed"])
        return

    # Парсим афиши
    events = parse_events(city="Москва")  # Можно добавить выбор города

    if not events:
        await update.message.reply_text(messages[user_language]["no_events"])
        return

    # Генерируем сценарий
    scenario_text = generate_scenario(events)
    await update.message.reply_text(scenario_text)

# Основная функция
def main():
    init_db()  # Инициализация базы данных
    application = Application.builder().token(TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("Получить код|Get code|Отримати код"), button_handler))
    application.add_handler(CommandHandler("scenario", scenario))

    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
