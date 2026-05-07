import os

# ── Bot Credentials ────────────────────────────────────────────────────────────
API_ID    = int(os.environ.get("API_ID", 14050586))
API_HASH  = os.environ.get("API_HASH", "42a60d9c657b106370c79bb0a8ac560c")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# ── MongoDB ────────────────────────────────────────────────────────────────────
MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://Krishna:pss968048@cluster0.4rfuzro.mongodb.net/?retryWrites=true&w=majority")

# ── Owner ──────────────────────────────────────────────────────────────────────
BOT_OWNER_ID       = int(os.environ.get("BOT_OWNER_ID", 5738579437))
BOT_OWNER_USERNAME = os.environ.get("BOT_OWNER_USERNAME", "Rishu1286")
SUPPORT_GROUP      = os.environ.get("SUPPORT_GROUP", "https://t.me/rishu1286")

# ── Log Channel (optional) — send action logs here ────────────────────────────
# Set to your channel/group ID e.g. -1001234567890
LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", -1001992970818))

# ── Web / Health-check ─────────────────────────────────────────────────────────
PORT = int(os.environ.get("PORT", 8080))

# ── Bot banner image ───────────────────────────────────────────────────────────
START_IMG = os.environ.get(
    "START_IMG",
    "https://graph.org/file/e9eed432610bc524cd1b1-b423df52eace6fae7c.jpg",
)
