import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
app = Flask(__name__)

# Инициализация PTB
application = Application.builder().token(TOKEN).updater(None).build()

# === ТВОИ ХЕНДЛЕРЫ ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я работаю на Render через Webhook.")

application.add_handler(CommandHandler("start", start))

# Webhook endpoint
@app.post("/webhook")
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, application.bot)
    application.update_queue.put(update)
    return "OK", 200

@app.get("/")
def home():
    return "Бот живой!"

if __name__ == "__main__":
    import asyncio
    from threading import Thread

    # Запускаем обработку обновлений в фоне
    async def run_bot():
        await application.initialize()
        await application.start()
        await application.bot.set_webhook(
            url="https://telegram-bot-8vl0.onrender.com/webhook",
            drop_pending_updates=True
        )
        print("🚀 Webhook установлен!")

    def start_bot():
        asyncio.run(run_bot())

    Thread(target=start_bot, daemon=True).start()

    # Запускаем Flask
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
