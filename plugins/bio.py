import re
from pyrogram import Client, filters, errors
from pyrogram.types import CallbackQuery, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import BOT_OWNER_ID, START_IMG
from database import (
    get_bio_state, set_bio_state, get_config, update_config,
    get_warnings, increment_warning, reset_warnings,
    add_whitelist, remove_whitelist, is_whitelisted, is_admin,
)
from helpers import mlink, fullname, safe_edit, log_action

URL_PATTERN = re.compile(
    r"(https?://|www\.)[a-zA-Z0-9\-.]+"
    r"\.[a-zA-Z]{2,}(?:/[^\s]*)?|@[\w]{4,}",
    re.IGNORECASE,
)


@Client.on_message(filters.group & filters.command("bio"))
async def cmd_bio(client: Client, message: Message):
    chat_id = message.chat.id
    if not await is_admin(client, chat_id, message.from_user.id):
        return await message.reply_text("❌ ᴏɴʟʏ ᴀᴅᴍɪɴs!")
    if len(message.command) > 1 and message.command[1].lower() in ("status", "state"):
        s = await get_bio_state(chat_id)
        return await message.reply_text(f"<b>🧬 ʙɪᴏ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ:</b> {'🟢 ON' if s else '🔴 OFF'}")
    state = await get_bio_state(chat_id)
    _, limit, penalty = await get_config(chat_id)
    text = (
        f"<b>🧬 ʙɪᴏ ʟɪɴᴋ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ:</b> {'🟢 ON' if state else '🔴 OFF'}\n"
        f"<b>⚠️ ᴡᴀʀɴ ʟɪᴍɪᴛ:</b> {limit}  |  <b>⚖️ ᴘᴇɴᴀʟᴛʏ:</b> {penalty.upper()}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔴 ᴛᴜʀɴ OFF" if state else "🟢 ᴛᴜʀɴ ON",
            callback_data=f"togglebio_{'off' if state else 'on'}",
        )],
        [
            InlineKeyboardButton("⚙️ ᴄᴏɴꜰɪɢ", callback_data="open_config"),
            InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",  callback_data="close"),
        ],
    ])
    await message.reply_text(text, reply_markup=kb)


@Client.on_callback_query(filters.regex(r"^togglebio_(on|off)$"))
async def cb_togglebio(client: Client, cq: CallbackQuery):
    if not await is_admin(client, cq.message.chat.id, cq.from_user.id):
        return await cq.answer("❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!", show_alert=True)
    action  = cq.data.split("_")[1]
    chat_id = cq.message.chat.id
    await set_bio_state(chat_id, action == "on")
    state = await get_bio_state(chat_id)
    _, limit, penalty = await get_config(chat_id)
    text = (
        f"<b>🧬 ʙɪᴏ ɪs ɴᴏᴡ:</b> {'🟢 ON' if state else '🔴 OFF'}\n"
        f"<b>⚠️ ᴡᴀʀɴ ʟɪᴍɪᴛ:</b> {limit}  |  <b>⚖️ ᴘᴇɴᴀʟᴛʏ:</b> {penalty.upper()}"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "🔴 ᴛᴜʀɴ OFF" if state else "🟢 ᴛᴜʀɴ ON",
            callback_data=f"togglebio_{'off' if state else 'on'}",
        )],
        [
            InlineKeyboardButton("⚙️ ᴄᴏɴꜰɪɢ", callback_data="open_config"),
            InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",  callback_data="close"),
        ],
    ])
    await safe_edit(cq.message, text, kb)
    await cq.answer("✅ ᴛᴏɢɢʟᴇᴅ!")


def _config_text(limit, penalty):
    return (
        "<b>⚙️ ʙɪᴏ ᴘʀᴏᴛᴇᴄᴛᴏʀ ᴄᴏɴꜰɪɢ</b>\n\n"
        f"📊 ᴡᴀʀɴ ʟɪᴍɪᴛ: <b>{limit}</b>\n"
        f"⚖️ ᴘᴇɴᴀʟᴛʏ: <b>{penalty.upper()}</b>"
    )

