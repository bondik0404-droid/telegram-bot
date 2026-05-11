import logging
import sys
import telebot
from telebot import types
from config import TOKEN, ADMIN_ID
from database import init_db, add_or_update_user, add_note, get_user_notes, get_stats
from keyboards import main_menu, cancel_keyboard

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = telebot.TeleBot(TOKEN)

user_states = {}  # Для создания заметок

@bot.message_handler(commands=['start'])
def start(message):
    add_or_update_user(message.from_user)
    bot.send_message(message.chat.id, 
                     f"👋 Добро пожаловать в <b>{telebot.formatting.escape_md('Серьёзный Бот')}</b>!\n\n"
                     "Я помогу тебе вести заметки и отслеживать информацию.", 
                     parse_mode='HTML', 
                     reply_markup=main_menu())

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "Доступные команды:\n/start - перезапустить бота\n/help - помощь")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    add_or_update_user(message.from_user)
    text = message.text.strip()

    if text == "📝 Мои заметки":
        notes = get_user_notes(message.from_user.id)
        if not notes:
            bot.send_message(message.chat.id, "У вас пока нет заметок.")
            return
        
        response = "📝 <b>Ваши заметки:</b>\n\n"
        for note in notes:
            response += f"<b>{note[1]}</b>\n{note[2][:200]}{'...' if len(note[2]) > 200 else ''}\n\n"
        bot.send_message(message.chat.id, response, parse_mode='HTML')

    elif text == "➕ Новая заметка":
        user_states[message.from_user.id] = "waiting_title"
        bot.send_message(message.chat.id, "✍️ Введите заголовок заметки:", reply_markup=cancel_keyboard())

    elif text == "📊 Статистика":
        users, notes = get_stats()
        bot.send_message(message.chat.id, 
                        f"📊 <b>Статистика бота:</b>\n\n"
                        f"👥 Пользователей: <b>{users}</b>\n"
                        f"📝 Всего заметок: <b>{notes}</b>", parse_mode='HTML')

    elif text == "❓ Помощь":
        bot.send_message(message.chat.id, "Напишите мне что угодно — я помогу организовать ваши заметки.")

    elif text == "❌ Отмена":
        if message.from_user.id in user_states:
            del user_states[message.from_user.id]
        bot.send_message(message.chat.id, "❌ Действие отменено.", reply_markup=main_menu())

    # Создание заметки (двухшаговый процесс)
    elif message.from_user.id in user_states:
        state = user_states[message.from_user.id]
        
        if state == "waiting_title":
            user_states[message.from_user.id] = {"state": "waiting_content", "title": text}
            bot.send_message(message.chat.id, "📝 Теперь введите текст заметки:")
        
        elif isinstance(state, dict) and state["state"] == "waiting_content":
            note_id = add_note(message.from_user.id, state["title"], text)
            del user_states[message.from_user.id]
            bot.send_message(message.chat.id, f"✅ Заметка успешно сохранена! (ID: {note_id})", reply_markup=main_menu())

if __name__ == "__main__":
    init_db()
    print("🚀 Серьёзный бот успешно запущен на Railway!")
    bot.infinity_polling(none_stop=True, interval=1)
