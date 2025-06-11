import os
import random
import tempfile
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
import instaloader

# ENV variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Flask App
app = Flask(__name__)
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Logger
logging.basicConfig(level=logging.INFO)

# Reels list
REELS = [
    "https://www.instagram.com/reel/DJYhS7DTC7S/",
    "https://www.instagram.com/reel/DKBWBXHxh-h/",
    "https://www.instagram.com/reel/DI6foZCSlsg/"
]

# Downloader function
async def download_reel(link: str) -> str:
    try:
        shortcode = link.strip("/").split("/")[-1]
        L = instaloader.Instaloader(dirname_pattern=tempfile.gettempdir(), save_metadata=False, download_comments=False)
        L.load_session_from_file(username=None, filename="cookies.txt")
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        L.download_post(post, target=shortcode)
        for file in os.listdir(tempfile.gettempdir()):
            if file.startswith(shortcode) and file.endswith(".mp4"):
                return os.path.join(tempfile.gettempdir(), file)
    except Exception as e:
        logging.error(f"Reel download error: {e}")
    return None

# Viral command handler
async def viral_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and "#viral" in update.message.text.lower():
        link = random.choice(REELS)
        video = await download_reel(link)
        if video:
            await update.message.reply_video(
                video=video,
                caption=f"🎞️ Viral Reel from Instagram\n🔗 {link}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎲 Next Reel", callback_data="next_reel")]
                ])
            )
            os.remove(video)

# Callback query handler
async def next_reel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    link = random.choice(REELS)
    video = await download_reel(link)
    if video:
        await query.message.edit_caption("⏳ Loading next reel...")
        await query.message.reply_video(
            video=video,
            caption=f"🎞️ Viral Reel from Instagram\n🔗 {link}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎲 Next Reel", callback_data="next_reel")]
            ])
        )
        os.remove(video)

# Telegram webhook endpoint
@app.post("/webhook")
async def telegram_webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "OK"

@app.route("/")
def home():
    return "Insta Viral Bot is Running"

# Add handlers
application.add_handler(CommandHandler("start", viral_handler))
application.add_handler(CallbackQueryHandler(next_reel_handler))

if __name__ == "__main__":
    import asyncio
    asyncio.run(application.initialize())
    asyncio.run(application.start())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