def _config_kb(penalty):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚠️ ᴡᴀʀɴ ʟɪᴍɪᴛ", callback_data="warn_menu")],
        [
            InlineKeyboardButton("🔇 ᴍᴜᴛᴇ" + (" ✅" if penalty == "mute" else ""), callback_data="set_mute"),
            InlineKeyboardButton("🔨 ʙᴀɴ"  + (" ✅" if penalty == "ban"  else ""), callback_data="set_ban"),
        ],
        [InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")],
    ])


@Client.on_message(filters.group & filters.command("config"))
async def cmd_config(client: Client, message: Message):
    if not await is_admin(client, message.chat.id, message.from_user.id): return
    _, limit, penalty = await get_config(message.chat.id)
    try:
        await client.send_photo(message.chat.id, START_IMG, caption=_config_text(limit, penalty), reply_markup=_config_kb(penalty))
    except Exception:
        await message.reply_text(_config_text(limit, penalty), reply_markup=_config_kb(penalty))
    try: await message.delete()
    except Exception: pass


@Client.on_callback_query(filters.regex(r"^open_config$"))
async def cb_open_config(client: Client, cq: CallbackQuery):
    if not await is_admin(client, cq.message.chat.id, cq.from_user.id):
        return await cq.answer("❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!", show_alert=True)
    _, limit, penalty = await get_config(cq.message.chat.id)
    await safe_edit(cq.message, _config_text(limit, penalty), _config_kb(penalty))
    await cq.answer()


@Client.on_callback_query(filters.regex(r"^set_(mute|ban)$"))
async def cb_set_penalty(client: Client, cq: CallbackQuery):
    if not await is_admin(client, cq.message.chat.id, cq.from_user.id):
        return await cq.answer("❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!", show_alert=True)
    await update_config(cq.message.chat.id, penalty=cq.data.split("_")[1])
    _, limit, penalty = await get_config(cq.message.chat.id)
    await safe_edit(cq.message, _config_text(limit, penalty), _config_kb(penalty))
    await cq.answer(f"✅ ᴘᴇɴᴀʟᴛʏ → {penalty.upper()}")


def _warn_kb(selected):
    def btn(n):
        return InlineKeyboardButton(f"{n} ✅" if n == selected else str(n), callback_data=f"setwarn_{n}")
    return InlineKeyboardMarkup([
        [btn(3), btn(4), btn(5)],
        [InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="config_back"),
         InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")],
    ])


@Client.on_callback_query(filters.regex(r"^warn_menu$"))
async def cb_warn_menu(client: Client, cq: CallbackQuery):
    if not await is_admin(client, cq.message.chat.id, cq.from_user.id):
        return await cq.answer("❌", show_alert=True)
    _, limit, _ = await get_config(cq.message.chat.id)
    await safe_edit(cq.message, "<b>sᴇʟᴇᴄᴛ ᴡᴀʀɴ ʟɪᴍɪᴛ:</b>", _warn_kb(limit))
    await cq.answer()


@Client.on_callback_query(filters.regex(r"^setwarn_(3|4|5)$"))
async def cb_setwarn(client: Client, cq: CallbackQuery):
    if not await is_admin(client, cq.message.chat.id, cq.from_user.id):
        return await cq.answer("❌", show_alert=True)
    count = int(cq.data.split("_")[1])
    await update_config(cq.message.chat.id, limit=count)
    await safe_edit(cq.message, f"<b>✅ ᴡᴀʀɴ ʟɪᴍɪᴛ → <code>{count}</code></b>", _warn_kb(count))
    await cq.answer(f"✅ {count}")


