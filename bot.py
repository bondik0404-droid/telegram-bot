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
    await update.message.reply_text("✅ Бот работает!\nНапиши любое сообщение.")

async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        text = update.message.text
        await update.message.reply_text(f"Получил: {text}\n\nБот отвечает!")

# Регистрируем хендлеры
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))
application.add_handler(MessageHandler(filters.ALL, any_message))  # на всё остальное

# ====================== WEBHOOK ======================
@app.post("/webhook")
def webhook():
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)
        
        # Правильный способ обработки
        asyncio.create_task(application.process_update(update))
        
        return "OK", 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return "ERROR", 500

@app.get("/")
def home():
    return "<h1>✅ Bot is live and processing messages!</h1>"

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
        print("✅ Webhook установлен при старте")

    Thread(target=lambda: asyncio.run(run_bot()), daemon=True).start()

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
