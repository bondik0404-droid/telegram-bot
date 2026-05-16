import os
import asyncio
import threading
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN is not set!")

app = Flask(__name__)

application = Application.builder().token(TOKEN).updater(None).build()

# Глобальная ссылка на event loop бота
bot_loop = None


# ==================== ХЕНДЛЕРЫ ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Бот работает!\nНапиши любое сообщение.")


async def any_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        text = update.message.text
        await update.message.reply_text(f"Получил: {text}\n\nБот отвечает!")


application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, any_message))
application.add_handler(MessageHandler(filters.ALL, any_message))


# ==================== WEBHOOK ====================

@app.post("/webhook")
def webhook():
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)

        # Передаём задачу в event loop бота (thread-safe)
        future = asyncio.run_coroutine_threadsafe(
            application.process_update(update),
            bot_loop
        )
        future.result(timeout=30)  # ждём выполнения (макс 30 сек)

        return "OK", 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return "ERROR", 500


@app.get("/")
def home():
    return "<h1>✅ Bot is live and processing messages!</h1>"


# ==================== ЗАПУСК ====================

if __name__ == "__main__":
    async def run_bot():
        global bot_loop
        bot_loop = asyncio.get_event_loop()

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

        # Держим бота живым
        await asyncio.Event().wait()

    def start_bot_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        global bot_loop
        bot_loop = loop

        loop.run_until_complete(run_bot())

    thread = threading.Thread(target=start_bot_thread, daemon=True)
    thread.start()

    # Небольшая пауза, чтобы bot_loop успел инициализироваться
    import time
    time.sleep(2)

    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