@Client.on_callback_query(filters.regex(r"^config_back$"))
async def cb_config_back(client: Client, cq: CallbackQuery):
    if not await is_admin(client, cq.message.chat.id, cq.from_user.id):
        return await cq.answer("❌", show_alert=True)
    _, limit, penalty = await get_config(cq.message.chat.id)
    await safe_edit(cq.message, _config_text(limit, penalty), _config_kb(penalty))
    await cq.answer()


# ── Warn / whitelist callbacks ────────────────────────────────────────────────

@Client.on_callback_query(filters.regex(r"^cancel_warn_(\d+)$"))
async def cb_cancel_warn(client: Client, cq: CallbackQuery):
    if not await is_admin(client, cq.message.chat.id, cq.from_user.id):
        return await cq.answer("❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!", show_alert=True)
    target_id = int(cq.data.split("_")[-1])
    chat_id   = cq.message.chat.id
    await reset_warnings(chat_id, target_id)
    try:
        u = await client.get_users(target_id)
        name = fullname(u)
    except Exception:
        name = str(target_id)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ", callback_data=f"whitelist_{target_id}"),
        InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",     callback_data="close"),
    ]])
    await safe_edit(cq.message, f"<b>✅ {mlink(name, target_id)} — ᴡᴀʀɴs ʀᴇsᴇᴛ!</b>", kb)
    await cq.answer("✅ Warns reset!")


@Client.on_callback_query(filters.regex(r"^(whitelist|unwhitelist)_(\d+)$"))
async def cb_toggle_whitelist(client: Client, cq: CallbackQuery):
    if not await is_admin(client, cq.message.chat.id, cq.from_user.id):
        return await cq.answer("❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!", show_alert=True)
    action, uid_s = cq.data.split("_", 1)
    target_id = int(uid_s)
    chat_id   = cq.message.chat.id
    try:
        u = await client.get_users(target_id)
        name = fullname(u)
    except Exception:
        name = str(target_id)
    if action == "whitelist":
        await add_whitelist(chat_id, target_id)
        await reset_warnings(chat_id, target_id)
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚫 ʀᴇᴍᴏᴠᴇ", callback_data=f"unwhitelist_{target_id}"),
            InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",  callback_data="close"),
        ]])
        await safe_edit(cq.message, f"<b>✅ {mlink(name, target_id)} ᴡʜɪᴛᴇʟɪsᴛᴇᴅ!</b>", kb)
    else:
        await remove_whitelist(chat_id, target_id)
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ", callback_data=f"whitelist_{target_id}"),
            InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",     callback_data="close"),
        ]])
        await safe_edit(cq.message, f"<b>🚫 {mlink(name, target_id)} ʀᴇᴍᴏᴠᴇᴅ.</b>", kb)
    await cq.answer()


@Client.on_callback_query(filters.regex(r"^(unmute|unban)_(\d+)$"))
async def cb_unpunish(client: Client, cq: CallbackQuery):
    if not await is_admin(client, cq.message.chat.id, cq.from_user.id):
        return await cq.answer("❌ ᴀᴅᴍɪɴs ᴏɴʟʏ!", show_alert=True)
    action, uid_s = cq.data.split("_", 1)
    target_id = int(uid_s)
    chat_id   = cq.message.chat.id
    try:
        u = await client.get_users(target_id)
        name = fullname(u)
    except Exception:
        name = str(target_id)
    try:
        if action == "unmute":
            await client.restrict_chat_member(chat_id, target_id, ChatPermissions(
                can_send_messages=True, can_send_media_messages=True,
                can_send_other_messages=True, can_add_web_page_previews=True,
            ))
            label = "ᴜɴᴍᴜᴛᴇᴅ 🔊"
            ak = "UNMUTE"
        else:
            await client.unban_chat_member(chat_id, target_id)
            label = "ᴜɴʙᴀɴɴᴇᴅ ✅"
            ak = "UNBAN"
        await reset_warnings(chat_id, target_id)
        await log_action(client, ak, chat_id, cq.message.chat.title or "",
                         cq.from_user.id, fullname(cq.from_user), target_id, name)
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ", callback_data=f"whitelist_{target_id}"),
            InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ",     callback_data="close"),
        ]])
        await safe_edit(cq.message, f"<b>{mlink(name, target_id)} ʜᴀs ʙᴇᴇɴ {label}!</b>", kb)
    except errors.ChatAdminRequired:
        await safe_edit(cq.message, "<b>❌ ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ!</b>")
    await cq.answer()


