from pyrogram import Client, filters, errors
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from database import get_pin_state, set_pin_state, set_pin_msg_id, is_admin
from helpers import safe_edit, log_action, fullname


@Client.on_message(filters.group & filters.command("pin"))
async def cmd_pin(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ ᴀᴅᴍɪɴ ᴏɴʟʏ!")
    if message.reply_to_message:
        msg_id = message.reply_to_message.id
    elif len(message.command) > 1 and message.command[1].lstrip("-").isdigit():
        msg_id = abs(int(message.command[1]))
    else:
        return await message.reply_text("<b>ʀᴇᴘʟʏ ᴛᴏ ᴍsɢ ᴏʀ /pin -id</b>")
    try:
        await client.pin_chat_message(message.chat.id, msg_id, disable_notification=False)
        await set_pin_state(message.chat.id, True)
        await set_pin_msg_id(message.chat.id, msg_id)
        await log_action(client, "PIN", message.chat.id, message.chat.title or "",
                         message.from_user.id, fullname(message.from_user),
                         message.from_user.id, fullname(message.from_user),
                         reason=f"msg_id={msg_id}")
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("📌 ᴀᴜᴛᴏ-ᴘɪɴ ✅", callback_data="toggle_autopin_off"),
            InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",       callback_data="close"),
        ]])
        await message.reply_text(f"<b>📌 ᴍsɢ <code>{msg_id}</code> ᴘɪɴɴᴇᴅ!\nᴀᴜᴛᴏ-ᴘɪɴ: ✅ ON</b>", reply_markup=kb)
    except errors.ChatAdminRequired:
        await message.reply_text("❌ ɪ ɴᴇᴇᴅ <b>ᴘɪɴ ᴍsɢs</b> ᴘᴇʀᴍɪssɪᴏɴ!")
    except Exception as e:
        await message.reply_text(f"❌ <code>{e}</code>")


@Client.on_message(filters.group & filters.command("unpin"))
async def cmd_unpin(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id):
        return await message.reply_text("❌ ᴀᴅᴍɪɴ ᴏɴʟʏ!")
    try:
        await client.unpin_all_chat_messages(message.chat.id)
        await set_pin_state(message.chat.id, False)
        await set_pin_msg_id(message.chat.id, None)
        await log_action(client, "UNPIN", message.chat.id, message.chat.title or "",
                         message.from_user.id, fullname(message.from_user),
                         message.from_user.id, fullname(message.from_user))
        await message.reply_text("<b>📌❌ ᴀʟʟ ᴍsɢs ᴜɴᴘɪɴɴᴇᴅ!</b>")
    except Exception as e:
        await message.reply_text(f"❌ <code>{e}</code>")


@Client.on_callback_query(filters.regex(r"^toggle_autopin_(on|off)$"))
async def cb_toggle_autopin(client: Client, cq: CallbackQuery):
    if not await is_admin(client, cq.message.chat.id, cq.from_user.id):
        return await cq.answer("❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!", show_alert=True)
    action = cq.data.split("_")[-1]
    await set_pin_state(cq.message.chat.id, action == "on")
    state = await get_pin_state(cq.message.chat.id)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            f"📌 ᴀᴜᴛᴏ-ᴘɪɴ {'✅ ON' if state else '❌ OFF'}",
            callback_data=f"toggle_autopin_{'off' if state else 'on'}",
        ),
        InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close"),
    ]])
    await safe_edit(cq.message, f"<b>📌 ᴀᴜᴛᴏ-ᴘɪɴ: {'✅ ON' if state else '❌ OFF'}</b>", kb)
    await cq.answer()
