import os
import asyncio
import json
import logging
from datetime import datetime
from anthropic import Anthropic

from telegram import Update, Chat
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from apscheduler.schedulers.background import BackgroundScheduler

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_KEY    = os.environ["ANTHROPIC_API_KEY"]
CHANNEL_ID       = os.environ["CHANNEL_ID"]          # e.g. @mychannel or -1001234567890
ADMIN_IDS        = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x]
SCHEDULE_FILE    = "schedule.json"

anthropic = Anthropic(api_key=ANTHROPIC_KEY)

SYSTEM_PROMPT = """Ты — умный AI-помощник делового Telegram-канала о бизнесе и маркетинге.
Твоя задача:
1. Отвечать на вопросы подписчиков чётко, по делу, с практической пользой.
2. Генерировать посты для канала — структурированные, с эмодзи, на русском языке.
3. Модерировать: если сообщение содержит грубость, спам или рекламу, отвечай: УДАЛИТЬ.
Тон: профессиональный, дружелюбный, конкретный. Без воды."""

# ─── AI helpers ────────────────────────────────────────────────────────────────

def ask_claude(user_message: str, extra_instruction: str = "") -> str:
    prompt = extra_instruction + "\n\n" + user_message if extra_instruction else user_message
    response = anthropic.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def generate_post(topic: str) -> str:
    instruction = (
        "Напиши пост для Telegram-канала о бизнесе/маркетинге. "
        "Структура: заголовок с эмодзи → 3-5 ключевых тезиса → призыв к действию. "
        "Длина — до 900 символов."
    )
    return ask_claude(topic, instruction)


def moderate(text: str) -> bool:
    """Returns True if message should be deleted."""
    verdict = ask_claude(
        text,
        "Это сообщение в деловом Telegram-канале. "
        "Если оно содержит мат, оскорбления, спам или рекламу — ответь только словом УДАЛИТЬ. "
        "Иначе ответь только словом ОК.",
    )
    return verdict.strip().upper().startswith("УДАЛИТЬ")


# ─── Schedule helpers ──────────────────────────────────────────────────────────

def load_schedule() -> list:
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE) as f:
            return json.load(f)
    return []


def save_schedule(posts: list):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)


# ─── Scheduled job ─────────────────────────────────────────────────────────────

async def publish_scheduled(app: Application):
    posts = load_schedule()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    remaining = []
    for post in posts:
        if post["time"] <= now:
            try:
                await app.bot.send_message(chat_id=CHANNEL_ID, text=post["text"])
                logger.info(f"Published scheduled post: {post['text'][:50]}…")
            except Exception as e:
                logger.error(f"Failed to publish: {e}")
                remaining.append(post)
        else:
            remaining.append(post)
    save_schedule(remaining)


# ─── Command handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я AI-администратор вашего канала.\n\n"
        "Команды для администраторов:\n"
        "/post <тема> — опубликовать пост сейчас\n"
        "/schedule ГГГГ-ММ-ДД ЧЧ:ММ <тема> — запланировать пост\n"
        "/list — список запланированных постов\n"
        "/clear — очистить расписание\n\n"
        "Просто напишите мне вопрос — отвечу как эксперт по бизнесу и маркетингу. 🚀"
    )


async def cmd_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("⛔ Только для администраторов.")
    topic = " ".join(ctx.args)
    if not topic:
        return await update.message.reply_text("Укажите тему: /post <тема>")
    await update.message.reply_text("⏳ Генерирую пост…")
    text = generate_post(topic)
    await ctx.bot.send_message(chat_id=CHANNEL_ID, text=text)
    await update.message.reply_text("✅ Пост опубликован!")


async def cmd_schedule(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("⛔ Только для администраторов.")
    # /schedule 2025-06-01 09:00 Тема поста
    if len(ctx.args) < 3:
        return await update.message.reply_text(
            "Формат: /schedule ГГГГ-ММ-ДД ЧЧ:ММ <тема>"
        )
    date_str = ctx.args[0]
    time_str = ctx.args[1]
    topic    = " ".join(ctx.args[2:])
    dt_str   = f"{date_str} {time_str}"
    try:
        datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except ValueError:
        return await update.message.reply_text("❌ Неверный формат даты. Пример: 2025-06-01 09:00")

    await update.message.reply_text("⏳ Генерирую пост…")
    text  = generate_post(topic)
    posts = load_schedule()
    posts.append({"time": dt_str, "text": text})
    posts.sort(key=lambda p: p["time"])
    save_schedule(posts)
    await update.message.reply_text(f"✅ Пост запланирован на {dt_str}:\n\n{text[:200]}…")


async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    posts = load_schedule()
    if not posts:
        return await update.message.reply_text("📭 Расписание пустое.")
    lines = [f"{i+1}. {p['time']} — {p['text'][:60]}…" for i, p in enumerate(posts)]
    await update.message.reply_text("📅 Запланированные посты:\n\n" + "\n".join(lines))


async def cmd_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    save_schedule([])
    await update.message.reply_text("🗑 Расписание очищено.")


# ─── Message handlers ──────────────────────────────────────────────────────────

async def handle_comment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Moderate comments in channel discussion group."""
    msg = update.message
    if not msg or not msg.text:
        return

    # Moderation
    if moderate(msg.text):
        try:
            await msg.delete()
            logger.info(f"Deleted message from {msg.from_user.id}: {msg.text[:60]}")
        except Exception as e:
            logger.warning(f"Cannot delete: {e}")
        return

    # Reply to questions (messages ending with ?)
    if msg.text.strip().endswith("?"):
        answer = ask_claude(msg.text)
        await msg.reply_text(answer)


async def handle_private(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Answer questions in private chat (for admins and users)."""
    answer = ask_claude(update.message.text)
    await update.message.reply_text(answer)


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("post",     cmd_post))
    app.add_handler(CommandHandler("schedule", cmd_schedule))
    app.add_handler(CommandHandler("list",     cmd_list))
    app.add_handler(CommandHandler("clear",    cmd_clear))

    # Messages in groups/channels → moderation + Q&A
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        handle_comment,
    ))

    # Private messages → AI assistant
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_private,
    ))

    # Scheduler: check every minute for posts to publish
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: asyncio.get_event_loop().create_task(publish_scheduled(app)),
        trigger="interval",
        minutes=1,
    )
    scheduler.start()

    logger.info("Bot started.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
