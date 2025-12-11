from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import os, re, sys
from dotenv import load_dotenv
import requests
import traceback

load_dotenv()

token = os.getenv("TOKEN")

if not token:
    print("error: no $TOKEN provided", file=sys.stderr)
    exit(1)

output_platforms = {
    "youtube": "YouTube",
    "spotify": "Spotify",
    "appleMusic": "Apple Music"
}

re_streaming = {
    "spotify": "https://open\\.spotify\\.com/\\S*",
    "apple": "https://(?:geo\\.)?music\\.apple\\.com/\\S*|https://itunes\\.apple\\.com/\\S*",
    "youtube": "https://youtube\\.com/watch\\?v=.*|https://youtu\\.be/\\S*",
    "ytmusic": "https://music\\.youtube\\.com/watch\\?v=.*",
    "pandora": "https://www\\.pandora\\.com/\\S*",
    "deezer": "https://www\\.deezer\\.com/\\S*",
    "soundcloud": "https://soundcloud\\.com/\\S*",
    "amazon": "https://music\\.amazon\\.com/\\S*",
    "tidal": "https://listen\\.tidal\\.com/\\S*",
    "yandex": "https://music\\.yandex\\.ru/\\S*",
    "audiomack": "https://audiomack\\.com/\\S*",
    "anghami": "https://play\\.anghami\\.com/\\S*"
}

re_all = re.compile("|".join(v for v in re_streaming.values() if v))

def find_all_urls(msg):
    return re_all.findall(msg)

api_endpoint = "https://api.song.link/v1-alpha.1/links"

def odesli(url, cc="DE"):
    try:
        r = requests.get(api_endpoint, params={"url": url, "userCountry": cc})
        r_data = r.json()
        odesli_link = r_data["pageUrl"]
        spotify_id = next((key for key in r_data["entitiesByUniqueId"] if key.startswith("SPOTIFY_SONG")), None)
        if spotify_id:
            entity_id = spotify_id
        else:
            entity_id = r_data["entityUniqueId"]
        entity = r_data["entitiesByUniqueId"][entity_id]
        artist, title = entity.get("artistName", "[no artist]"), entity.get("title", "[no title]").rstrip(" - Topic")
        msg = f"***{title}*** by ***{artist}*** ([Odesli]({odesli_link}))\n\n"
        for platform_id, platform_name in output_platforms.items():
            if r_data["linksByPlatform"].get(platform_id):
                url = r_data["linksByPlatform"][platform_id]["url"]
                msg += f"***{platform_name}***: [Link]({url})\n"
        return msg
    except:
        traceback.print_exc()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass

async def parse(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    urls = find_all_urls(update.message.text)
    if urls:
        for url in urls:
            try:
                await update.message.reply_text(odesli(url), parse_mode="Markdown", link_preview_options={"is_disabled": True}, reply_to_message_id=update.message.id)
            except:
                traceback.print_exc()

app = Application.builder().token(token).build()

app.add_handler(CommandHandler("start", start))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, parse))

print("starting Odesli bot")
app.run_polling()
