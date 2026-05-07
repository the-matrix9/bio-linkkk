"""
broadcast.py — /broadcast (owner only, reply to any msg)
Flags: -users, -groups, (none = both)
"""

import asyncio

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import BOT_OWNER_ID
from database import get_all_users, get_all_chats


def register(app: Client):

    @app.on_message(filters.command("broadcast") & filters.private)
    async def cmd_broadcast(client: Client, message: Message):
        if message.from_user.id != BOT_OWNER_ID:
            return await message.reply_text("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")

        if not message.reply_to_message:
            return await message.reply_text(
                "<b>📡 ʙʀᴏᴀᴅᴄᴀsᴛ ᴜsᴀɢᴇ:</b>\n\n"
                "ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ ᴍsɢ + /broadcast\n\n"
                "<b>ꜰʟᴀɢs:</b>\n"
                "  <code>-users</code>  → ᴜsᴇʀs ᴏɴʟʏ\n"
                "  <code>-groups</code> → ɢʀᴏᴜᴘs ᴏɴʟʏ\n"
                "  <i>(ɴᴏɴᴇ)</i>        → ʙᴏᴛʜ"
            )

        flags     = [c.lower() for c in message.command[1:]]
        do_users  = "-groups" not in flags
        do_groups = "-users"  not in flags
        fwd       = message.reply_to_message

        status = await message.reply_text("📡 <b>ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ...</b>")

        ok_u = fail_u = ok_g = fail_g = 0

        if do_users:
            for uid in await get_all_users():
                try:
                    await fwd.forward(uid)
                    ok_u += 1
                except Exception:
                    fail_u += 1
                await asyncio.sleep(0.05)

        if do_groups:
            for cid in await get_all_chats():
                try:
                    await fwd.forward(cid)
                    ok_g += 1
                except Exception:
                    fail_g += 1
                await asyncio.sleep(0.05)

        total_ok   = ok_u + ok_g
        total_fail = fail_u + fail_g

        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")]])
        await status.edit_text(
            "<b>✅ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ!</b>\n\n"
            f"👤 <b>ᴜsᴇʀs:</b>  ✅ {ok_u}  ❌ {fail_u}\n"
            f"👥 <b>ɢʀᴏᴜᴘs:</b> ✅ {ok_g}  ❌ {fail_g}\n"
            f"━━━━━━━━━━━━━\n"
            f"📊 <b>ᴛᴏᴛᴀʟ:</b>  ✅ {total_ok}  ❌ {total_fail}",
            reply_markup=kb,
        )
