import random
import string
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "ТВОЙ_ТЕЛЕГРАМ_ТОКЕН"
BOOSTY_URL = "https://boosty.to/ТВОЙ_БЛОГ"

# Хранилище кодов {user_id: код}
user_codes = {}

# Функция генерации уникального кода (8 случайных символов)
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💫 Добро пожаловать! Чтобы получить доступ к сценариям, "
        f"оформите подписку: {BOOSTY_URL}\n\n"
        "После оплаты отправьте команду: /getcode"
    )

# Генерация уникального кода
async def get_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Проверяем, есть ли уже код для пользователя
    if user_id in user_codes:
        await update.message.reply_text(f"📌 Ваш код уже сгенерирован: {user_codes[user_id]}")
    else:
        # Создаём новый код и привязываем к пользователю
        new_code = generate_code()
        user_codes[user_id] = new_code
        await update.message.reply_text(f"✅ Ваш уникальный код: {new_code}\n\nВведите его командой: /code <ВАШ_КОД>")

# Проверка введённого кода
async def check_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_code = ' '.join(context.args)

    # Проверяем, соответствует ли код и не был ли уже использован
    if user_id in user_codes and user_codes[user_id] == user_code:
        await update.message.reply_text(
            "🎉 Код подтверждён! Доступ к сценариям открыт. Введите /scenario, чтобы начать."
        )
        # Код использован — удаляем его
        del user_codes[user_id]
    else:
        await update.message.reply_text("❌ Неверный код или код уже использован.")

application = Application.builder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("getcode", get_code))
application.add_handler(CommandHandler("code", check_code))

application.run_polling()
