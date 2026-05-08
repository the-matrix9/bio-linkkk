from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import BOT_OWNER_ID, START_IMG
from database import get_logs_for_chat, get_recent_logs, get_user_count, get_chat_count, is_admin
from helpers import fmt_time, safe_edit

ACTION_ICONS = {
    "WARN": "⚠️", "WARN_RESET": "❌⚠️", "MUTE": "🔇", "UNMUTE": "🔊",
    "BAN": "🔨", "UNBAN": "✅", "GBAN": "🌐🔨", "UNGBAN": "🌐✅",
    "PIN": "📌", "UNPIN": "📌❌", "WLADD": "✅📋", "WLREM": "🚫📋",
}

def fmt_log(doc) -> str:
    icon   = ACTION_ICONS.get(doc.get("action", ""), "🔔")
    line   = f"{icon} <b>{doc.get('action','?')}</b> — <code>{doc.get('target_name','?')}</code> (<code>{doc.get('target_id','?')}</code>)"
    chat   = doc.get("chat_title", "")
    if chat and chat != "GLOBAL":
        line += f"\n   👥 {chat}"
    reason = doc.get("reason", "")
    if reason:
        line += f"\n   📝 {reason}"
    if "ts" in doc:
        line += f"\n   🕐 {fmt_time(doc['ts'])}"
    return line


@Client.on_message(filters.group & filters.command("logs"))
async def cmd_logs(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ ᴀᴅᴍɪɴ ᴏɴʟʏ!")
    docs = await get_logs_for_chat(message.chat.id, limit=15)
    if not docs:
        return await message.reply_text("<b>📋 ɴᴏ ʟᴏɢs ʏᴇᴛ.</b>")
    text = f"<b>📋 ʟᴏɢs — {message.chat.title}</b>\n━━━━━━━━━━━━━━━━\n\n"
    text += "\n\n".join(fmt_log(d) for d in docs)
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")]]))


@Client.on_message(filters.command("alogs"))
async def cmd_alogs(client: Client, message: Message):
    if message.from_user.id != BOT_OWNER_ID:
        return await message.reply_text("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")
    docs = await get_recent_logs(limit=20)
    if not docs:
        return await message.reply_text("<b>📋 ɴᴏ ʟᴏɢs ʏᴇᴛ.</b>")
    text = "<b>📋 ɢʟᴏʙᴀʟ ʟᴏɢs (ʟᴀsᴛ 20)</b>\n━━━━━━━━━━━━━━━━\n\n"
    text += "\n\n".join(fmt_log(d) for d in docs)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")]])
    if len(text) > 4000:
        for part in [text[i:i+4000] for i in range(0, len(text), 4000)]:
            await message.reply_text(part, reply_markup=kb)
    else:
        await message.reply_text(text, reply_markup=kb)


@Client.on_message(filters.command("stats"))
async def cmd_stats(client: Client, message: Message):
    if message.from_user.id != BOT_OWNER_ID:
        return await message.reply_text("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")
    users = await get_user_count()
    chats = await get_chat_count()
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 ʀᴇꜰʀᴇsʜ", callback_data="show_stats"),
        InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",   callback_data="close"),
    ]])
    try:
        await client.send_photo(message.chat.id, START_IMG,
            caption=f"<b>📊 sᴛᴀᴛs</b>\n\n👤 ᴜsᴇʀs: <b>{users}</b>\n👥 ɢʀᴏᴜᴘs: <b>{chats}</b>",
            reply_markup=kb)
    except Exception:
        await message.reply_text(f"<b>📊 sᴛᴀᴛs</b>\n\n👤 ᴜsᴇʀs: <b>{users}</b>\n👥 ɢʀᴏᴜᴘs: <b>{chats}</b>", reply_markup=kb)


@Client.on_callback_query(filters.regex(r"^show_stats$"))
async def cb_show_stats(client: Client, cq: CallbackQuery):
    if cq.from_user.id != BOT_OWNER_ID:
        return await cq.answer("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!", show_alert=True)
    users = await get_user_count()
    chats = await get_chat_count()
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 ʀᴇꜰʀᴇsʜ", callback_data="show_stats"),
        InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",   callback_data="close"),
    ]])
    await safe_edit(cq.message, f"<b>📊 sᴛᴀᴛs</b>\n\n👤 ᴜsᴇʀs: <b>{users}</b>\n👥 ɢʀᴏᴜᴘs: <b>{chats}</b>", kb)
    await cq.answer("✅ ʀᴇꜰʀᴇsʜᴇᴅ")
