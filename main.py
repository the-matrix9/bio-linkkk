"""
main.py — Bot entry point
Bio Link Protector Bot
─────────────────────────────────────
Loads all plugins from /plugins/ folder.
Starts Flask health-check server for Heroku/Koyeb/Railway.
"""

import asyncio
import importlib
import logging
import os
import threading

from flask import Flask
from pyrogram import Client

from config import API_ID, API_HASH, BOT_TOKEN, PORT, LOG_CHANNEL, BOT_OWNER_ID, START_IMG
from database import save_chat, get_all_chats_with_title

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("BioBot")

# ── Flask health-check ────────────────────────────────────────────────────────
flask_app = Flask(__name__)

@flask_app.route("/")
def health():
    return "BioBot is alive! 🛡️", 200

@flask_app.route("/health")
def healthz():
    return {"status": "ok", "bot": "BioLinkProtector"}, 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=PORT, use_reloader=False)

# ── Pyrogram Client ───────────────────────────────────────────────────────────
app = Client(
    "biobot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True,   # no session file → works on ephemeral FS (Heroku/Koyeb)
)

# ── Load plugins ──────────────────────────────────────────────────────────────
PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "plugins")

def load_plugins():
    for fname in sorted(os.listdir(PLUGINS_DIR)):
        if fname.endswith(".py") and not fname.startswith("_"):
            module_name = f"plugins.{fname[:-3]}"
            try:
                mod = importlib.import_module(module_name)
                # Inject the `app` client into each plugin
                if hasattr(mod, "register"):
                    mod.register(app)
                log.info(f"✅ Loaded plugin: {module_name}")
            except Exception as e:
                log.error(f"❌ Failed to load {module_name}: {e}")

# ── Startup alert ─────────────────────────────────────────────────────────────
async def startup_alert():
    """Send startup message to owner and log channel."""
    try:
        me = await app.get_me()
        chats = await get_all_chats_with_title()
        text = (
            f"<b>🚀 ʙɪᴏ ʙᴏᴛ sᴛᴀʀᴛᴇᴅ!</b>\n\n"
            f"🤖 <b>ʙᴏᴛ:</b> @{me.username}\n"
            f"👥 <b>ᴛᴏᴛᴀʟ ɢʀᴏᴜᴘs:</b> {len(chats)}\n"
            f"🌐 <b>ᴘᴏʀᴛ:</b> {PORT}\n"
            f"⏱️ <b>sᴛᴀᴛᴜs:</b> ᴀʟʟ ᴘʟᴜɢɪɴs ʟᴏᴀᴅᴇᴅ ✅"
        )
        # Alert owner
        if BOT_OWNER_ID:
            try:
                await app.send_photo(BOT_OWNER_ID, START_IMG, caption=text)
            except Exception:
                await app.send_message(BOT_OWNER_ID, text)
        # Alert log channel
        if LOG_CHANNEL:
            try:
                await app.send_message(LOG_CHANNEL, text)
            except Exception:
                pass
    except Exception as e:
        log.error(f"Startup alert failed: {e}")

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Load plugins before starting
    load_plugins()

    # Start Flask in background
    threading.Thread(target=run_flask, daemon=True).start()
    log.info(f"🌐 Health-check server → port {PORT}")

    # Run bot with startup hook
    async def _run():
        async with app:
            await startup_alert()
            log.info("🛡️  Bio Link Protector Bot is running...")
            await asyncio.get_event_loop().create_future()  # run forever

    asyncio.run(_run())
