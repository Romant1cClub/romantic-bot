import random
import string
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Вставьте свои значения
TOKEN = '8179789266:AAFiXJ-B-32F2GfZxOghM8qiHOtnRXXE5Sc'  # Замените на токен вашего бота
BOOSTY_URL = 'https://boosty.to/romant1cclub_bot/purchase/3245989?ssource=DIRECT&share=subscription_link'  # Замените на вашу ссылку Boosty

# Хранилище данных
user_codes = {}  # {user_id: код}
subscribed_users = set()  # Множество подписанных пользователей

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

    # Проверка, подписан ли пользователь
    if user_id not in subscribed_users:
        await update.message.reply_text(
            "❌ Вы не подписаны. Пожалуйста, оформите подписку и попробуйте снова."
        )
        return

    # Генерация кода
    if user_id in user_codes:
        await update.message.reply_text(f"📌 Ваш код уже сгенерирован: {user_codes[user_id]}")
    else:
        new_code = generate_code()
        user_codes[user_id] = new_code
        await update.message.reply_text(
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

# Основная функция
def main():
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
