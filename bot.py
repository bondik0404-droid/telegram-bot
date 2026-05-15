import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)

# Инициализация PTB
application = Application.builder().token(TOKEN).updater(None).build()

# ====================== ХЕНДЛЕРЫ ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот работает на Render через Webhook 🚀")

application.add_handler(CommandHandler("start", start))
# Добавляй сюда остальные свои команды

# ====================== WEBHOOK ======================
@app.post("/webhook")
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, application.bot)
    application.update_queue.put(update)
    return "OK", 200

# ====================== УДОБНЫЕ СТРАНИЦЫ ======================
@app.get("/")
def home():
    return """
    <h1>✅ telegram-bot is live!</h1>
    <p><a href="/set_webhook">🔧 Нажми сюда, чтобы установить Webhook</a></p>
    """

@app.get("/set_webhook")
async def set_webhook_route():
    await application.bot.delete_webhook(drop_pending_updates=True)
    await application.bot.set_webhook(
        url="https://telegram-bot-8vl0.onrender.com/webhook",
        drop_pending_updates=True
    )
    return "<h2>✅ Webhook успешно установлен!</h2><p>Теперь можешь писать боту в Telegram.</p>"

if __name__ == "__main__":
    import asyncio
    from threading import Thread

    async def run_bot():
        await application.initialize()
        await application.start()
        print("🚀 Application initialized")

    Thread(target=lambda: asyncio.run(run_bot()), daemon=True).start()

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
