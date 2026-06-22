import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# --- Configuration Variables ---

# Bot Token from @BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Pyrogram API ID and Hash (for MTProto)
API_ID = os.getenv("API_ID", "")
API_HASH = os.getenv("API_HASH", "")

# Directory to store temporary downloads
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "./downloads")

# Whether to keep downloaded files after uploading to Telegram
KEEP_DOWNLOADS = os.getenv("KEEP_DOWNLOADS", "False").lower() in ("true", "1", "yes")

# Proxy URL (Optional, e.g. http://127.0.0.1:10809 or socks5://127.0.0.1:10808)
PROXY_URL = os.getenv("PROXY_URL", "")
if PROXY_URL:
    os.environ["HTTP_PROXY"] = PROXY_URL
    os.environ["HTTPS_PROXY"] = PROXY_URL
    os.environ["http_proxy"] = PROXY_URL
    os.environ["https_proxy"] = PROXY_URL
else:
    # Explicitly clear any leftover dead proxies from your Windows environment
    os.environ.pop("HTTP_PROXY", None)
    os.environ.pop("HTTPS_PROXY", None)
    os.environ.pop("http_proxy", None)
    os.environ.pop("https_proxy", None)

# Maximum allowed file size for downloads in Megabytes (2GB limit)
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "2000"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Maximum allowed video duration in seconds (default 3600 = 1 hour)
MAX_VIDEO_DURATION = int(os.getenv("MAX_VIDEO_DURATION", "3600"))

# Telegram User ID for the admin (can use special commands)
try:
    ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))
except ValueError:
    ADMIN_USER_ID = 0

# Whitelist and Blacklist parsing
_whitelist_raw = os.getenv("WHITELIST_USERS", "")
WHITELIST_USERS = [int(x.strip()) for x in _whitelist_raw.split(",") if x.strip().isdigit()]

_blacklist_raw = os.getenv("BLACKLIST_USERS", "")
BLACKLIST_USERS = [int(x.strip()) for x in _blacklist_raw.split(",") if x.strip().isdigit()]

def is_user_allowed(user_id: int) -> bool:
    """Check if a user is allowed to use the bot based on whitelist/blacklist."""
    if BLACKLIST_USERS and user_id in BLACKLIST_USERS:
        return False
    if WHITELIST_USERS and user_id not in WHITELIST_USERS:
        return False
    return True
