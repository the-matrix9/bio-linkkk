from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import BOT_OWNER_USERNAME, SUPPORT_GROUP, START_IMG
from database import save_user
from helpers import safe_edit, send_with_photo

START_TEXT = (
    "<b>🛡️ ʙɪᴏ ʟɪɴᴋ ᴘʀᴏᴛᴇᴄᴛᴏʀ ʙᴏᴛ</b>\n\n"
    "ɪ ɢᴜᴀʀᴅ ʏᴏᴜʀ ɢʀᴏᴜᴘs ᴀɢᴀɪɴsᴛ ᴜsᴇʀs\n"
    "ᴡɪᴛʜ <b>ʟɪɴᴋs / @ᴜsᴇʀɴᴀᴍᴇs</b> ɪɴ ᴛʜᴇɪʀ ʙɪᴏ.\n\n"
    "<b>🔹 ꜰᴇᴀᴛᴜʀᴇs:</b>\n"
    "  • ᴀᴜᴛᴏ ᴜʀʟ ᴅᴇᴛᴇᴄᴛɪᴏɴ ɪɴ ʙɪᴏ\n"
    "  • ᴡᴀʀɴ / ᴍᴜᴛᴇ / ʙᴀɴ sʏsᴛᴇᴍ\n"
    "  • ᴡʜɪᴛᴇʟɪsᴛ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ\n"
    "  • ᴘɪɴ + ᴀᴜᴛᴏ-ᴘɪɴ ᴏɴ ᴊᴏɪɴ\n"
    "  • ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏ ᴜsᴇʀs & ɢʀᴏᴜᴘs\n"
    "  • ᴀᴄᴛɪᴏɴ ʟᴏɢs\n"
    "  • /aban — ɢʟᴏʙᴀʟ ʙᴀɴ ᴀᴄʀᴏss ᴀʟʟ ɢʀᴏᴜᴘs\n\n"
    "ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ & ᴜsᴇ <code>/bio</code> ᴛᴏ sᴛᴀʀᴛ."
)

HELP_TEXT = (
    "<b>🛠️ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs</b>\n\n"
    "<b>── ɢʀᴏᴜᴘ (ᴀᴅᴍɪɴ) ──</b>\n"
    "  /bio — ᴛᴏɢɢʟᴇ ʙɪᴏ ᴘʀᴏᴛᴇᴄᴛɪᴏɴ\n"
    "  /bio status — ᴄᴜʀʀᴇɴᴛ sᴛᴀᴛᴇ\n"
    "  /config — ᴡᴀʀɴ ʟɪᴍɪᴛ + ᴘᴇɴᴀʟᴛʏ\n"
    "  /free — ᴡʜɪᴛᴇʟɪsᴛ ᴜsᴇʀ\n"
    "  /unfree — ʀᴇᴍᴏᴠᴇ ꜰʀᴏᴍ ᴡʜɪᴛᴇʟɪsᴛ\n"
    "  /freelist — ᴠɪᴇᴡ ᴡʜɪᴛᴇʟɪsᴛ\n"
    "  /warns — ᴄʜᴇᴄᴋ ᴡᴀʀɴs\n"
    "  /pin — ᴘɪɴ (ʀᴇᴘʟʏ ᴏʀ /pin -ɪᴅ)\n"
    "  /unpin — ᴜɴᴘɪɴ ᴀʟʟ\n"
    "  /logs — ʀᴇᴄᴇɴᴛ ʟᴏɢs ꜰᴏʀ ᴛʜɪs ɢʀᴏᴜᴘ\n\n"
    "<b>── ᴏᴡɴᴇʀ ᴏɴʟʏ ──</b>\n"
    "  /broadcast — ꜰᴡᴅ ᴛᴏ ᴜsᴇʀs/ɢʀᴏᴜᴘs\n"
    "  /stats — ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs\n"
    "  /aban — ɢʟᴏʙᴀʟ ʙᴀɴ ꜰʀᴏᴍ ᴀʟʟ ɢᴄs\n"
    "  /aungban — ɢʟᴏʙᴀʟ ᴜɴʙᴀɴ\n"
    "  /alogs — ᴀʟʟ ʀᴇᴄᴇɴᴛ ʟᴏɢs\n"
    "  /cmds — ɪɴʟɪɴᴇ ᴄᴏᴍᴍᴀɴᴅ ᴘᴀɴᴇʟ\n\n"
    "<b>ɴᴏᴛᴇ:</b> ʙᴏᴛ ɴᴇᴇᴅs ᴅᴇʟᴇᴛᴇ + ʙᴀɴ ᴘᴇʀᴍs."
)

