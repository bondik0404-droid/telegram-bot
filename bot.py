import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
from threading import Thread

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")

app = Flask(__name__)

# Инициализация бота
application = Application.builder().token(TOKEN).updater(None).build()

# ====================== ХЕНДЛЕРЫ ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот успешно работает на Render 🚀")

application.add_handler(CommandHandler("start", start))

# ====================== WEBHOOK ======================
@app.post("/webhook")
def webhook():
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)
        application.update_queue.put(update)
        return "OK", 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return "ERROR", 500

# ====================== СТРАНИЦЫ ======================
@app.get("/")
def home():
    return """
    <h1>✅ telegram-bot is live!</h1>
    <p><a href="/set_webhook">🔧 Установить Webhook</a></p>
    <p><a href="/health">❤️ Health Check</a></p>
    """

@app.get("/health")
def health():
    return "OK"

@app.get("/set_webhook")
def set_webhook_route():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.bot.delete_webhook(drop_pending_updates=True))
        loop.run_until_complete(application.bot.set_webhook(
            url="https://telegram-bot-8vl0.onrender.com/webhook",
            drop_pending_updates=True
        ))
        loop.close()
        return "<h2>✅ Webhook успешно установлен!</h2><p>Можешь писать боту.</p>"
    except Exception as e:
        return f"<h2>Ошибка: {str(e)}</h2>"

if __name__ == "__main__":
    async def run_bot():
        await application.initialize()
        await application.start()
        print("🚀 Bot application initialized")

    # Запуск бота в отдельном потоке
    Thread(target=lambda: asyncio.run(run_bot()), daemon=True).start()

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
