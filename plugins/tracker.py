"""
tracker.py — Auto-save users & chats, send group join alert, handle bot kick
"""

from pyrogram import Client, filters
from pyrogram.types import Message

from config import BOT_OWNER_ID, LOG_CHANNEL, START_IMG
from database import save_user, save_chat, remove_chat, get_pin_state, get_pin_msg_id


def register(app: Client):

    @app.on_message(filters.private & ~filters.bot)
    async def track_user(client: Client, message: Message):
        if message.from_user:
            await save_user(message.from_user.id)

    @app.on_message(filters.group & ~filters.service)
    async def track_chat(client: Client, message: Message):
        if message.chat:
            await save_chat(message.chat.id, message.chat.title or "")
        if message.from_user:
            await save_user(message.from_user.id)

    @app.on_message(filters.new_chat_members)
    async def on_new_member(client: Client, message: Message):
        me = await client.get_me()
        chat = message.chat
        await save_chat(chat.id, chat.title or "")

        # Check if BOT itself just joined a new group
        for member in (message.new_chat_members or []):
            if member.id == me.id:
                # Send join alert to owner
                alert = (
                    f"<b>📥 ʙᴏᴛ ᴀᴅᴅᴇᴅ ᴛᴏ ɴᴇᴡ ɢʀᴏᴜᴘ!</b>\n\n"
                    f"👥 <b>ɢʀᴏᴜᴘ:</b> {chat.title}\n"
                    f"🆔 <b>ɪᴅ:</b> <code>{chat.id}</code>\n"
                    f"👤 <b>ᴀᴅᴅᴇᴅ ʙʏ:</b> {message.from_user.mention if message.from_user else 'Unknown'}\n"
                    f"👥 <b>ᴍᴇᴍʙᴇʀs:</b> {chat.members_count or '?'}"
                )
                if BOT_OWNER_ID:
                    try:
                        await client.send_photo(BOT_OWNER_ID, START_IMG, caption=alert)
                    except Exception:
                        try:
                            await client.send_message(BOT_OWNER_ID, alert)
                        except Exception:
                            pass
                if LOG_CHANNEL:
                    try:
                        await client.send_message(LOG_CHANNEL, alert)
                    except Exception:
                        pass

                # Send start message in the group itself
                from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                from config import SUPPORT_GROUP, BOT_OWNER_USERNAME
                bot = await client.get_me()
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📖 ᴄᴏᴍᴍᴀɴᴅs", callback_data="help_menu"),
                     InlineKeyboardButton("🧬 ᴇɴᴀʙʟᴇ ʙɪᴏ", callback_data="togglebio_on")],
                    [
                        InlineKeyboardButton("🛠️ sᴜᴘᴘᴏʀᴛ", url=SUPPORT_GROUP),
                        InlineKeyboardButton("👤 ᴏᴡɴᴇʀ", url=f"https://t.me/{BOT_OWNER_USERNAME}"),
                    ],
                ])
                greet = (
                    f"<b>🛡️ ʜᴇʟʟᴏ {chat.title}!</b>\n\n"
                    "ɪ'ᴍ <b>ʙɪᴏ ʟɪɴᴋ ᴘʀᴏᴛᴇᴄᴛᴏʀ</b> — ɪ ᴅᴇᴛᴇᴄᴛ & ᴘᴜɴɪsʜ ᴜsᴇʀs\n"
                    "ᴡʜᴏ ʜᴀᴠᴇ ʟɪɴᴋs/@ᴜsᴇʀɴᴀᴍᴇs ɪɴ ᴛʜᴇɪʀ ʙɪᴏ.\n\n"
                    "ᴜsᴇ /bio ᴛᴏ ᴇɴᴀʙʟᴇ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ.\n"
                    "<b>ʙɪᴏ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ ɪs ᴏꜰꜰ ʙʏ ᴅᴇꜰᴀᴜʟᴛ.</b>"
                )
                try:
                    await client.send_photo(chat.id, START_IMG, caption=greet, reply_markup=kb)
                except Exception:
                    try:
                        await client.send_message(chat.id, greet, reply_markup=kb)
                    except Exception:
                        pass

        # Auto-pin for non-bot members joining
        if await get_pin_state(chat.id):
            mid = await get_pin_msg_id(chat.id)
            if mid:
                try:
                    await client.pin_chat_message(chat.id, mid, disable_notification=True)
                except Exception:
                    pass

    @app.on_message(filters.left_chat_member)
    async def on_bot_kicked(client: Client, message: Message):
        me = await client.get_me()
        if message.left_chat_member and message.left_chat_member.id == me.id:
            await remove_chat(message.chat.id)
            # Alert owner
            if BOT_OWNER_ID:
                try:
                    await client.send_message(
                        BOT_OWNER_ID,
                        f"<b>⚠️ ʙᴏᴛ ᴋɪᴄᴋᴇᴅ!</b>\n\n"
                        f"👥 <b>ɢʀᴏᴜᴘ:</b> {message.chat.title}\n"
                        f"🆔 <code>{message.chat.id}</code>",
                    )
                except Exception:
                    pass
