import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os
import openai

# Загружаем переменные из .env
load_dotenv()

# Получаем переменные окружения
TOKEN = os.getenv('TOKEN')  # Токен бота
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')  # Ключ OpenAI

# Настройка OpenAI
openai.api_key = OPENAI_API_KEY

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
        "welcome": "💫 Добро пожаловать! Я помогу вам организовать идеальное свидание.",
        "ask_criteria": "Пожалуйста, ответьте на несколько вопросов:\n\n1. Ваш бюджет?\n2. Предпочтения (например, ресторан, кино, прогулка)?\n3. Местоположение?\n4. Дополнительные пожелания?",
        "generating_scenario": "🛠 Генерирую сценарий...",
        "scenario_ready": "🎉 Ваш уникальный сценарий готов!",
        "error": "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
    },
    "en": {
        "welcome": "💫 Welcome! I'll help you organize the perfect date.",
        "ask_criteria": "Please answer a few questions:\n\n1. Your budget?\n2. Preferences (e.g., restaurant, cinema, walk)?\n3. Location?\n4. Any additional wishes?",
        "generating_scenario": "🛠 Generating scenario...",
        "scenario_ready": "🎉 Your unique scenario is ready!",
        "error": "❌ An error occurred. Please try again later."
    }
}

# Получение языка пользователя
def get_user_language(update: Update):
    user_language = update.effective_user.language_code
    return user_language if user_language in messages else "en"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_language = get_user_language(update)
    await update.message.reply_text(messages[user_language]["welcome"])
    await update.message.reply_text(messages[user_language]["ask_criteria"])

# Обработка ввода критериев
async def handle_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_language = get_user_language(update)
    user_input = update.message.text

    # Сохраняем ввод пользователя в контексте
    context.user_data["criteria"] = user_input

    # Уведомляем о начале генерации
    async def handle_criteria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_language = get_user_language(update)
    user_input = update.message.text

    # Уведомляем о начале генерации
    await update.message.reply_text(messages[user_language]["generating_scenario"])

    try:
        # Фиктивный сценарий (заглушка)
        scenario = f"Ваш сценарий на основе критериев:\n\n{user_input}\n\nПример сценария:\n1. Начните с прогулки в парке.\n2. Посетите уютное кафе.\n3. Завершите вечер просмотром фильма."
        await update.message.reply_text(messages[user_language]["scenario_ready"])
        await update.message.reply_text(scenario)

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text(messages[user_language]["error"])

# Основная функция
def main():
    application = Application.builder().token(TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_criteria))

    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
