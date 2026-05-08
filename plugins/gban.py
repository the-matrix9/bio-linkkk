import asyncio
from pyrogram import Client, filters, errors
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from config import BOT_OWNER_ID
from database import gban_user, ungban_user, is_gbanned, get_all_chats_with_title
from helpers import mlink, fullname, resolve_target, log_action, safe_edit


@Client.on_message(filters.command("aban"))
async def cmd_aban(client: Client, message: Message):
    if message.from_user.id != BOT_OWNER_ID:
        return await message.reply_text("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")
    target = await resolve_target(client, message)
    if not target:
        return await message.reply_text("<b>ʀᴇᴘʟʏ ᴏʀ /aban @user [reason]</b>")
    me = await client.get_me()
    if target.id in (BOT_OWNER_ID, me.id):
        return await message.reply_text("❌ ᴄᴀɴ'ᴛ ɢʙᴀɴ ᴛʜɪs ᴜsᴇʀ!")
    reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason"
    name   = fullname(target)
    umen   = mlink(name, target.id)
    await gban_user(target.id, reason)
    status = await message.reply_text(f"🌐🔨 <b>ɢʙᴀɴɴɪɴɢ {umen}...</b>")
    chats  = await get_all_chats_with_title()
    ok = fail = skipped = 0
    for chat_id, _ in chats:
        try:
            await client.ban_chat_member(chat_id, target.id)
            ok += 1
            await asyncio.sleep(0.1)
        except errors.ChatAdminRequired: skipped += 1
        except errors.UserNotParticipant: skipped += 1
        except Exception: fail += 1
    await log_action(client, "GBAN", 0, "GLOBAL",
                     message.from_user.id, fullname(message.from_user), target.id, name, reason=reason)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ ᴜɴɢʙᴀɴ", callback_data=f"do_ungban_{target.id}"),
        InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",  callback_data="close"),
    ]])
    await status.edit_text(
        f"<b>🌐🔨 ɢʙᴀɴ ᴄᴏᴍᴘʟᴇᴛᴇ!</b>\n\n"
        f"👤 {umen}\n📝 {reason}\n\n"
        f"✅ ʙᴀɴɴᴇᴅ: {ok}  ⏭️ sᴋɪᴘᴘᴇᴅ: {skipped}  ❌ ᴇʀʀᴏʀ: {fail}",
        reply_markup=kb,
    )


@Client.on_message(filters.command("aungban"))
async def cmd_aungban(client: Client, message: Message):
    if message.from_user.id != BOT_OWNER_ID:
        return await message.reply_text("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")
    target = await resolve_target(client, message)
    if not target:
        return await message.reply_text("<b>ʀᴇᴘʟʏ ᴏʀ /aungban @user</b>")
    name = fullname(target)
    umen = mlink(name, target.id)
    if not await is_gbanned(target.id):
        return await message.reply_text(f"<b>ℹ️ {umen} ɪs ɴᴏᴛ ɢʙᴀɴɴᴇᴅ.</b>")
    await ungban_user(target.id)
    chats = await get_all_chats_with_title()
    ok = 0
    for chat_id, _ in chats:
        try: await client.unban_chat_member(chat_id, target.id); ok += 1
        except Exception: pass
        await asyncio.sleep(0.05)
    await log_action(client, "UNGBAN", 0, "GLOBAL",
                     message.from_user.id, fullname(message.from_user), target.id, name)
    await message.reply_text(
        f"<b>🌐✅ {umen} ᴜɴɢʙᴀɴɴᴇᴅ ꜰʀᴏᴍ {ok} ɢʀᴏᴜᴘs!</b>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")]]),
    )


@Client.on_callback_query(filters.regex(r"^do_ungban_(\d+)$"))
async def cb_ungban_btn(client: Client, cq: CallbackQuery):
    if cq.from_user.id != BOT_OWNER_ID:
        return await cq.answer("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!", show_alert=True)
    target_id = int(cq.data.split("_")[-1])
    try: name = fullname(await client.get_users(target_id))
    except Exception: name = str(target_id)
    await ungban_user(target_id)
    chats = await get_all_chats_with_title()
    ok = 0
    for chat_id, _ in chats:
        try: await client.unban_chat_member(chat_id, target_id); ok += 1
        except Exception: pass
        await asyncio.sleep(0.05)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")]])
    await safe_edit(cq.message, f"<b>🌐✅ {mlink(name, target_id)} ᴜɴɢʙᴀɴɴᴇᴅ ꜰʀᴏᴍ {ok} ɢʀᴏᴜᴘs!</b>", kb)
    await cq.answer("✅ Done!")
