import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Подключи здесь свои handlers, если они в отдельных файлах
# from handlers.user import router
# dp.include_router(router)

async def on_startup(bot: Bot):
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(
        url="https://telegram-bot-8vl0.onrender.com/webhook",
        drop_pending_updates=True
    )
    print("✅ Webhook успешно установлен!")

async def main():
    dp.startup.register(on_startup)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    setup_application(app, dp, bot=bot)

    port = int(os.getenv("PORT", 10000))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()

    print(f"🚀 Бот запущен через Webhook на порту {port}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
