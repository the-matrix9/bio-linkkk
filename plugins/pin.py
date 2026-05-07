"""
pin.py — /pin /unpin + auto-pin callback
"""

from pyrogram import Client, filters, errors
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from database import get_pin_state, set_pin_state, get_pin_msg_id, set_pin_msg_id, is_admin
from helpers import admin_gate, safe_edit, log_action, fullname


def register(app: Client):

    @app.on_message(filters.group & filters.command("pin"))
    async def cmd_pin(client: Client, message: Message):
        chat_id = message.chat.id
        if not await is_admin(client, chat_id, message.from_user.id):
            return await message.reply_text("❌ ᴀᴅᴍɪɴ ᴏɴʟʏ!")

        if message.reply_to_message:
            msg_id = message.reply_to_message.id
        elif len(message.command) > 1 and message.command[1].lstrip("-").isdigit():
            msg_id = abs(int(message.command[1]))
        else:
            return await message.reply_text(
                "<b>📌 ᴜsᴀɢᴇ:</b>\n"
                "• ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍsɢ + <code>/pin</code>\n"
                "• <code>/pin -&lt;message_id&gt;</code>"
            )

        try:
            await client.pin_chat_message(chat_id, msg_id, disable_notification=False)
            await set_pin_state(chat_id, True)
            await set_pin_msg_id(chat_id, msg_id)

            await log_action(
                client, "PIN", chat_id, message.chat.title or "",
                message.from_user.id, fullname(message.from_user),
                message.from_user.id, fullname(message.from_user),
                reason=f"Pinned msg_id={msg_id}",
            )

            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("📌 ᴀᴜᴛᴏ-ᴘɪɴ ✅ ON", callback_data="toggle_autopin_off"),
                InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close"),
            ]])
            await message.reply_text(
                f"<b>📌 ᴍsɢ <code>{msg_id}</code> ᴘɪɴɴᴇᴅ!</b>\n"
                "<i>ᴀᴜᴛᴏ-ᴘɪɴ ᴏɴ ɴᴇᴡ ᴊᴏɪɴs: ✅ ON</i>",
                reply_markup=kb,
            )
        except errors.ChatAdminRequired:
            await message.reply_text("❌ ɪ ɴᴇᴇᴅ <b>ᴘɪɴ ᴍᴇssᴀɢᴇs</b> ᴘᴇʀᴍɪssɪᴏɴ!")
        except Exception as e:
            await message.reply_text(f"❌ ᴇʀʀᴏʀ: <code>{e}</code>")

    @app.on_message(filters.group & filters.command("unpin"))
    async def cmd_unpin(client: Client, message: Message):
        chat_id = message.chat.id
        if not await is_admin(client, chat_id, message.from_user.id):
            return await message.reply_text("❌ ᴀᴅᴍɪɴ ᴏɴʟʏ!")
        try:
            await client.unpin_all_chat_messages(chat_id)
            await set_pin_state(chat_id, False)
            await set_pin_msg_id(chat_id, None)

            await log_action(
                client, "UNPIN", chat_id, message.chat.title or "",
                message.from_user.id, fullname(message.from_user),
                message.from_user.id, fullname(message.from_user),
                reason="Unpinned all messages",
            )
            await message.reply_text("<b>📌❌ ᴀʟʟ ᴍsɢs ᴜɴᴘɪɴɴᴇᴅ & ᴀᴜᴛᴏ-ᴘɪɴ ᴅɪsᴀʙʟᴇᴅ!</b>")
        except Exception as e:
            await message.reply_text(f"❌ ᴇʀʀᴏʀ: <code>{e}</code>")

    @app.on_callback_query(filters.regex(r"^toggle_autopin_(on|off)$"))
    async def cb_toggle_autopin(client: Client, cq: CallbackQuery):
        if not await admin_gate(client, cq): return
        action  = cq.data.split("_")[-1]
        chat_id = cq.message.chat.id
        await set_pin_state(chat_id, action == "on")
        state = await get_pin_state(chat_id)
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                f"📌 ᴀᴜᴛᴏ-ᴘɪɴ {'✅ ON' if state else '❌ OFF'}",
                callback_data=f"toggle_autopin_{'off' if state else 'on'}",
            ),
            InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close"),
        ]])
        await safe_edit(
            cq.message,
            f"<b>📌 ᴀᴜᴛᴏ-ᴘɪɴ ɪs ɴᴏᴡ: {'✅ ON' if state else '❌ OFF'}</b>",
            kb,
        )
        await cq.answer()
