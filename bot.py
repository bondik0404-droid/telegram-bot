import os
from flask import Flask
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram import Update

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN is not set!")

app = Flask(__name__)

# Инициализация бота
application = Application.builder().token(TOKEN).updater(None).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Бот работает на Render! 🚀")

application.add_handler(CommandHandler("start", start))

# Главная страница
@app.get("/")
def home():
    return """
    <h1>✅ telegram-bot is live!</h1>
    <p>Бот запущен.</p>
    """

if __name__ == "__main__":
    import asyncio
    from threading import Thread

    async def run_bot():
        await application.initialize()
        await application.start()
        # Устанавливаем webhook один раз при старте
        try:
            await application.bot.delete_webhook(drop_pending_updates=True)
            await application.bot.set_webhook(
                url="https://telegram-bot-8vl0.onrender.com/webhook",
                drop_pending_updates=True
            )
            print("✅ Webhook успешно установлен при старте!")
        except Exception as e:
            print(f"Webhook setup error: {e}")

    # Запуск бота
    Thread(target=lambda: asyncio.run(run_bot()), daemon=True).start()

    # Flask
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
