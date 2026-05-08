from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from database import (
    add_whitelist, remove_whitelist, get_whitelist, is_whitelisted,
    reset_warnings, get_warnings, get_config, is_admin,
)
from helpers import mlink, fullname, resolve_target, log_action


@Client.on_message(filters.group & filters.command("free"))
async def cmd_free(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id): return
    target = await resolve_target(client, message)
    if not target:
        return await message.reply_text("<b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴏʀ: /free @user</b>")
    await add_whitelist(message.chat.id, target.id)
    await reset_warnings(message.chat.id, target.id)
    await log_action(client, "WLADD", message.chat.id, message.chat.title or "",
                     message.from_user.id, fullname(message.from_user), target.id, fullname(target))
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🚫 ʀᴇᴍᴏᴠᴇ", callback_data=f"unwhitelist_{target.id}"),
        InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",  callback_data="close"),
    ]])
    await message.reply_text(f"<b>✅ {mlink(fullname(target), target.id)} ᴀᴅᴅᴇᴅ ᴛᴏ ᴡʜɪᴛᴇʟɪsᴛ!</b>", reply_markup=kb)


@Client.on_message(filters.group & filters.command("unfree"))
async def cmd_unfree(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id): return
    target = await resolve_target(client, message)
    if not target:
        return await message.reply_text("<b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴏʀ: /unfree @user</b>")
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ", callback_data=f"whitelist_{target.id}"),
        InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",     callback_data="close"),
    ]])
    if await is_whitelisted(message.chat.id, target.id):
        await remove_whitelist(message.chat.id, target.id)
        await log_action(client, "WLREM", message.chat.id, message.chat.title or "",
                         message.from_user.id, fullname(message.from_user), target.id, fullname(target))
        text = f"<b>🚫 {mlink(fullname(target), target.id)} ʀᴇᴍᴏᴠᴇᴅ!</b>"
    else:
        text = f"<b>ℹ️ {mlink(fullname(target), target.id)} ɴᴏᴛ ɪɴ ᴡʜɪᴛᴇʟɪsᴛ.</b>"
    await message.reply_text(text, reply_markup=kb)


@Client.on_message(filters.group & filters.command("freelist"))
async def cmd_freelist(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id): return
    ids = await get_whitelist(message.chat.id)
    if not ids:
        return await message.reply_text("<b>📋 ɴᴏ ᴡʜɪᴛᴇʟɪsᴛᴇᴅ ᴜsᴇʀs.</b>")
    lines = f"<b>📋 ᴡʜɪᴛᴇʟɪsᴛᴇᴅ ({len(ids)}):</b>\n\n"
    for i, uid in enumerate(ids, 1):
        try: name = fullname(await client.get_users(uid))
        except Exception: name = "Unknown"
        lines += f"{i}. {mlink(name, uid)} — <code>{uid}</code>\n"
    await message.reply_text(lines, reply_markup=InlineKeyboardMarkup([[
        InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")]]))


@Client.on_message(filters.group & filters.command("warns"))
async def cmd_warns(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id): return
    target = await resolve_target(client, message)
    if not target:
        return await message.reply_text("<b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴜsᴇʀ ᴏʀ: /warns @user</b>")
    _, limit, _ = await get_config(message.chat.id)
    count = await get_warnings(message.chat.id, target.id)
    wbar  = "🟥" * count + "⬜" * max(0, limit - count)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ ʀᴇsᴇᴛ", callback_data=f"cancel_warn_{target.id}"),
        InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ", callback_data=f"whitelist_{target.id}"),
        InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",     callback_data="close"),
    ]])
    await message.reply_text(
        f"<b>⚠️ {mlink(fullname(target), target.id)}\nᴡᴀʀɴs: {count}/{limit}  {wbar}</b>",
        reply_markup=kb,
    )