CMD_TEXTS = {
    "cmd_bio_info": (
        "<b>🧬 /bio</b>\n\n"
        "<code>/bio</code> — ᴛᴏɢɢʟᴇ ᴏɴ/ᴏꜰꜰ (ᴅᴇꜰᴀᴜʟᴛ: ᴏꜰꜰ)\n"
        "<code>/bio status</code> — ᴄʜᴇᴄᴋ sᴛᴀᴛᴇ"
    ),
    "cmd_config_info": (
        "<b>⚙️ /config</b>\n\n"
        "sᴇᴛ ᴡᴀʀɴ ʟɪᴍɪᴛ: <b>3 / 4 / 5</b>\n"
        "sᴇᴛ ᴘᴇɴᴀʟᴛʏ: <b>ᴍᴜᴛᴇ</b> ᴏʀ <b>ʙᴀɴ</b>"
    ),
    "cmd_whitelist_info": (
        "<b>✅ ᴡʜɪᴛᴇʟɪsᴛ</b>\n\n"
        "<code>/free</code> — ᴡʜɪᴛᴇʟɪsᴛ\n"
        "<code>/unfree</code> — ʀᴇᴍᴏᴠᴇ\n"
        "<code>/freelist</code> — ᴠɪᴇᴡ ᴀʟʟ"
    ),
    "cmd_warns_info": (
        "<b>⚠️ /warns</b>\n\n"
        "ʀᴇᴘʟʏ ᴛᴏ ᴜsᴇʀ ᴏʀ /warns @user\n"
        "ɪɴʟɪɴᴇ ʙᴜᴛᴛᴏɴ ᴛᴏ ʀᴇsᴇᴛ ᴡᴀʀɴs."
    ),
    "cmd_pin_info": (
        "<b>📌 ᴘɪɴ</b>\n\n"
        "<code>/pin</code> — ʀᴇᴘʟʏ ᴛᴏ ᴘɪɴ\n"
        "<code>/pin -id</code> — ᴘɪɴ ʙʏ ɪᴅ\n"
        "<code>/unpin</code> — ᴜɴᴘɪɴ ᴀʟʟ"
    ),
    "cmd_bcast_info": (
        "<b>📡 /broadcast</b>\n\n"
        "ʀᴇᴘʟʏ ᴛᴏ ᴍsɢ + /broadcast\n"
        "<code>-users</code> / <code>-groups</code> / ʙᴏᴛʜ\n"
        "ᴏᴡɴᴇʀ ᴘᴍ ᴏɴʟʏ."
    ),
    "cmd_gban_info": (
        "<b>🌐🔨 /aban</b>\n\n"
        "<code>/aban @user [reason]</code>\n"
        "ʙᴀɴs ꜰʀᴏᴍ ᴀʟʟ ɢʀᴏᴜᴘs\n\n"
        "<code>/aungban @user</code> — ᴜɴᴅᴏ"
    ),
    "cmd_logs_info": (
        "<b>📋 ʟᴏɢs</b>\n\n"
        "<code>/logs</code> — ᴛʜɪs ɢᴄ (ᴀᴅᴍɪɴ)\n"
        "<code>/alogs</code> — ɢʟᴏʙᴀʟ (ᴏᴡɴᴇʀ)"
    ),
}


@Client.on_message(filters.command("start"))
async def cmd_start(client: Client, message: Message):
    if message.from_user:
        await save_user(message.from_user.id)
    bot  = await client.get_me()
    link = f"https://t.me/{bot.username}?startgroup=true"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ᴀᴅᴅ ᴛᴏ ɢʀᴏᴜᴘ", url=link)],
        [
            InlineKeyboardButton("🛠️ sᴜᴘᴘᴏʀᴛ", url=SUPPORT_GROUP),
            InlineKeyboardButton("👤 ᴏᴡɴᴇʀ",    url=f"https://t.me/{BOT_OWNER_USERNAME}"),
        ],
        [
            InlineKeyboardButton("📖 ʜᴇʟᴘ", callback_data="help_menu"),
            InlineKeyboardButton("📋 ᴄᴍᴅs", callback_data="cmds_main"),
        ],
    ])
    await send_with_photo(client, message.chat.id, START_TEXT, kb)


@Client.on_message(filters.command(["help", "bhelp"]))
async def cmd_help(client: Client, message: Message):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back_start"),
        InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close"),
    ]])
    await send_with_photo(client, message.chat.id, HELP_TEXT, kb)


