import random
import string
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Вставьте свои значения
TOKEN = '8179789266:AAFiXJ-B-32F2GfZxOghM8qiHOtnRXXE5Sc'  # Замените на токен вашего бота
BOOSTY_URL = 'https://boosty.to/romant1cclub_bot'  # Замените на вашу ссылку Boosty

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

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💫 Добро пожаловать! Чтобы получить доступ к сценариям, "
        f"оформите подписку: {BOOSTY_URL}\n\n"
        "После оплаты отправьте команду: /getcode"
    )

# Команда /getcode
async def get_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)

    if not check_subscription(user_id):
        await update.message.reply_text("❌ Вы не подписаны. Пожалуйста, оформите подписку.")
        return

    new_code = generate_code()
    update_code(user_id, new_code)
    await update.message.reply_text(
        f"✅ Ваш уникальный код: {new_code}\n\n"
        "Введите его командой: /code <ВАШ_КОД>"
    )

# Команда /code
async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_code = ' '.join(context.args)

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT code FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0] == user_code:
        await update.message.reply_text("🎉 Код подтверждён! Доступ к сценариям открыт. Введите /scenario, чтобы начать.")
        update_code(user_id, None)  # Удаляем код после использования
    else:
        await update.message.reply_text("❌ Неверный код или код уже использован.")

# Команда /scenario
async def scenario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not check_subscription(user_id):
        await update.message.reply_text("❌ У вас нет доступа к сценариям. Оформите подписку.")
        return

    await update.message.reply_text("📖 Вот ваш сценарий: ...")

# Основная функция
def main():
    init_db()  # Инициализация базы данных
    application = Application.builder().token(TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getcode", get_code))
    application.add_handler(CommandHandler("code", check_code))
    application.add_handler(CommandHandler("scenario", scenario))

    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
