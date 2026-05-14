import os
import asyncio
import json
import logging
from datetime import datetime
from anthropic import Anthropic

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_KEY  = os.environ["ANTHROPIC_API_KEY"]
CHANNEL_ID     = os.environ["CHANNEL_ID"]
ADMIN_IDS      = [int(x) for x in os.environ.get("ADMIN_IDS", "").split(",") if x]
SCHEDULE_FILE  = "schedule.json"

anthropic = Anthropic(api_key=ANTHROPIC_KEY)

DD_TYPE, DD_ADDRESS, DD_OWNER, DD_ENCUMBRANCE, DD_HISTORY, DD_AREA, DD_YEAR, DD_EXTRA = range(8)

DD_SYSTEM = """Ты — опытный юрист по недвижимости и эксперт Due Diligence в России.
Проанализируй данные об объекте и составь структурированный отчёт о рисках.

Формат отчёта:
🏠 ОБЪЕКТ: [тип и адрес]
📊 ОБЩАЯ ОЦЕНКА РИСКА: [Низкий / Средний / Высокий] + обоснование

🔴 КРИТИЧЕСКИЕ РИСКИ:
🟡 УМЕРЕННЫЕ РИСКИ:
🟢 ПОЛОЖИТЕЛЬНЫЕ ФАКТОРЫ:

📋 ЧТО ПРОВЕРИТЬ ДОПОЛНИТЕЛЬНО:
1. ...

⚖️ ЗАКЛЮЧЕНИЕ: [вывод и рекомендация]

Отвечай профессионально, без воды. Предупреждай о необходимости консультации с юристом."""

CHANNEL_SYSTEM = """Ты — AI-помощник делового Telegram-канала о бизнесе и маркетинге.
1. Отвечай чётко и по делу.
2. Генерируй посты — структурированные, с эмодзи.
3. Модерируй: если спам/мат/реклама — отвечай только: УДАЛИТЬ."""

def ask_claude(prompt: str, system: str = CHANNEL_SYSTEM) -> str:
    r = anthropic.messages.create(model="claude-opus-4-5", max_tokens=2000, system=system,
                                   messages=[{"role": "user", "content": prompt}])
    return r.content[0].text.strip()

def generate_post(topic: str) -> str:
    return ask_claude(f"Напиши пост для Telegram-канала о бизнесе/маркетинге. "
                      f"Структура: заголовок с эмодзи → 3-5 тезисов → призыв к действию. До 900 символов.\n\nТема: {topic}")

def moderate(text: str) -> bool:
    r = ask_claude(f"Сообщение в деловом канале. Спам/мат/реклама — ответь УДАЛИТЬ, иначе — ОК.\n\n{text}")
    return r.strip().upper().startswith("УДАЛИТЬ")

def generate_dd_report(data: dict) -> str:
    prompt = f"""Проведи Due Diligence объекта недвижимости:
Тип: {data.get('type')}
Адрес: {data.get('address')}
Собственник: {data.get('owner')}
Обременения: {data.get('encumbrance')}
История переходов: {data.get('history')}
Площадь: {data.get('area')} кв.м
Год постройки: {data.get('year')}
Доп. информация: {data.get('extra')}"""
    return ask_claude(prompt, system=DD_SYSTEM)

def load_schedule() -> list:
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE) as f: return json.load(f)
    return []

def save_schedule(posts: list):
    with open(SCHEDULE_FILE, "w") as f: json.dump(posts, f, ensure_ascii=False, indent=2)

async def publish_scheduled(app):
    posts = load_schedule()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    remaining = []
    for post in posts:
        if post["time"] <= now:
            try:
                await app.bot.send_message(chat_id=CHANNEL_ID, text=post["text"])
            except Exception as e:
                logger.error(e); remaining.append(post)
        else:
            remaining.append(post)
    save_schedule(remaining)

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я AI-помощник.\n\n"
        "🏠 *Due Diligence недвижимости:*\n/dd — начать проверку объекта\n\n"
        "📋 *Команды администратора:*\n"
        "/post <тема> — опубликовать пост\n"
        "/schedule ГГГГ-ММ-ДД ЧЧ:ММ <тема> — запланировать\n"
        "/list — расписание\n/clear — очистить расписание",
        parse_mode="Markdown")

async def cmd_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("⛔ Только для администраторов.")
    topic = " ".join(ctx.args)
    if not topic: return await update.message.reply_text("Укажите тему: /post <тема>")
    await update.message.reply_text("⏳ Генерирую пост…")
    text = generate_post(topic)
    await ctx.bot.send_message(chat_id=CHANNEL_ID, text=text)
    await update.message.reply_text("✅ Пост опубликован!")

