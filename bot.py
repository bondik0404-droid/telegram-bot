import os
import sys
from dotenv import load_dotenv
import telebot

load_dotenv()  # загружает .env (на Railway не обязательно, но не мешает)

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("ОШИБКА: BOT_TOKEN не найден!")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Бот запущен на Railway ✅")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, message.text)

print("Бот успешно запущен...")

if __name__ == "__main__":
    bot.infinity_polling(none_stop=True)
