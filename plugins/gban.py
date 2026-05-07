"""
gban.py — /aban (global ban from all groups) + /aungban
Owner only. Bans user from every group where bot has ban permission.
"""

import asyncio

from pyrogram import Client, filters, errors
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import BOT_OWNER_ID, LOG_CHANNEL
from database import (
    gban_user, ungban_user, is_gbanned, get_gban_reason,
    get_all_chats_with_title,
)
from helpers import mlink, fullname, resolve_target, log_action, send_log


def register(app: Client):

    @app.on_message(filters.command("aban"))
    async def cmd_aban(client: Client, message: Message):
        """Global ban — bans user from ALL groups where bot has ban permission."""
        if message.from_user.id != BOT_OWNER_ID:
            return await message.reply_text("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")

        target = await resolve_target(client, message)
        if not target:
            return await message.reply_text(
                "<b>ᴜsᴀɢᴇ:</b> ʀᴇᴘʟʏ ᴏʀ\n"
                "<code>/aban @user / user_id [reason]</code>"
            )

        # Can't gban self or bot
        me = await client.get_me()
        if target.id in (BOT_OWNER_ID, me.id):
            return await message.reply_text("❌ ᴄᴀɴ'ᴛ ɢʙᴀɴ ᴛʜɪs ᴜsᴇʀ!")

        # Parse reason (everything after @user/id)
        reason = " ".join(message.command[2:]) if len(message.command) > 2 else "No reason"
        name   = fullname(target)
        umen   = mlink(name, target.id)

        # Mark in DB
        await gban_user(target.id, reason)

        status = await message.reply_text(
            f"🌐🔨 <b>ɢʟᴏʙᴀʟ ʙᴀɴ ɪɴɪᴛɪᴀᴛᴇᴅ ꜰᴏʀ {umen}</b>\n"
            f"📝 ʀᴇᴀsᴏɴ: {reason}\n\n"
            "<i>ʙᴀɴɴɪɴɢ ꜰʀᴏᴍ ᴀʟʟ ɢʀᴏᴜᴘs...</i>"
        )

        chats = await get_all_chats_with_title()
        ok    = 0
        fail  = 0
        skipped = 0

        for chat_id, chat_title in chats:
            try:
                await client.ban_chat_member(chat_id, target.id)
                ok += 1
                await asyncio.sleep(0.1)
            except errors.ChatAdminRequired:
                skipped += 1
            except errors.UserNotParticipant:
                skipped += 1
            except Exception:
                fail += 1

        # Log
        await log_action(
            client, "GBAN",
            0, "GLOBAL",
            message.from_user.id, fullname(message.from_user),
            target.id, name,
            reason=reason,
        )

        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ᴜɴɢʙᴀɴ", callback_data=f"do_ungban_{target.id}"),
            InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",  callback_data="close"),
        ]])

        await status.edit_text(
            f"<b>🌐🔨 ɢʟᴏʙᴀʟ ʙᴀɴ ᴄᴏᴍᴘʟᴇᴛᴇ!</b>\n\n"
            f"👤 <b>ᴜsᴇʀ:</b> {umen}\n"
            f"📝 <b>ʀᴇᴀsᴏɴ:</b> {reason}\n\n"
            f"✅ ʙᴀɴɴᴇᴅ: <b>{ok}</b> ɢʀᴏᴜᴘs\n"
            f"⏭️ sᴋɪᴘᴘᴇᴅ: <b>{skipped}</b> (ɴᴏ ᴘᴇʀᴍ/ɴᴏᴛ ᴍᴇᴍʙᴇʀ)\n"
            f"❌ ᴇʀʀᴏʀ: <b>{fail}</b>",
            reply_markup=kb,
        )

    @app.on_message(filters.command("aungban"))
    async def cmd_aungban(client: Client, message: Message):
        """Global unban."""
        if message.from_user.id != BOT_OWNER_ID:
            return await message.reply_text("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!")

        target = await resolve_target(client, message)
        if not target:
            return await message.reply_text(
                "<b>ᴜsᴀɢᴇ:</b> ʀᴇᴘʟʏ ᴏʀ\n"
                "<code>/aungban @user / user_id</code>"
            )

        name = fullname(target)
        umen = mlink(name, target.id)

        if not await is_gbanned(target.id):
            return await message.reply_text(f"<b>ℹ️ {umen} ɪs ɴᴏᴛ ɢʙᴀɴɴᴇᴅ.</b>")

        await ungban_user(target.id)

        # Unban from all groups
        chats = await get_all_chats_with_title()
        ok = fail = 0
        for chat_id, _ in chats:
            try:
                await client.unban_chat_member(chat_id, target.id)
                ok += 1
                await asyncio.sleep(0.1)
            except Exception:
                fail += 1

        await log_action(
            client, "UNGBAN",
            0, "GLOBAL",
            message.from_user.id, fullname(message.from_user),
            target.id, name,
        )

        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")]])
        await message.reply_text(
            f"<b>🌐✅ ɢʟᴏʙᴀʟ ᴜɴʙᴀɴ ᴄᴏᴍᴘʟᴇᴛᴇ!</b>\n\n"
            f"👤 <b>ᴜsᴇʀ:</b> {umen}\n"
            f"✅ ᴜɴʙᴀɴɴᴇᴅ ꜰʀᴏᴍ: <b>{ok}</b> ɢʀᴏᴜᴘs\n"
            f"❌ ꜰᴀɪʟᴇᴅ: <b>{fail}</b>",
            reply_markup=kb,
        )

    # ── Inline ungban button ──────────────────────────────────────────────────

    @app.on_message(filters.regex(r"^do_ungban_(\d+)$"))
    async def cb_do_ungban(client: Client, cq):
        pass  # handled below via callback_query

    from pyrogram.types import CallbackQuery

    @app.on_callback_query(filters.regex(r"^do_ungban_(\d+)$"))
    async def cb_ungban_btn(client: Client, cq: CallbackQuery):
        if cq.from_user.id != BOT_OWNER_ID:
            return await cq.answer("❌ ᴏᴡɴᴇʀ ᴏɴʟʏ!", show_alert=True)

        target_id = int(cq.data.split("_")[-1])
        try:
            u    = await client.get_users(target_id)
            name = fullname(u)
        except Exception:
            name = str(target_id)
        umen = mlink(name, target_id)

        await ungban_user(target_id)
        chats = await get_all_chats_with_title()
        ok = 0
        for chat_id, _ in chats:
            try:
                await client.unban_chat_member(chat_id, target_id)
                ok += 1
                await asyncio.sleep(0.05)
            except Exception:
                pass

        from helpers import safe_edit
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")]])
        await safe_edit(
            cq.message,
            f"<b>🌐✅ {umen} ɢʟᴏʙᴀʟʟʏ ᴜɴʙᴀɴɴᴇᴅ ꜰʀᴏᴍ {ok} ɢʀᴏᴜᴘs!</b>",
            kb,
        )
        await cq.answer("✅ Ungbanned!")