@Client.on_message(filters.command("cmds"))
async def cmd_cmds(client: Client, message: Message):
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧬 ʙɪᴏ",       callback_data="cmd_bio_info"),
            InlineKeyboardButton("⚙️ ᴄᴏɴꜰɪɢ",    callback_data="cmd_config_info"),
        ],
        [
            InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ", callback_data="cmd_whitelist_info"),
            InlineKeyboardButton("⚠️ ᴡᴀʀɴs",     callback_data="cmd_warns_info"),
        ],
        [
            InlineKeyboardButton("📌 ᴘɪɴ",    callback_data="cmd_pin_info"),
            InlineKeyboardButton("📡 ʙᴄᴀsᴛ",  callback_data="cmd_bcast_info"),
        ],
        [
            InlineKeyboardButton("🌐🔨 ɢʙᴀɴ", callback_data="cmd_gban_info"),
            InlineKeyboardButton("📋 ʟᴏɢs",   callback_data="cmd_logs_info"),
        ],
        [InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")],
    ])
    await send_with_photo(client, message.chat.id, "<b>📋 ɪɴʟɪɴᴇ ᴄᴏᴍᴍᴀɴᴅ ᴘᴀɴᴇʟ</b>\n\nᴄʜᴏᴏsᴇ:", kb)


@Client.on_callback_query(filters.regex(r"^close$"))
async def cb_close(client: Client, cq: CallbackQuery):
    try: await cq.message.delete()
    except Exception: pass
    await cq.answer()


@Client.on_callback_query(filters.regex(r"^help_menu$"))
async def cb_help_menu(client: Client, cq: CallbackQuery):
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="back_start"),
        InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close"),
    ]])
    await safe_edit(cq.message, HELP_TEXT, kb)
    await cq.answer()


@Client.on_callback_query(filters.regex(r"^back_start$"))
async def cb_back_start(client: Client, cq: CallbackQuery):
    bot  = await client.get_me()
    link = f"https://t.me/{bot.username}?startgroup=true"
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ ᴀᴅᴅ ᴛᴏ ɢʀᴏᴜᴘ", url=link)],
        [
            InlineKeyboardButton("🛠️ sᴜᴘᴘᴏʀᴛ", url=SUPPORT_GROUP),
            InlineKeyboardButton("👤 ᴏᴡɴᴇʀ",    url=f"https://t.me/{BOT_OWNER_USERNAME}"),
        ],
        [
            InlineKeyboardButton("📖 ʜᴇʟᴘ", callback_data="help_menu"),
            InlineKeyboardButton("📋 ᴄᴍᴅs", callback_data="cmds_main"),
        ],
    ])
    await safe_edit(cq.message, START_TEXT, kb)
    await cq.answer()


@Client.on_callback_query(filters.regex(r"^cmds_main$"))
async def cb_cmds_main(client: Client, cq: CallbackQuery):
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧬 ʙɪᴏ",       callback_data="cmd_bio_info"),
            InlineKeyboardButton("⚙️ ᴄᴏɴꜰɪɢ",    callback_data="cmd_config_info"),
        ],
        [
            InlineKeyboardButton("✅ ᴡʜɪᴛᴇʟɪsᴛ", callback_data="cmd_whitelist_info"),
            InlineKeyboardButton("⚠️ ᴡᴀʀɴs",     callback_data="cmd_warns_info"),
        ],
        [
            InlineKeyboardButton("📌 ᴘɪɴ",    callback_data="cmd_pin_info"),
            InlineKeyboardButton("📡 ʙᴄᴀsᴛ",  callback_data="cmd_bcast_info"),
        ],
        [
            InlineKeyboardButton("🌐🔨 ɢʙᴀɴ", callback_data="cmd_gban_info"),
            InlineKeyboardButton("📋 ʟᴏɢs",   callback_data="cmd_logs_info"),
        ],
        [InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close")],
    ])
    await safe_edit(cq.message, "<b>📋 ɪɴʟɪɴᴇ ᴄᴏᴍᴍᴀɴᴅ ᴘᴀɴᴇʟ</b>\n\nᴄʜᴏᴏsᴇ:", kb)
    await cq.answer()


@Client.on_callback_query(filters.regex(r"^cmd_(bio|config|whitelist|warns|pin|bcast|gban|logs)_info$"))
async def cb_cmd_info(client: Client, cq: CallbackQuery):
    text = CMD_TEXTS.get(cq.data, "ɴᴏ ɪɴꜰᴏ.")
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 ʙᴀᴄᴋ", callback_data="cmds_main"),
        InlineKeyboardButton("🗑️ ᴄʟᴏsᴇ", callback_data="close"),
    ]])
    await safe_edit(cq.message, text, kb)
    await cq.answer()
