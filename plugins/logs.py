"""
logs.py — /logs (group), /alogs (owner), /stats (owner)
"""

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import BOT_OWNER_ID, START_IMG
from database import (
    get_logs_for_chat, get_recent_logs,
    get_user_count, get_chat_count, is_admin,
)
from helpers import fmt_time, safe_edit


ACTION_ICONS = {
    "WARN": "⚠️", "WARN_RESET": "❌⚠️",
    "MUTE": "🔇", "UNMUTE": "🔊",
    "BAN":  "🔨", "UNBAN":  "✅",
    "GBAN": "🌐🔨", "UNGBAN": "🌐✅",
    "PIN":  "📌", "UNPIN": "📌❌",
    "WLADD": "✅📋", "WLREM": "🚫📋",
}


def fmt_log(doc) -> str:
    icon   = ACTION_ICONS.get(doc.get("action", ""), "🔔")
    action = doc.get("action", "?")
    target = doc.get("target_name", "?")
    tid    = doc.get("target_id", "?")
    chat   = doc.get("chat_title", "?")
    reason = doc.get("reason", "")
    ts     = fmt_time(doc["ts"]) if "ts" in doc else "?"
    line = f"{icon} <b>{action}</b> — <code>{target}</code> (<code>{tid}</code>)"
    if chat and chat != "GLOBAL":
        line += f"\n   👥 {chat}"
    if reason:
        line += f"\n   📝 {reason}"
    line += f"\n   🕐 {ts}"
    return line


def register(app: Client):

    # ── /logs — group action logs (admin) ─────────────────────────────────────

    @app.on_message(filters.group & filters.command("logs"))
    async def cmd_logs(client: Client, message: Message):
        chat_id = message.chat.id
        if not await is_admin(client, chat_id, message.from_user.id):
            return await message.reply_text("❌ ᴀᴅᴍɪɴ ᴏɴʟʏ!")

        docs = await get_logs_for_chat(chat_id, limit=15)
        if not docs:
            return await message.reply_text("<b>📋 ɴᴏ ʟᴏɢs ʏᴇᴛ ꜰᴏʀ ᴛʜɪs ɢʀᴏᴜᴘ.</b>")

        text = f"<b>📋 ʀᴇᴄᴇɴᴛ ʟᴏɢs — {message.chat.title}</b>\n"
        text += "━━━━━━━━━━━━━━━━━━\n\n"
        for doc in docs:
            text += fmt_log(doc) + "\n\n"

        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")]])
        await message.reply_text(text, reply_markup=kb)

    # ── /alogs — all recent logs (owner only) ─────────────────────────────────

    @app.on_message(filters.command("alogs"))
    async def cmd_alogs(client: Client, message: Message):
        if message.from_user.id != BOT_OWNER_ID:
            return await message.reply_text("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")

        docs = await get_recent_logs(limit=20)
        if not docs:
            return await message.reply_text("<b>📋 ɴᴏ ʟᴏɢs ʏᴇᴛ.</b>")

        text = "<b>📋 ɢʟᴏʙᴀʟ ʀᴇᴄᴇɴᴛ ʟᴏɢs (ʟᴀsᴛ 20)</b>\n"
        text += "━━━━━━━━━━━━━━━━━━\n\n"
        for doc in docs:
            text += fmt_log(doc) + "\n\n"

        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")]])
        # Split if too long
        if len(text) > 4000:
            parts = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for part in parts:
                await message.reply_text(part, reply_markup=kb)
        else:
            await message.reply_text(text, reply_markup=kb)

    # ── /stats (owner) ────────────────────────────────────────────────────────

    @app.on_message(filters.command("stats"))
    async def cmd_stats(client: Client, message: Message):
        if message.from_user.id != BOT_OWNER_ID:
            return await message.reply_text("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")
        await _send_stats(client, message.chat.id)

    @app.on_callback_query(filters.regex(r"^show_stats$"))
    async def cb_show_stats(client: Client, cq: CallbackQuery):
        if cq.from_user.id != BOT_OWNER_ID:
            return await cq.answer("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!", show_alert=True)
        users = await get_user_count()
        chats = await get_chat_count()
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 ʀᴇꜰʀᴇsʜ", callback_data="show_stats"),
             InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",   callback_data="close")],
        ])
        await safe_edit(
            cq.message,
            "<b>📊 ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs</b>\n\n"
            f"👤 ᴛᴏᴛᴀʟ ᴜsᴇʀs: <b>{users}</b>\n"
            f"👥 ᴛᴏᴛᴀʟ ɢʀᴏᴜᴘs: <b>{chats}</b>",
            kb,
        )
        await cq.answer("✅ ʀᴇꜰʀᴇsʜᴇᴅ")


async def _send_stats(client: Client, chat_id: int):
    users = await get_user_count()
    chats = await get_chat_count()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 ʀᴇꜰʀᴇsʜ", callback_data="show_stats"),
         InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",   callback_data="close")],
    ])
    try:
        await client.send_photo(
            chat_id, START_IMG,
            caption=(
                "<b>📊 ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs</b>\n\n"
                f"👤 ᴛᴏᴛᴀʟ ᴜsᴇʀs: <b>{users}</b>\n"
                f"👥 ᴛᴏᴛᴀʟ ɢʀᴏᴜᴘs: <b>{chats}</b>"
            ),
            reply_markup=kb,
        )
    except Exception:
        await client.send_message(
            chat_id,
            "<b>📊 ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs</b>\n\n"
            f"👤 ᴛᴏᴛᴀʟ ᴜsᴇʀs: <b>{users}</b>\n"
            f"👥 ᴛᴏᴛᴀʟ ɢʀᴏᴜᴘs: <b>{chats}</b>",
            reply_markup=kb,
        )
