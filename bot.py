import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN is not set!")

app = Flask(__name__)

application = Application.builder().token(TOKEN).updater(None).build()

# ====================== ХЕНДЛЕРЫ ======================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот работает на Render! 🚀\n\nНапиши что угодно — я отвечу.")

async def echo_or_process(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    await update.message.reply_text(f"Получил: {text}\n\n(Здесь будет твоя логика)")

# Команды
application.add_handler(CommandHandler("start", start))

# Все текстовые сообщения
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_or_process))

# ====================== WEBHOOK ======================
@app.post("/webhook")
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, application.bot)
    application.update_queue.put(update)
    return "OK", 200

@app.get("/")
def home():
    return "<h1>✅ Bot is live and ready!</h1>"

if __name__ == "__main__":
    import asyncio
    from threading import Thread

    async def run_bot():
        await application.initialize()
        await application.start()
        await application.bot.set_webhook(
            url="https://telegram-bot-8vl0.onrender.com/webhook",
            drop_pending_updates=True
        )
        print("✅ Webhook установлен")

    Thread(target=lambda: asyncio.run(run_bot()), daemon=True).start()

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
