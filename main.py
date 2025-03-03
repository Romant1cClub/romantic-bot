import random
import string
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
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
        "subscribe": "Оформите подписку: {BOOSTY_URL}",
        "get_code": "Получить код",
        "code_prompt": "Введите код доступа:",
        "code_success": "🎉 Код подтверждён! Доступ к сценариям открыт.",
        "code_fail": "❌ Неверный код или код уже использован.",
        "scenario": "📖 Вот ваш сценарий: ...",
        "not_subscribed": "❌ У вас нет доступа к сценариям. Оформите подписку."
    },
    "en": {
        "welcome": "💫 Welcome!",
        "subscribe": "Subscribe here: {BOOSTY_URL}",
        "get_code": "Get code",
        "code_prompt": "Enter access code:",
        "code_success": "🎉 Code confirmed! Access to scenarios granted.",
        "code_fail": "❌ Invalid code or code already used.",
        "scenario": "📖 Here is your scenario: ...",
        "not_subscribed": "❌ You don't have access to scenarios. Please subscribe."
    }
}

# Хранилище данных
user_codes = {}  # {user_id: код}
subscribed_users = set()  # Множество подписанных пользователей

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

# Генерация уникального кода
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

# Получение языка пользователя
def get_user_language(update: Update):
    return update.effective_user.language_code or "en"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_language = get_user_language(update)
    keyboard = [
        [InlineKeyboardButton(messages[user_language]["get_code"], callback_data='get_code')],
        [InlineKeyboardButton(messages[user_language]["subscribe"], url=BOOSTY_URL)]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(messages[user_language]["welcome"], reply_markup=reply_markup)

# Обработка нажатия кнопки "Получить код"
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    user_language = get_user_language(update)

    if user_id not in subscribed_users:
        await query.edit_message_text(messages[user_language]["not_subscribed"])
        return

    if user_id in user_codes:
        await query.edit_message_text(f"📌 Ваш код уже сгенерирован: {user_codes[user_id]}")
    else:
        new_code = generate_code()
        user_codes[user_id] = new_code
        await query.edit_message_text(
            f"✅ Ваш уникальный код: {new_code}\n\n"
            f"{messages[user_language]['code_prompt']}"
        )

# Команда /code
async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)
    user_code = ' '.join(context.args)

    if user_id in user_codes and user_codes[user_id] == user_code:
        await update.message.reply_text(messages[user_language]["code_success"])
        del user_codes[user_id]
    else:
        await update.message.reply_text(messages[user_language]["code_fail"])

# Команда /scenario
async def scenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_language = get_user_language(update)

    if user_id not in subscribed_users:
        await update.message.reply_text(messages[user_language]["not_subscribed"])
        return

    await update.message.reply_text(messages[user_language]["scenario"])

# Обработка ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")
    user_language = get_user_language(update)
    await update.message.reply_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

# Основная функция
def main():
    init_db()  # Инициализация базы данных
    application = Application.builder().token(TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(CommandHandler("code", check_code))
    application.add_handler(CommandHandler("scenario", scenario))

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
