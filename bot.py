import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")          # ← лучше брать из переменных Render

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ← Подключи здесь все свои handlers/routers

async def on_startup(bot: Bot) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(
        url="https://telegram-bot-8vl0.onrender.com/webhook",  # ← твой точный URL
        drop_pending_updates=True
    )
    print("✅ Webhook установлен!")

async def main():
    dp.startup.register(on_startup)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    # ←←← КРИТИЧНО ДЛЯ RENDER ←←←
    port = int(os.getenv("PORT", 10000))
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()

    print(f"🚀 Бот запущен на Webhook! Порт: {port}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
