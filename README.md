# 🛡️ Bio Link Protector Bot

Auto-detects & punishes users with links/@usernames in their Telegram bio.

## 📁 File Structure
```
biobot/
├── main.py           ← Entry point (Flask + plugin loader)
├── config.py         ← Env var config
├── database.py       ← All MongoDB helpers
├── helpers.py        ← Shared utilities
├── plugins/
│   ├── tracker.py    ← Auto-save users/chats, join alerts
│   ├── start.py      ← /start /help /cmds
│   ├── bio.py        ← Bio watcher + /bio /config
│   ├── whitelist.py  ← /free /unfree /freelist /warns
│   ├── pin.py        ← /pin /unpin + auto-pin
│   ├── broadcast.py  ← /broadcast
│   ├── gban.py       ← /aban /aungban (global ban)
│   └── logs.py       ← /logs /alogs /stats
├── Procfile          ← Heroku
├── Dockerfile        ← Koyeb / Railway / VPS
├── runtime.txt
├── requirements.txt
└── .env.example
```

## ⚙️ Env Vars
| Variable | Required | Description |
|---|---|---|
| `API_ID` | ✅ | From my.telegram.org |
| `API_HASH` | ✅ | From my.telegram.org |
| `BOT_TOKEN` | ✅ | From @BotFather |
| `MONGO_URL` | ✅ | MongoDB connection string |
| `BOT_OWNER_ID` | ✅ | Your Telegram user ID |
| `BOT_OWNER_USERNAME` | ✅ | Your username (no @) |
| `LOG_CHANNEL` | ⬜ | Channel ID for action logs |
| `SUPPORT_GROUP` | ⬜ | Support group link |
| `PORT` | ⬜ | Health-check port (default 8080) |

## 🚀 Deploy

**Heroku:**
```
heroku create
heroku config:set API_ID=... API_HASH=... BOT_TOKEN=... MONGO_URL=... BOT_OWNER_ID=...
git push heroku main
```

**Koyeb / Railway:**
- Set env vars in dashboard
- Uses Dockerfile automatically

**VPS:**
```bash
pip install -r requirements.txt
python main.py
```

## 📋 Commands
| Command | Who | Description |
|---|---|---|
| `/bio` | Admin | Toggle bio protection (default OFF) |
| `/bio status` | Admin | Check current state |
| `/config` | Admin | Set warn limit (3/4/5) + penalty |
| `/free` | Admin | Whitelist a user |
| `/unfree` | Admin | Remove from whitelist |
| `/freelist` | Admin | View whitelist |
| `/warns` | Admin | Check user warns |
| `/pin` | Admin | Pin message (reply or /pin -id) |
| `/unpin` | Admin | Unpin all |
| `/logs` | Admin | Recent logs for this group |
| `/broadcast` | Owner | Forward msg to users/groups |
| `/stats` | Owner | Bot statistics |
| `/aban` | Owner | Global ban from all groups |
| `/aungban` | Owner | Global unban |
| `/alogs` | Owner | All recent action logs |
| `/cmds` | All | Inline command panel |
