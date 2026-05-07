"""
database.py — All MongoDB helpers for Bio Link Protector Bot
"""

from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from pyrogram import Client, enums
from config import MONGO_URL

# ── Collections ───────────────────────────────────────────────────────────────
_client         = AsyncIOMotorClient(MONGO_URL)
db              = _client["biobot_db"]

warnings_col    = db["warnings"]
punishments_col = db["punishments"]
whitelists_col  = db["whitelists"]
bio_state_col   = db["bio_state"]
users_col       = db["users"]
chats_col       = db["chats"]
pins_col        = db["pins"]
logs_col        = db["action_logs"]
gbans_col       = db["global_bans"]

DEFAULT_WARN_LIMIT = 3
DEFAULT_PUNISHMENT = "mute"


# ═══════════════════════════════════════════════════════════════════════════════
# ██  ADMIN CHECK
# ═══════════════════════════════════════════════════════════════════════════════

async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in [
            enums.ChatMemberStatus.OWNER,
            enums.ChatMemberStatus.ADMINISTRATOR,
        ]
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# ██  USER / CHAT REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

async def save_user(user_id: int):
    await users_col.update_one(
        {"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True
    )

async def save_chat(chat_id: int, title: str = ""):
    await chats_col.update_one(
        {"chat_id": chat_id},
        {"$set": {"chat_id": chat_id, "title": title}},
        upsert=True,
    )

async def remove_chat(chat_id: int):
    await chats_col.delete_one({"chat_id": chat_id})

async def get_all_users() -> list:
    docs = await users_col.find({}).to_list(length=None)
    return [d["user_id"] for d in docs]

async def get_all_chats() -> list:
    docs = await chats_col.find({}).to_list(length=None)
    return [d["chat_id"] for d in docs]

async def get_all_chats_with_title() -> list:
    """Returns list of (chat_id, title) tuples."""
    docs = await chats_col.find({}).to_list(length=None)
    return [(d["chat_id"], d.get("title", "")) for d in docs]

async def get_user_count() -> int:
    return await users_col.count_documents({})

async def get_chat_count() -> int:
    return await chats_col.count_documents({})


# ═══════════════════════════════════════════════════════════════════════════════
# ██  BIO STATE (default OFF)
# ═══════════════════════════════════════════════════════════════════════════════

async def get_bio_state(chat_id: int) -> bool:
    doc = await bio_state_col.find_one({"chat_id": chat_id})
    return bool(doc.get("enabled", False)) if doc else False

async def set_bio_state(chat_id: int, enabled: bool):
    await bio_state_col.update_one(
        {"chat_id": chat_id}, {"$set": {"enabled": enabled}}, upsert=True
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ██  CONFIG (warn limit + penalty)
# ═══════════════════════════════════════════════════════════════════════════════

async def get_config(chat_id: int):
    doc = await punishments_col.find_one({"chat_id": chat_id})
    if doc:
        return (
            doc.get("mode", "warn"),
            doc.get("limit", DEFAULT_WARN_LIMIT),
            doc.get("penalty", DEFAULT_PUNISHMENT),
        )
    return ("warn", DEFAULT_WARN_LIMIT, DEFAULT_PUNISHMENT)

async def update_config(chat_id: int, mode=None, limit=None, penalty=None):
    upd = {}
    if mode    is not None: upd["mode"]    = mode
    if limit   is not None: upd["limit"]   = limit
    if penalty is not None: upd["penalty"] = penalty
    if upd:
        await punishments_col.update_one(
            {"chat_id": chat_id}, {"$set": upd}, upsert=True
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ██  WARNINGS
# ═══════════════════════════════════════════════════════════════════════════════

async def increment_warning(chat_id: int, user_id: int) -> int:
    await warnings_col.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$inc": {"count": 1}},
        upsert=True,
    )
    doc = await warnings_col.find_one({"chat_id": chat_id, "user_id": user_id})
    return doc["count"]

async def reset_warnings(chat_id: int, user_id: int):
    await warnings_col.delete_one({"chat_id": chat_id, "user_id": user_id})

async def get_warnings(chat_id: int, user_id: int) -> int:
    doc = await warnings_col.find_one({"chat_id": chat_id, "user_id": user_id})
    return doc["count"] if doc else 0


# ═══════════════════════════════════════════════════════════════════════════════
# ██  WHITELIST
# ═══════════════════════════════════════════════════════════════════════════════

async def is_whitelisted(chat_id: int, user_id: int) -> bool:
    return bool(await whitelists_col.find_one({"chat_id": chat_id, "user_id": user_id}))

async def add_whitelist(chat_id: int, user_id: int):
    await whitelists_col.update_one(
        {"chat_id": chat_id, "user_id": user_id},
        {"$set": {"user_id": user_id}},
        upsert=True,
    )

async def remove_whitelist(chat_id: int, user_id: int):
    await whitelists_col.delete_one({"chat_id": chat_id, "user_id": user_id})

async def get_whitelist(chat_id: int) -> list:
    docs = await whitelists_col.find({"chat_id": chat_id}).to_list(length=None)
    return [d["user_id"] for d in docs]


# ═══════════════════════════════════════════════════════════════════════════════
# ██  PIN FEATURE
# ═══════════════════════════════════════════════════════════════════════════════

async def get_pin_state(chat_id: int) -> bool:
    doc = await pins_col.find_one({"chat_id": chat_id})
    return bool(doc.get("enabled", False)) if doc else False

async def set_pin_state(chat_id: int, enabled: bool):
    await pins_col.update_one(
        {"chat_id": chat_id}, {"$set": {"enabled": enabled}}, upsert=True
    )

async def get_pin_msg_id(chat_id: int):
    doc = await pins_col.find_one({"chat_id": chat_id})
    return doc.get("msg_id") if doc else None

async def set_pin_msg_id(chat_id: int, msg_id):
    await pins_col.update_one(
        {"chat_id": chat_id}, {"$set": {"msg_id": msg_id}}, upsert=True
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ██  ACTION LOGS
# ═══════════════════════════════════════════════════════════════════════════════

async def save_log(
    action: str,
    chat_id: int,
    chat_title: str,
    actor_id: int,
    actor_name: str,
    target_id: int,
    target_name: str,
    reason: str = "",
):
    await logs_col.insert_one({
        "action":      action,
        "chat_id":     chat_id,
        "chat_title":  chat_title,
        "actor_id":    actor_id,
        "actor_name":  actor_name,
        "target_id":   target_id,
        "target_name": target_name,
        "reason":      reason,
        "ts":          datetime.utcnow(),
    })

async def get_recent_logs(limit: int = 20) -> list:
    cursor = logs_col.find({}).sort("ts", -1).limit(limit)
    return await cursor.to_list(length=limit)

async def get_logs_for_chat(chat_id: int, limit: int = 15) -> list:
    cursor = logs_col.find({"chat_id": chat_id}).sort("ts", -1).limit(limit)
    return await cursor.to_list(length=limit)


# ═══════════════════════════════════════════════════════════════════════════════
# ██  GLOBAL BAN
# ═══════════════════════════════════════════════════════════════════════════════

async def gban_user(user_id: int, reason: str = "No reason"):
    await gbans_col.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id, "reason": reason, "ts": datetime.utcnow()}},
        upsert=True,
    )

async def ungban_user(user_id: int):
    await gbans_col.delete_one({"user_id": user_id})

async def is_gbanned(user_id: int) -> bool:
    return bool(await gbans_col.find_one({"user_id": user_id}))

async def get_gban_reason(user_id: int) -> str:
    doc = await gbans_col.find_one({"user_id": user_id})
    return doc.get("reason", "") if doc else ""

async def get_all_gbanned() -> list:
    docs = await gbans_col.find({}).to_list(length=None)
    return [d["user_id"] for d in docs]
