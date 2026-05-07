"""
helpers.py — Shared utility functions
"""

from datetime import datetime, timezone
from pyrogram import Client, errors
from pyrogram.types import CallbackQuery, ChatPermissions, Message
from database import is_admin, save_log
from config import LOG_CHANNEL, BOT_OWNER_ID, START_IMG


# ── Text helpers ──────────────────────────────────────────────────────────────

def mlink(name: str, uid: int) -> str:
    return f"[{name}](tg://user?id={uid})"

def fullname(user) -> str:
    ln = f" {user.last_name}" if getattr(user, "last_name", None) else ""
    return f"{user.first_name}{ln}"

def fmt_time(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%d %b %Y, %H:%M UTC")


# ── Gate helpers ──────────────────────────────────────────────────────────────

async def admin_gate(client: Client, cq: CallbackQuery) -> bool:
    if not await is_admin(client, cq.message.chat.id, cq.from_user.id):
        await cq.answer("❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!", show_alert=True)
        return False
    return True

async def owner_gate(cq: CallbackQuery) -> bool:
    if cq.from_user.id != BOT_OWNER_ID:
        await cq.answer("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!", show_alert=True)
        return False
    return True


# ── Message helpers ───────────────────────────────────────────────────────────

async def safe_edit(msg, text: str, kb=None):
    try:
        if msg.photo:
            await msg.edit_caption(caption=text, reply_markup=kb, parse_mode="html")
        else:
            await msg.edit_text(text, reply_markup=kb, parse_mode="html")
    except Exception:
        pass

async def resolve_target(client: Client, message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        arg = message.command[1]
        try:
            return await client.get_users(int(arg) if arg.lstrip("-").isdigit() else arg)
        except Exception:
            return None
    return None

async def send_with_photo(client: Client, chat_id: int, text: str, kb=None):
    """Try sending with banner photo, fallback to text."""
    try:
        await client.send_photo(chat_id, START_IMG, caption=text, reply_markup=kb)
    except Exception:
        await client.send_message(chat_id, text, reply_markup=kb)


# ── Log channel sender ────────────────────────────────────────────────────────

async def send_log(client: Client, text: str):
    """Send formatted log to LOG_CHANNEL if configured."""
    if not LOG_CHANNEL:
        return
    try:
        await client.send_message(LOG_CHANNEL, text, parse_mode="html")
    except Exception:
        pass


# ── Action logger (DB + channel) ─────────────────────────────────────────────

async def log_action(
    client: Client,
    action: str,
    chat_id: int,
    chat_title: str,
    actor_id: int,
    actor_name: str,
    target_id: int,
    target_name: str,
    reason: str = "",
):
    # Save to MongoDB
    await save_log(
        action=action,
        chat_id=chat_id,
        chat_title=chat_title,
        actor_id=actor_id,
        actor_name=actor_name,
        target_id=target_id,
        target_name=target_name,
        reason=reason,
    )
    # Send to log channel
    icons = {
        "WARN":   "⚠️",
        "MUTE":   "🔇",
        "BAN":    "🔨",
        "UNBAN":  "✅",
        "UNMUTE": "🔊",
        "GBAN":   "🌐🔨",
        "UNGBAN": "🌐✅",
        "PIN":    "📌",
        "UNPIN":  "📌❌",
        "WLADD":  "✅",
        "WLREM":  "🚫",
    }
    icon = icons.get(action, "🔔")
    log_text = (
        f"{icon} <b>{action}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>ɢʀᴏᴜᴘ:</b> {chat_title} (<code>{chat_id}</code>)\n"
        f"🎯 <b>ᴛᴀʀɢᴇᴛ:</b> {mlink(target_name, target_id)} (<code>{target_id}</code>)\n"
        f"👮 <b>ʙʏ:</b> {mlink(actor_name, actor_id)} (<code>{actor_id}</code>)\n"
    )
    if reason:
        log_text += f"📝 <b>ʀᴇᴀsᴏɴ:</b> {reason}\n"
    log_text += f"🕐 <b>ᴛɪᴍᴇ:</b> {fmt_time(datetime.utcnow())}"
    await send_log(client, log_text)


# ── Punishment helper ─────────────────────────────────────────────────────────

async def apply_penalty(
    client: Client,
    chat_id: int,
    user_id: int,
    penalty: str,
) -> bool:
    """Apply mute or ban. Returns True on success."""
    try:
        if penalty == "mute":
            await client.restrict_chat_member(chat_id, user_id, ChatPermissions())
        else:
            await client.ban_chat_member(chat_id, user_id)
        return True
    except errors.ChatAdminRequired:
        return False
    except Exception:
        return False
