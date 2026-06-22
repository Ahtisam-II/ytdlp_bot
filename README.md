# 📱 Termux yt-dlp Bot (Pyrogram Edition) 🚀

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Pyrogram](https://img.shields.io/badge/Pyrogram-v2.0-orange.svg)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-red.svg)
![Termux](https://img.shields.io/badge/Platform-Termux%20%7C%20Android-green.svg)

A powerful, queue-based, **2GB-bypassing** Telegram bot built specifically to run natively on Android using Termux. 

---

## ✨ Features

- 🚀 **Massive 2GB Uploads**: Fully bypasses the standard 50MB Bot API limit by utilizing Pyrogram's MTProto chunked uploads for large files.
- ⚡ **Hybrid Speeds**: Automatically detects file size. If `< 50MB`, it uses Telegram's hyper-fast HTTP API. If `> 50MB`, it safely switches to the native MTProto connection.
- 🚦 **Smart Queueing**: Videos are processed one at a time via a strict background queue system. Prevents your phone's memory or storage from crashing under heavy loads.
- 🏷️ **Original Titles**: Automatically renames output files to perfectly match the original video's title (`%(title)s.%(ext)s`).
- 🎬 **Forced MKV Remuxing**: Safely merges video/audio tracks and remuxes them into `.mkv` without re-encoding to ensure flawless playback in Telegram.
- 🛡️ **Termux-Native VPN Support**: Because it's designed for Termux, it seamlessly routes through your phone's background VPN (like Cloudflare WARP or 1.1.1.1) automatically! No complex proxy config needed.
- 🔒 **Access Control**: Built-in whitelist and blacklist features to restrict who can use your private bot instance.
- 🧹 **Auto-Cleanup**: Intelligently cleans up download directories to prevent your phone's storage from filling up.

---

## 📲 Installation on Phone (Termux)

### 1. Install Termux
> ⚠️ **IMPORTANT**: Do NOT install Termux from the Google Play Store! It is abandoned and broken. Install it from [F-Droid](https://f-droid.org/en/packages/com.termux/).

### 2. Setup Termux Storage & Requirements
Open Termux and run these commands to prepare your environment:
```bash
# Give Termux access to your phone's files
termux-setup-storage

# Update system packages
pkg update && pkg upgrade -y

# Install Python and ffmpeg (required for video merging)
pkg install python ffmpeg -y
```

### 3. Transfer Code
Copy this entire `termus_ytdlp` folder to your phone's internal storage, then navigate to it in Termux. For example, if you saved it in your Downloads folder:
```bash
cd ~/storage/downloads/termus_ytdlp
```

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration

Create a `.env` file in the root folder with the following variables:

```env
BOT_TOKEN=your_botfather_token
API_ID=6
API_HASH=eb06d4abfb49dc3eeb1aeb98ae0f581e
MAX_FILE_SIZE_MB=2000
MAX_VIDEO_DURATION=3600
KEEP_DOWNLOADS=False
ADMIN_USER_ID= your telegram_id
```

### Configuration Details:
- **`API_ID` & `API_HASH`**: The defaults above (`6`) are the public Android API keys to bypass the `my.telegram.org` VPN block. If you have your own developer keys, put them here!
- **`KEEP_DOWNLOADS`**: Set this to `True` if you want the bot to *never* delete the downloaded videos from your phone's storage after sending them to Telegram.

---

## 🚀 Running the Bot

Turn on your phone's VPN (if required in your region to access Telegram), then run:

```bash
python main.py
```

The bot will stay alive as long as Termux is running in the background.

---

## ⌨️ Commands

| Command | Description | Access |
|---------|-------------|---------|
| `/start` | Start the bot and see the welcome message | All |
| `/help` | View usage instructions | All |
| `/showqueue` | Check your position in the processing queue | All |
| `/cancel` | Cancel a pending queued download | All |
| `/ping` | Check if the bot is alive | All |
| `/stats` | Check bot load, memory, and disk space | Admin |
| `/cleanup` | Force clean the downloads folder | Admin |
