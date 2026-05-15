import asyncio
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

TOKEN = "ТОКЕН_БОТА_ЗДЕСЬ"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ←←← Здесь подключи все свои роутеры/handlers ←←←
# from handlers import router
# dp.include_router(router)

async def on_startup(bot: Bot) -> None:
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(
        url="https://telegram-bot-8vl0.onrender.com/webhook",   # ← Убедись, что URL правильный!
        drop_pending_updates=True
    )
    print("✅ Webhook установлен успешно!")

async def main():
    dp.startup.register(on_startup)

    # Создаём веб-сервер
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path="/webhook")
    
    setup_application(app, dp, bot=bot)

    # Render использует порт 10000
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=10000)
    await site.start()

    print("🚀 Бот запущен на Webhook!")
    await asyncio.Event().wait()  # Держим процесс запущенным

if __name__ == "__main__":
    asyncio.run(main())
