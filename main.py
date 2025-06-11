import os
import random
import logging
from flask import Flask, request
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import instaloader
import tempfile
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes

app = Flask(__name__)

# Init bot
application = ApplicationBuilder().token(BOT_TOKEN).build()

@app.post('/webhook')
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return "OK"

# Logging
logging.basicConfig(level=logging.INFO)

# ENV Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")

# Pyrogram client
bot = Client(
    "instaviralbot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Reel URLs list (or update from scraper later)
REELS = [
    "https://www.instagram.com/reel/DJYhS7DTC7S/",
    "https://www.instagram.com/reel/DKBWBXHxh-h/",
    "https://www.instagram.com/reel/DI6foZCSlsg/"
]


# Helper to download reel using instaloader
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


# Handle #viral trigger
@bot.on_message(filters.text & filters.group)
async def viral_handler(client, message: Message):
    if "#viral" in message.text.lower():
        link = random.choice(REELS)
        video = await download_reel(link)
        if video:
            await message.reply_video(
                video=video,
                caption=f"🎞️ Viral Reel from Instagram\n🔗 {link}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎲 Next Reel", callback_data="next_reel")]
                ])
            )
            os.remove(video)


# Callback for next reel
@bot.on_callback_query()
async def callback_handler(client, callback_query):
    if callback_query.data == "next_reel":
        link = random.choice(REELS)
        video = await download_reel(link)
        if video:
            await callback_query.message.edit_caption("⏳ Loading next reel...")
            await callback_query.message.reply_video(
                video=video,
                caption=f"🎞️ Viral Reel from Instagram\n🔗 {link}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎲 Next Reel", callback_data="next_reel")]
                ])
            )
            os.remove(video)
        await callback_query.answer()


@app.route("/")
def home():
    return "InstaViralBot is running."


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json()
    if update:
        bot.process_update(update)
    return "ok"


if __name__ == "__main__":
    bot.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
