import os
import sys
import telebot
from dotenv import load_dotenv
from telebot import types

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("ОШИБКА: BOT_TOKEN не найден!")
    sys.exit(1)

bot = telebot.TeleBot(TOKEN)

# Главное меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Привет", "Помощь")
    markup.add("Информация", "Контакты")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я бот, запущенный на Railway 🚀", reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, "Доступные команды:\n/start - перезапустить бота\n/help - это сообщение")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    text = message.text.lower()
    
    if text in ["привет", "hello", "hi"]:
        bot.reply_to(message, "Привет! Как дела?")
    elif text in ["помощь", "help"]:
        bot.reply_to(message, "Напиши что угодно — я отвечу!")
    elif text == "информация":
        bot.reply_to(message, "Я Telegram-бот, запущенный на Railway.app")
    elif text == "контакты":
        bot.reply_to(message, "Напиши @твой_юзернейм")
    else:
        bot.reply_to(message, f"Ты написал: {message.text}\n\nЯ пока просто эхо-бот 😊")

print("✅ Бот успешно запущен на Railway!")

if __name__ == "__main__":
    bot.infinity_polling(none_stop=True, interval=1, timeout=30)
