"""
bio.py — Bio protection watcher, /bio toggle, /config
"""

import re
from pyrogram import Client, filters, errors
from pyrogram.types import (
    CallbackQuery, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup, Message,
)

from config import BOT_OWNER_ID, START_IMG
from database import (
    get_bio_state, set_bio_state,
    get_config, update_config,
    get_warnings, increment_warning, reset_warnings,
    add_whitelist, is_whitelisted, is_admin,
)
from helpers import admin_gate, mlink, fullname, safe_edit, log_action

URL_PATTERN = re.compile(
    r"(https?://|www\.)[a-zA-Z0-9\-.]+"
    r"\.[a-zA-Z]{2,}(?:/[^\s]*)?|@[\w]{4,}",
    re.IGNORECASE,
)


def register(app: Client):

    # ── /bio ─────────────────────────────────────────────────────────────────

    def bio_kb(state: bool) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "🔴 ᴛᴜʀɴ OFF" if state else "🟢 ᴛᴜʀɴ ON",
                callback_data=f"togglebio_{'off' if state else 'on'}",
            )],
            [
                InlineKeyboardButton("⚙️ ᴄᴏɴꜰɪɢ", callback_data="open_config"),
                InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",  callback_data="close"),
            ],
        ])

    @app.on_message(filters.group & filters.command("bio"))
    async def cmd_bio(client: Client, message: Message):
        chat_id = message.chat.id
        if not await is_admin(client, chat_id, message.from_user.id):
            return await message.reply_text("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!")
        if len(message.command) > 1 and message.command[1].lower() in ("status", "state"):
            s = await get_bio_state(chat_id)
            return await message.reply_text(
                f"<b>🧬 ʙɪᴏ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ:</b> {'🟢 ON' if s else '🔴 OFF'}"
            )
        state = await get_bio_state(chat_id)
        _, limit, penalty = await get_config(chat_id)
        text = (
            f"<b>🧬 ʙɪᴏ ʟɪɴᴋ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ:</b> {'🟢 ON' if state else '🔴 OFF'}\n"
            f"<b>⚠️ ᴡᴀʀɴ ʟɪᴍɪᴛ:</b> {limit}  |  <b>⚖️ ᴘᴇɴᴀʟᴛʏ:</b> {penalty.upper()}"
        )
        await message.reply_text(text, reply_markup=bio_kb(state))

    @app.on_callback_query(filters.regex(r"^togglebio_(on|off)$"))
    async def cb_togglebio(client: Client, cq: CallbackQuery):
        if not await admin_gate(client, cq): return
        action  = cq.data.split("_")[1]
        chat_id = cq.message.chat.id
        await set_bio_state(chat_id, action == "on")
        state = await get_bio_state(chat_id)
        _, limit, penalty = await get_config(chat_id)
        text = (
            f"<b>🧬 ʙɪᴏ ʟɪɴᴋ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ ɪs ɴᴏᴡ:</b> {'🟢 ON' if state else '🔴 OFF'}\n"
            f"<b>⚠️ ᴡᴀʀɴ ʟɪᴍɪᴛ:</b> {limit}  |  <b>⚖️ ᴘᴇɴᴀʟᴛʏ:</b> {penalty.upper()}"
        )
        await safe_edit(cq.message, text, bio_kb(state))
        await cq.answer("✅ ᴛᴏɢɢʟᴇᴅ!")

    # ── /config ───────────────────────────────────────────────────────────────

    def config_kb(penalty: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("⚠️ ᴡᴀʀɴ ʟɪᴍɪᴛ", callback_data="warn_menu")],
            [
                InlineKeyboardButton("🔇 ᴍᴜᴛᴇ" + (" ✅" if penalty == "mute" else ""), callback_data="set_mute"),
                InlineKeyboardButton("🔨 ʙᴀɴ"  + (" ✅" if penalty == "ban"  else ""), callback_data="set_ban"),
            ],
            [InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")],
        ])

    def config_text(limit, penalty):
        return (
            "<b>⚙️ ʙɪᴏ ᴘʀᴏᴛᴇᴄᴛᴏʀ ᴄᴏɴꜰɪɢ</b>\n\n"
            f"📊 ᴡᴀʀɴ ʟɪᴍɪᴛ: <b>{limit}</b>\n"
            f"⚖️ ᴘᴇɴᴀʟᴛʏ: <b>{penalty.upper()}</b>\n\n"
            "ᴄʜᴏᴏsᴇ ᴘᴇɴᴀʟᴛʏ ᴏʀ sᴇᴛ ᴡᴀʀɴ ʟɪᴍɪᴛ:"
        )

    @app.on_message(filters.group & filters.command("config"))
    async def cmd_config(client: Client, message: Message):
        chat_id = message.chat.id
        if not await is_admin(client, chat_id, message.from_user.id): return
        _, limit, penalty = await get_config(chat_id)
        text = config_text(limit, penalty)
        try:
            await client.send_photo(chat_id, START_IMG, caption=text, reply_markup=config_kb(penalty))
        except Exception:
            await message.reply_text(text, reply_markup=config_kb(penalty))
        try: await message.delete()
        except Exception: pass

    @app.on_callback_query(filters.regex(r"^open_config$"))
    async def cb_open_config(client: Client, cq: CallbackQuery):
        if not await admin_gate(client, cq): return
        _, limit, penalty = await get_config(cq.message.chat.id)
        await safe_edit(cq.message, config_text(limit, penalty), config_kb(penalty))
        await cq.answer()

    @app.on_callback_query(filters.regex(r"^set_(mute|ban)$"))
    async def cb_set_penalty(client: Client, cq: CallbackQuery):
        if not await admin_gate(client, cq): return
        action  = cq.data.split("_")[1]
        chat_id = cq.message.chat.id
        await update_config(chat_id, penalty=action)
        _, limit, penalty = await get_config(chat_id)
        await safe_edit(cq.message, config_text(limit, penalty), config_kb(penalty))
        await cq.answer(f"✅ ᴘᴇɴᴀʟᴛʏ → {action.upper()}")

    def warn_limit_kb(selected: int) -> InlineKeyboardMarkup:
        def btn(n):
            return InlineKeyboardButton(f"{n} ✅" if n == selected else str(n), callback_data=f"setwarn_{n}")
        return InlineKeyboardMarkup([
            [btn(3), btn(4), btn(5)],
            [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="config_back"),
             InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")],
        ])

    @app.on_callback_query(filters.regex(r"^warn_menu$"))
    async def cb_warn_menu(client: Client, cq: CallbackQuery):
        if not await admin_gate(client, cq): return
        _, limit, _ = await get_config(cq.message.chat.id)
        await safe_edit(cq.message, "<b>sᴇʟᴇᴄᴛ ᴡᴀʀɴ ʟɪᴍɪᴛ:</b>", warn_limit_kb(limit))
        await cq.answer()

    @app.on_callback_query(filters.regex(r"^setwarn_(3|4|5)$"))
    async def cb_setwarn(client: Client, cq: CallbackQuery):
        if not await admin_gate(client, cq): return
        count = int(cq.data.split("_")[1])
        await update_config(cq.message.chat.id, limit=count)
        await safe_edit(cq.message, f"<b>✅ ᴡᴀʀɴ ʟɪᴍɪᴛ sᴇᴛ ᴛᴏ <code>{count}</code></b>", warn_limit_kb(count))
        await cq.answer(f"✅ Warn limit → {count}")

    @app.on_callback_query(filters.regex(r"^config_back$"))
    async def cb_config_back(client: Client, cq: CallbackQuery):
        if not await admin_gate(client, cq): return
        _, limit, penalty = await get_config(cq.message.chat.id)
        await safe_edit(cq.message, config_text(limit, penalty), config_kb(penalty))
        await cq.answer()

    # ── BIO WATCHER ───────────────────────────────────────────────────────────

    @app.on_message(filters.group & ~filters.service)
    async def bio_watcher(client: Client, message: Message):
        if not message or not message.from_user: return
        if message.from_user.is_bot: return

        chat_id = message.chat.id
        user_id = message.from_user.id

        # Skip owner
        if user_id == BOT_OWNER_ID:
            return

        if not await get_bio_state(chat_id):
            return

        try:
            if await is_admin(client, chat_id, user_id): return
            if await is_whitelisted(chat_id, user_id):   return
        except Exception:
            return

        try:
            user = await client.get_chat(user_id)
        except Exception:
            return

        bio  = user.bio or ""
        name = fullname(user)
        umen = mlink(name, user_id)

        if not URL_PATTERN.search(bio):
            await reset_warnings(chat_id, user_id)
            return

        # ── URL found ─────────────────────────────────────────────────────────
        try:
            await message.delete()
        except errors.MessageDeleteForbidden:
            await message.reply_text("⚠️ ɢɪᴠᴇ ᴍᴇ ᴅᴇʟᴇᴛᴇ ᴘᴇʀᴍɪssɪᴏɴ!")
            return
        except Exception:
            pass

        mode, limit, penalty = await get_config(chat_id)
        chat_title = message.chat.title or str(chat_id)
        actor_name = "ʙɪᴏ ʙᴏᴛ (ᴀᴜᴛᴏ)"
        me = await client.get_me()

        count = await increment_warning(chat_id, user_id)

        warn_text = (
            "<b>🚨 ᴡᴀʀɴɪɴɢ ɪssᴜᴇᴅ!</b>\n\n"
            f"👤 <b>ᴜsᴇʀ:</b> {umen}\n"
            "❌ <b>ʀᴇᴀsᴏɴ:</b> ʟɪɴᴋ/@ᴜsᴇʀɴᴀᴍᴇ ɪɴ ʙɪᴏ\n"
            f"⚠️ <b>ᴡᴀʀɴs:</b> {count}/{limit}\n\n"
            "<i>ʀᴇᴍᴏᴠᴇ ᴛʜᴇ ʟɪɴᴋ ꜰʀᴏᴍ ʏᴏᴜʀ ʙɪᴏ ᴛᴏ ᴀᴠᴏɪᴅ ᴘᴇɴᴀʟᴛʏ.</i>"
        )
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴡᴀʀɴ", callback_data=f"cancel_warn_{user_id}"),
                InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ",   callback_data=f"whitelist_{user_id}"),
            ],
            [InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")],
        ])
        sent = await message.reply_text(warn_text, reply_markup=kb)

        # Log warn
        await log_action(
            client, "WARN", chat_id, chat_title,
            me.id, "BioBot", user_id, name,
            reason=f"Link in bio | warn {count}/{limit}",
        )

        if count >= limit:
            ok = False
            try:
                if penalty == "mute":
                    await client.restrict_chat_member(chat_id, user_id, ChatPermissions())
                    ok = True
                    action_done = "MUTE"
                    action_label = f"🔇 ᴍᴜᴛᴇᴅ"
                    ub = InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔊 ᴜɴᴍᴜᴛᴇ",    callback_data=f"unmute_{user_id}"),
                        InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ", callback_data=f"whitelist_{user_id}"),
                    ]])
                else:
                    await client.ban_chat_member(chat_id, user_id)
                    ok = True
                    action_done = "BAN"
                    action_label = f"🔨 ʙᴀɴɴᴇᴅ"
                    ub = InlineKeyboardMarkup([[
                        InlineKeyboardButton("✅ ᴜɴʙᴀɴ", callback_data=f"unban_{user_id}"),
                    ]])
                if ok:
                    await sent.edit_text(
                        f"<b>{action_label}! {umen}</b>\n⚠️ ʀᴇᴀᴄʜᴇᴅ {count}/{limit} ᴡᴀʀɴs\n❌ ʟɪɴᴋ ɪɴ ʙɪᴏ",
                        reply_markup=ub,
                    )
                    await log_action(
                        client, action_done, chat_id, chat_title,
                        me.id, "BioBot", user_id, name,
                        reason=f"Reached warn limit {count}/{limit}",
                    )
            except errors.ChatAdminRequired:
                await sent.edit_text("<b>❌ ɪ ʟᴀᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ ᴀᴘᴘʟʏ ᴘᴇɴᴀʟᴛʏ!</b>")
            except Exception:
                pass

    # ── Warn / whitelist callbacks ────────────────────────────────────────────

    @app.on_callback_query(filters.regex(r"^cancel_warn_(\d+)$"))
    async def cb_cancel_warn(client: Client, cq: CallbackQuery):
        if not await admin_gate(client, cq): return
        target_id = int(cq.data.split("_")[-1])
        chat_id   = cq.message.chat.id
        await reset_warnings(chat_id, target_id)
        try:
            u    = await client.get_users(target_id)
            name = fullname(u)
        except Exception:
            name = str(target_id)
        await log_action(
            client, "WARN_RESET", chat_id, cq.message.chat.title or "",
            cq.from_user.id, fullname(cq.from_user), target_id, name,
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ", callback_data=f"whitelist_{target_id}"),
            InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",     callback_data="close"),
        ]])
        await safe_edit(cq.message, f"<b>✅ {mlink(name, target_id)} — ᴡᴀʀɴs ʀᴇsᴇᴛ!</b>", kb)
        await cq.answer("✅ Warns reset!")

    @app.on_callback_query(filters.regex(r"^(whitelist|unwhitelist)_(\d+)$"))
    async def cb_toggle_whitelist(client: Client, cq: CallbackQuery):
        if not await admin_gate(client, cq): return
        action, uid_s = cq.data.split("_", 1)
        target_id = int(uid_s)
        chat_id   = cq.message.chat.id
        try:
            u    = await client.get_users(target_id)
            name = fullname(u)
        except Exception:
            name = str(target_id)
        if action == "whitelist":
            await add_whitelist(chat_id, target_id)
            await reset_warnings(chat_id, target_id)
            await log_action(
                client, "WLADD", chat_id, cq.message.chat.title or "",
                cq.from_user.id, fullname(cq.from_user), target_id, name,
            )
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("🚫 ʀᴇᴍᴏᴠᴇ", callback_data=f"unwhitelist_{target_id}"),
                InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",  callback_data="close"),
            ]])
            await safe_edit(cq.message, f"<b>✅ {mlink(name, target_id)} ᴡʜɪᴛᴇʟɪsᴛᴇᴅ!</b>", kb)
        else:
            from database import remove_whitelist
            await remove_whitelist(chat_id, target_id)
            await log_action(
                client, "WLREM", chat_id, cq.message.chat.title or "",
                cq.from_user.id, fullname(cq.from_user), target_id, name,
            )
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ", callback_data=f"whitelist_{target_id}"),
                InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",     callback_data="close"),
            ]])
            await safe_edit(cq.message, f"<b>🚫 {mlink(name, target_id)} ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴡʜɪᴛᴇʟɪsᴛ.</b>", kb)
        await cq.answer()

    @app.on_callback_query(filters.regex(r"^(unmute|unban)_(\d+)$"))
    async def cb_unpunish(client: Client, cq: CallbackQuery):
        if not await admin_gate(client, cq): return
        action, uid_s = cq.data.split("_", 1)
        target_id = int(uid_s)
        chat_id   = cq.message.chat.id
        try:
            u    = await client.get_users(target_id)
            name = fullname(u)
        except Exception:
            name = str(target_id)
        try:
            if action == "unmute":
                await client.restrict_chat_member(
                    chat_id, target_id,
                    ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_other_messages=True,
                        can_add_web_page_previews=True,
                    ),
                )
                label = "ᴜɴᴍᴜᴛᴇᴅ 🔊"
                action_key = "UNMUTE"
            else:
                await client.unban_chat_member(chat_id, target_id)
                label = "ᴜɴʙᴀɴɴᴇᴅ ✅"
                action_key = "UNBAN"
            await reset_warnings(chat_id, target_id)
            await log_action(
                client, action_key, chat_id, cq.message.chat.title or "",
                cq.from_user.id, fullname(cq.from_user), target_id, name,
            )
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ", callback_data=f"whitelist_{target_id}"),
                InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",     callback_data="close"),
            ]])
            await safe_edit(cq.message, f"<b>{mlink(name, target_id)} ʜᴀs ʙᴇᴇɴ {label}!</b>", kb)
        except errors.ChatAdminRequired:
            await safe_edit(cq.message, "<b>❌ ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ!</b>")
        except Exception:
            pass
        await cq.answer()
