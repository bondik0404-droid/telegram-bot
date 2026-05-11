import os
import sys
import telebot
from dotenv import load_dotenv

# Загружаем .env (на локалке)
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("ОШИБКА: BOT_TOKEN не найден в переменных окружения!")
    print("Проверь Variables на Railway")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот, запущенный на Railway ✅\nНапиши что-нибудь!")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ты написал: {message.text}")

print("✅ Бот успешно запущен на Railway!")

if __name__ == "__main__":
    bot.infinity_polling(none_stop=True, interval=1)
