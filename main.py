import random
import string
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Оформить подписку", url=BOOSTY_URL)],
        [InlineKeyboardButton("Получить код", callback_data='get_code')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("💫 Добро пожаловать!", reply_markup=reply_markup)

# Обработка нажатия кнопки "Получить код"
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in subscribed_users:
        await query.edit_message_text("❌ Вы не подписаны. Пожалуйста, оформите подписку.")
        return

    if user_id in user_codes:
        await query.edit_message_text(f"📌 Ваш код уже сгенерирован: {user_codes[user_id]}")
    else:
        new_code = generate_code()
        user_codes[user_id] = new_code
        await query.edit_message_text(
            f"✅ Ваш уникальный код: {new_code}\n\n"
            "Введите его командой: /code <ВАШ_КОД>"
        )

# Команда /code
async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_code = ' '.join(context.args)

    if user_id in user_codes and user_codes[user_id] == user_code:
        await update.message.reply_text(
            "🎉 Код подтверждён! Доступ к сценариям открыт. Введите /scenario, чтобы начать."
        )
        del user_codes[user_id]
    else:
        await update.message.reply_text("❌ Неверный код или код уже использован.")

# Команда /scenario
async def scenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in subscribed_users:
        await update.message.reply_text("❌ У вас нет доступа к сценариям. Оформите подписку.")
        return

    # Пример сценария
    await update.message.reply_text("📖 Вот ваш сценарий: ...")

# Обработка ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")
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
