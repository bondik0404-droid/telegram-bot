import os
import asyncio
import threading
import time
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from groq import Groq

# ==================== КОНФИГ ====================

TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not TOKEN:
    raise ValueError("BOT_TOKEN is not set!")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set!")

groq_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """Ты — AI-ассистент Дмитрия Бондарева, опытного юриста и риелтора из Ростова-на-Дону с более чем 10-летним стажем.

Твоя задача — отвечать на вопросы клиентов по недвижимости: покупка, продажа, юридическое сопровождение сделок, проверка документов, удалённые сделки по всей России.

Как отвечать:
- Дружелюбно, профессионально, на русском языке
- Давай конкретные и полезные ответы
- Если вопрос требует личной консультации — предложи связаться с Дмитрием напрямую в Telegram: @bondarev_law
- Не давай юридических гарантий — только информацию и рекомендации
- Отвечай кратко и по делу, без воды

Специализация:
- Сопровождение сделок купли-продажи недвижимости
- Юридическая проверка объектов и документов
- Удалённые сделки по всей России
- Работа с недвижимостью в Ростове-на-Дону и Сальске
"""

# Хранилище истории разговоров: {user_id: [{"role": ..., "content": ...}]}
conversation_history = {}
MAX_HISTORY = 20  # Максимум сообщений в истории на пользователя

app = Flask(__name__)
application = Application.builder().token(TOKEN).updater(None).build()
bot_loop = None


# ==================== GROQ ====================

def ask_groq(user_id: int, user_message: str) -> str:
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    history = conversation_history[user_id]
    history.append({"role": "user", "content": user_message})

    # Обрезаем историю если слишком длинная
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
        conversation_history[user_id] = history

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            max_tokens=1024,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        print(f"Groq error: {e}")
        return "Извините, произошла ошибка. Попробуйте позже или напишите напрямую: @bondarev_law"


# ==================== ХЕНДЛЕРЫ ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []  # Сброс истории

    await update.message.reply_text(
        "👋 Здравствуйте! Я AI-ассистент Дмитрия Бондарева — юриста и риелтора.\n\n"
        "Готов ответить на ваши вопросы по недвижимости: покупка, продажа, "
        "юридическое сопровождение, проверка документов.\n\n"
        "Просто напишите ваш вопрос! ✍️\n\n"
        "Для личной консультации: @bondarev_law"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conversation_history[user_id] = []
    await update.message.reply_text("🔄 История разговора очищена. Начнём заново!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    user_text = update.message.text

    # Показываем "печатает..."
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # Запускаем Groq в отдельном потоке (он синхронный)
    loop = asyncio.get_event_loop()
    reply = await loop.run_in_executor(None, ask_groq, user_id, user_text)

    await update.message.reply_text(reply)


application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("reset", reset))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# ==================== WEBHOOK ====================

@app.post("/webhook")
def webhook():
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)

        future = asyncio.run_coroutine_threadsafe(
            application.process_update(update),
            bot_loop
        )
        future.result(timeout=60)

        return "OK", 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return "ERROR", 500


@app.get("/")
def home():
    return "<h1>✅ Bondarev Law Bot — работает!</h1>"


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    def start_bot_thread():
        global bot_loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot_loop = loop

        async def run_bot():
            await application.initialize()
            await application.start()

            webhook_url = os.getenv(
                "WEBHOOK_URL",
                "https://telegram-bot-8vl0.onrender.com/webhook"
            )
            await application.bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True
            )
            print(f"✅ Webhook установлен: {webhook_url}")
            await asyncio.Event().wait()

        loop.run_until_complete(run_bot())

    thread = threading.Thread(target=start_bot_thread, daemon=True)
    thread.start()

    time.sleep(2)

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
