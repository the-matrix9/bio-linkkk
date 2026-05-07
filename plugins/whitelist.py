"""
whitelist.py — /free /unfree /freelist /warns
"""

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from database import (
    add_whitelist, remove_whitelist, get_whitelist, is_whitelisted,
    reset_warnings, get_warnings, get_config, is_admin,
)
from helpers import mlink, fullname, resolve_target, log_action


def register(app: Client):

    @app.on_message(filters.group & filters.command("free"))
    async def cmd_free(client: Client, message: Message):
        chat_id = message.chat.id
        if not await is_admin(client, chat_id, message.from_user.id): return
        target = await resolve_target(client, message)
        if not target:
            return await message.reply_text("<b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴏʀ: /free @user / id</b>")
        await add_whitelist(chat_id, target.id)
        await reset_warnings(chat_id, target.id)
        await log_action(
            client, "WLADD", chat_id, message.chat.title or "",
            message.from_user.id, fullname(message.from_user),
            target.id, fullname(target),
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚫 ʀᴇᴍᴏᴠᴇ", callback_data=f"unwhitelist_{target.id}"),
            InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",  callback_data="close"),
        ]])
        await message.reply_text(
            f"<b>✅ {mlink(fullname(target), target.id)} ᴀᴅᴅᴇᴅ ᴛᴏ ᴡʜɪᴛᴇʟɪsᴛ!</b>",
            reply_markup=kb,
        )

    @app.on_message(filters.group & filters.command("unfree"))
    async def cmd_unfree(client: Client, message: Message):
        chat_id = message.chat.id
        if not await is_admin(client, chat_id, message.from_user.id): return
        target = await resolve_target(client, message)
        if not target:
            return await message.reply_text("<b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴏʀ: /unfree @user / id</b>")
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ", callback_data=f"whitelist_{target.id}"),
            InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",     callback_data="close"),
        ]])
        if await is_whitelisted(chat_id, target.id):
            await remove_whitelist(chat_id, target.id)
            await log_action(
                client, "WLREM", chat_id, message.chat.title or "",
                message.from_user.id, fullname(message.from_user),
                target.id, fullname(target),
            )
            text = f"<b>🚫 {mlink(fullname(target), target.id)} ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴡʜɪᴛᴇʟɪsᴛ!</b>"
        else:
            text = f"<b>ℹ️ {mlink(fullname(target), target.id)} ɴᴏᴛ ɪɴ ᴡʜɪᴛᴇʟɪsᴛ.</b>"
        await message.reply_text(text, reply_markup=kb)

    @app.on_message(filters.group & filters.command("freelist"))
    async def cmd_freelist(client: Client, message: Message):
        chat_id = message.chat.id
        if not await is_admin(client, chat_id, message.from_user.id): return
        ids = await get_whitelist(chat_id)
        if not ids:
            return await message.reply_text("<b>📋 ɴᴏ ᴡʜɪᴛᴇʟɪsᴛᴇᴅ ᴜsᴇʀs.</b>")
        lines = f"<b>📋 ᴡʜɪᴛᴇʟɪsᴛᴇᴅ ᴜsᴇʀs ({len(ids)}):</b>\n\n"
        for i, uid in enumerate(ids, 1):
            try:
                u = await client.get_users(uid)
                name = fullname(u)
            except Exception:
                name = "Unknown"
            lines += f"{i}. {mlink(name, uid)} — <code>{uid}</code>\n"
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")]])
        await message.reply_text(lines, reply_markup=kb)

    @app.on_message(filters.group & filters.command("warns"))
    async def cmd_warns(client: Client, message: Message):
        chat_id = message.chat.id
        if not await is_admin(client, chat_id, message.from_user.id): return
        target = await resolve_target(client, message)
        if not target:
            return await message.reply_text("<b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴏʀ: /warns @user / id</b>")
        _, limit, _ = await get_config(chat_id)
        count = await get_warnings(chat_id, target.id)
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ ʀᴇsᴇᴛ ᴡᴀʀɴs",  callback_data=f"cancel_warn_{target.id}"),
            InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ",     callback_data=f"whitelist_{target.id}"),
            InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",         callback_data="close"),
        ]])
        wbar = "🟥" * count + "⬜" * max(0, limit - count)
        await message.reply_text(
            f"<b>⚠️ {mlink(fullname(target), target.id)}</b>\n"
            f"ᴡᴀʀɴs: <b>{count}/{limit}</b>  {wbar}",
            reply_markup=kb,
        )
