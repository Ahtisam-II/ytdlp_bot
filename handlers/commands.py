import os
import shutil
import psutil
from pyrogram import Client, filters
from pyrogram.types import Message
import config
from logger import get_logger
from services.queue_manager import queue_manager

logger = get_logger(__name__)

@Client.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handler for /start"""
    user_id = message.from_user.id
    if not config.is_user_allowed(user_id):
        await message.reply_text("You are not authorized to use this bot.")
        return
        
    welcome_msg = (
        "Welcome to the Termux yt-dlp Bot!\n\n"
        "Send me a video link, and I will extract the available formats for you to download.\n"
        "Downloads are queued one at a time to prevent server crashes.\n\n"
        "Use /help to see more commands."
    )
    await message.reply_text(welcome_msg)

@Client.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Handler for /help"""
    user_id = message.from_user.id
    if not config.is_user_allowed(user_id):
        return
        
    help_msg = (
        "Simply send a valid video URL (YouTube, Twitter, TikTok, etc.) to start.\n\n"
        "Commands:\n"
        "/start - Welcome message\n"
        "/help - This help message\n"
        "/showqueue - Check your position in the queue\n"
        "/cancel - Cancel your pending queued download\n"
        "/ping - Check if bot is alive\n"
    )
    if user_id == config.ADMIN_USER_ID:
        help_msg += (
            "\nAdmin Commands:\n"
            "/stats - Show bot statistics\n"
            "/cleanup - Manually clean the download folder"
        )
    await message.reply_text(help_msg)

@Client.on_message(filters.command("stats"))
async def stats_command(client: Client, message: Message):
    """Handler for /stats (Admin only)"""
    user_id = message.from_user.id
    if user_id != config.ADMIN_USER_ID:
        await message.reply_text("Admin only command.")
        return
        
    stats = queue_manager.get_queue_stats()
    
    # Get disk usage
    total, used, free = shutil.disk_usage(config.DOWNLOAD_DIR)
    free_mb = free // (2**20)
    
    # Get RAM usage
    ram = psutil.virtual_memory()
    ram_used_mb = ram.used // (2**20)
    ram_total_mb = ram.total // (2**20)
    
    msg = (
        f"📊 **Bot Statistics**\n\n"
        f"**Queue:**\n"
        f"- Active task user ID: `{stats['active']}`\n"
        f"- Pending tasks: `{stats['pending_count']}`\n\n"
        f"**System:**\n"
        f"- Free Disk Space: `{free_mb} MB`\n"
        f"- RAM Usage: `{ram_used_mb} MB / {ram_total_mb} MB`\n"
    )
    await message.reply_text(msg)

@Client.on_message(filters.command("showqueue"))
async def showqueue_command(client: Client, message: Message):
    """Handler for /showqueue"""
    user_id = message.from_user.id
    if not config.is_user_allowed(user_id):
        return
        
    pos = queue_manager.get_position(user_id)
    if pos == -1:
        await message.reply_text("You have no active or queued downloads.")
    elif pos == 0:
        await message.reply_text("Your download is currently being processed! ⏳")
    else:
        await message.reply_text(f"You are position {pos} in the queue. 📝")

@Client.on_message(filters.command("cancel"))
async def cancel_command(client: Client, message: Message):
    """Handler for /cancel"""
    user_id = message.from_user.id
    if not config.is_user_allowed(user_id):
        return
        
    pos = queue_manager.get_position(user_id)
    if pos == 0:
        await message.reply_text("Your download is currently processing and cannot be cancelled easily. It will finish shortly.")
    elif pos > 0:
        success = queue_manager.cancel_job(user_id)
        if success:
            await message.reply_text("Your queued download has been cancelled. ✅")
        else:
            await message.reply_text("Failed to cancel queued download.")
    else:
        await message.reply_text("You have no active or queued downloads to cancel.")

@Client.on_message(filters.command("cleanup"))
async def cleanup_command(client: Client, message: Message):
    """Handler for /cleanup (Admin only)"""
    user_id = message.from_user.id
    if user_id != config.ADMIN_USER_ID:
        await message.reply_text("Admin only command.")
        return
        
    logger.info(f"Manual cleanup triggered by admin {user_id}")
    count = 0
    if os.path.exists(config.DOWNLOAD_DIR):
        for filename in os.listdir(config.DOWNLOAD_DIR):
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    count += 1
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    count += 1
            except Exception as e:
                logger.error(f"Failed to delete {file_path}. Reason: {e}")
                
    await message.reply_text(f"Cleanup complete. Removed {count} items. 🧹")

@Client.on_message(filters.command("ping"))
async def ping_command(client: Client, message: Message):
    """Handler for /ping"""
    await message.reply_text("Pong! 🏓 I am alive and running.")
