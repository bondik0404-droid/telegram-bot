import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN is not set!")

app = Flask(__name__)

# Инициализация
application = Application.builder().token(TOKEN).updater(None).build()

# Хендлеры
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот работает на Render через Webhook 🚀")

application.add_handler(CommandHandler("start", start))

# Webhook endpoint
@app.post("/webhook")
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, application.bot)
    application.update_queue.put(update)
    return "OK", 200

# Страницы
@app.get("/")
def home():
    return """
    <h1>✅ telegram-bot is live!</h1>
    <p><a href="/set_webhook">🔧 Установить Webhook</a></p>
    """

@app.get("/set_webhook")
def set_webhook_route():
    # Простой способ без сложных async
    import asyncio
    from telegram.error import TelegramError
    
    try:
        # Запускаем в новом loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.run_until_complete(application.bot.delete_webhook(drop_pending_updates=True))
        loop.run_until_complete(application.bot.set_webhook(
            url="https://telegram-bot-8vl0.onrender.com/webhook",
            drop_pending_updates=True
        ))
        loop.close()
        return "<h2>✅ Webhook успешно установлен!</h2>"
    except Exception as e:
        return f"<h2>❌ Ошибка: {str(e)}</h2>"

if __name__ == "__main__":
    import asyncio
    from threading import Thread

    async def run_bot():
        await application.initialize()
        await application.start()
        print("🚀 Bot initialized")

    Thread(target=lambda: asyncio.run(run_bot()), daemon=True).start()

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