async def cmd_schedule(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("⛔ Только для администраторов.")
    if len(ctx.args) < 3: return await update.message.reply_text("Формат: /schedule ГГГГ-ММ-ДД ЧЧ:ММ <тема>")
    dt_str = f"{ctx.args[0]} {ctx.args[1]}"
    topic = " ".join(ctx.args[2:])
    try: datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    except ValueError: return await update.message.reply_text("❌ Неверный формат даты.")
    await update.message.reply_text("⏳ Генерирую пост…")
    text = generate_post(topic)
    posts = load_schedule()
    posts.append({"time": dt_str, "text": text})
    posts.sort(key=lambda p: p["time"])
    save_schedule(posts)
    await update.message.reply_text(f"✅ Запланирован на {dt_str}:\n\n{text[:200]}…")

async def cmd_list(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    posts = load_schedule()
    if not posts: return await update.message.reply_text("📭 Расписание пустое.")
    lines = [f"{i+1}. {p['time']} — {p['text'][:60]}…" for i, p in enumerate(posts)]
    await update.message.reply_text("📅 Посты:\n\n" + "\n".join(lines))

async def cmd_clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    save_schedule([])
    await update.message.reply_text("🗑 Расписание очищено.")

# ── DD conversation ─────────────────────────────────────────────────────────────

async def dd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["dd"] = {}
    kb = [["🏢 Квартира", "🏠 Дом"], ["🏬 Коммерческий объект", "🏗 Земельный участок"]]
    await update.message.reply_text(
        "🏠 *Due Diligence недвижимости*\n\nВыберите тип объекта:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True),
        parse_mode="Markdown")
    return DD_TYPE

async def dd_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["dd"]["type"] = update.message.text
    await update.message.reply_text("📍 Укажите адрес объекта:", reply_markup=ReplyKeyboardRemove())
    return DD_ADDRESS

async def dd_address(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["dd"]["address"] = update.message.text
    await update.message.reply_text("👤 Кто собственник?\n(физлицо / юрлицо, сколько собственников)")
    return DD_OWNER

async def dd_owner(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["dd"]["owner"] = update.message.text
    kb = [["Нет обременений"], ["Ипотека"], ["Арест / залог"], ["Аренда"], ["Не знаю"]]
    await update.message.reply_text("🔒 Обременения на объекте:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return DD_ENCUMBRANCE

async def dd_encumbrance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["dd"]["encumbrance"] = update.message.text
    kb = [["1 владелец давно", "1 владелец недавно"], ["2-3 перехода", "Много / не знаю"]]
    await update.message.reply_text("📜 История переходов права:",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return DD_HISTORY

async def dd_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["dd"]["history"] = update.message.text
    await update.message.reply_text("📐 Площадь объекта (кв. м):", reply_markup=ReplyKeyboardRemove())
    return DD_AREA

async def dd_area(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["dd"]["area"] = update.message.text
    await update.message.reply_text("🏗 Год постройки:")
    return DD_YEAR

async def dd_year(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["dd"]["year"] = update.message.text
    await update.message.reply_text(
        "📝 Дополнительно (перепланировка, маткапитал, наследство, прописанные дети и т.д.).\nЕсли нет — напишите *нет*.",
        parse_mode="Markdown")
    return DD_EXTRA

async def dd_extra(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["dd"]["extra"] = update.message.text
    await update.message.reply_text("⏳ Анализирую данные, формирую отчёт... (~30 сек)")
    report = generate_dd_report(ctx.user_data["dd"])
    for i in range(0, len(report), 4000):
        await update.message.reply_text(report[i:i+4000])
    await update.message.reply_text(
        "⚠️ Отчёт носит информационный характер и не заменяет консультацию юриста.\n\nПроверить другой объект: /dd")
    ctx.user_data["dd"] = {}
    return ConversationHandler.END

async def dd_cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["dd"] = {}
    await update.message.reply_text("❌ Проверка отменена. /dd — начать заново.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def handle_comment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg or not msg.text: return
    if moderate(msg.text):
        try: await msg.delete()
        except: pass
        return
    if msg.text.strip().endswith("?"):
        await msg.reply_text(ask_claude(msg.text))

async def handle_private(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ask_claude(update.message.text))

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(ConversationHandler(
        entry_points=[CommandHandler("dd", dd_start)],
        states={
            DD_TYPE:        [MessageHandler(filters.TEXT & ~filters.COMMAND, dd_type)],
            DD_ADDRESS:     [MessageHandler(filters.TEXT & ~filters.COMMAND, dd_address)],
            DD_OWNER:       [MessageHandler(filters.TEXT & ~filters.COMMAND, dd_owner)],
            DD_ENCUMBRANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, dd_encumbrance)],
            DD_HISTORY:     [MessageHandler(filters.TEXT & ~filters.COMMAND, dd_history)],
            DD_AREA:        [MessageHandler(filters.TEXT & ~filters.COMMAND, dd_area)],
            DD_YEAR:        [MessageHandler(filters.TEXT & ~filters.COMMAND, dd_year)],
            DD_EXTRA:       [MessageHandler(filters.TEXT & ~filters.COMMAND, dd_extra)],
        },
        fallbacks=[CommandHandler("cancel", dd_cancel)],
    ))

    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("post",     cmd_post))
    app.add_handler(CommandHandler("schedule", cmd_schedule))
    app.add_handler(CommandHandler("list",     cmd_list))
    app.add_handler(CommandHandler("clear",    cmd_clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, handle_comment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_private))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(publish_scheduled, trigger="interval", minutes=1, args=[app])

    async def post_init(application):
        scheduler.start()
        logger.info("Bot started.")

    app.post_init = post_init
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