# ── BIO WATCHER ───────────────────────────────────────────────────────────────

@Client.on_message(filters.group & ~filters.service)
async def bio_watcher(client: Client, message: Message):
    if not message or not message.from_user: return
    if message.from_user.is_bot: return
    chat_id = message.chat.id
    user_id = message.from_user.id
    if user_id == BOT_OWNER_ID: return
    if not await get_bio_state(chat_id): return
    try:
        if await is_admin(client, chat_id, user_id): return
        if await is_whitelisted(chat_id, user_id):   return
    except Exception: return

    try:
        user = await client.get_chat(user_id)
    except Exception: return

    bio  = user.bio or ""
    name = fullname(user)
    umen = mlink(name, user_id)

    if not URL_PATTERN.search(bio):
        await reset_warnings(chat_id, user_id)
        return

    try: await message.delete()
    except errors.MessageDeleteForbidden:
        await message.reply_text("⚠️ ɢɪᴠᴇ ᴍᴇ ᴅᴇʟᴇᴛᴇ ᴘᴇʀᴍɪssɪᴏɴ!")
        return
    except Exception: pass

    mode, limit, penalty = await get_config(chat_id)
    chat_title = message.chat.title or str(chat_id)
    me = await client.get_me()
    count = await increment_warning(chat_id, user_id)

    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❌ ᴄᴀɴᴄᴇʟ ᴡᴀʀɴ", callback_data=f"cancel_warn_{user_id}"),
            InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ",   callback_data=f"whitelist_{user_id}"),
        ],
        [InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")],
    ])
    sent = await message.reply_text(
        f"<b>🚨 ᴡᴀʀɴɪɴɢ!</b>\n\n"
        f"👤 {umen}\n❌ ʟɪɴᴋ/@ᴜsᴇʀɴᴀᴍᴇ ɪɴ ʙɪᴏ\n⚠️ <b>{count}/{limit}</b>",
        reply_markup=kb,
    )
    await log_action(client, "WARN", chat_id, chat_title, me.id, "BioBot", user_id, name,
                     reason=f"Link in bio | warn {count}/{limit}")

    if count >= limit:
        try:
            if penalty == "mute":
                await client.restrict_chat_member(chat_id, user_id, ChatPermissions())
                ub = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔊 ᴜɴᴍᴜᴛᴇ",    callback_data=f"unmute_{user_id}"),
                    InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ", callback_data=f"whitelist_{user_id}"),
                ]])
                await sent.edit_text(f"<b>🔇 {umen} ᴍᴜᴛᴇᴅ!</b>\n⚠️ {count}/{limit} ᴡᴀʀɴs", reply_markup=ub)
                await log_action(client, "MUTE", chat_id, chat_title, me.id, "BioBot", user_id, name,
                                 reason=f"Reached {count}/{limit} warns")
            else:
                await client.ban_chat_member(chat_id, user_id)
                ub = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ ᴜɴʙᴀɴ", callback_data=f"unban_{user_id}"),
                ]])
                await sent.edit_text(f"<b>🔨 {umen} ʙᴀɴɴᴇᴅ!</b>\n⚠️ {count}/{limit} ᴡᴀʀɴs", reply_markup=ub)
                await log_action(client, "BAN", chat_id, chat_title, me.id, "BioBot", user_id, name,
                                 reason=f"Reached {count}/{limit} warns")
        except errors.ChatAdminRequired:
            await sent.edit_text("<b>❌ ɪ ʟᴀᴄᴋ ᴘᴇʀᴍɪssɪᴏɴ!</b>")
        except Exception: pass
