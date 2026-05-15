import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN is not set!")

app = Flask(__name__)
application = Application.builder().token(TOKEN).updater(None).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает!\nНапиши любое сообщение.")

async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or "что-то"
    await update.message.reply_text(f"🔄 Я получил: {text}\n\nБот живой и отвечает!")

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.ALL, any_message))   # ← реагирует на всё

@app.post("/webhook")
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, application.bot)
    application.update_queue.put(update)
    return "OK", 200

@app.get("/")
def home():
    return "<h1>✅ Bot is live and should reply to everything!</h1>"

if __name__ == "__main__":
    import asyncio
    from threading import Thread

    async def run_bot():
        await application.initialize()
        await application.start()
        await application.bot.set_webhook(url="https://telegram-bot-8vl0.onrender.com/webhook", drop_pending_updates=True)
        print("Webhook set")

    Thread(target=lambda: asyncio.run(run_bot()), daemon=True).start()

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
