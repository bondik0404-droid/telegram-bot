import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден в переменных окружения!")

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  # Добавь свой Telegram ID в Variables

BOT_NAME = "Серьёзный Бот"
VERSION = "1.0"
