import os
import shutil
import asyncio
from pyrogram import Client, idle
import config
from logger import get_logger
from services.queue_manager import queue_manager

logger = get_logger(__name__)

def perform_startup_cleanup():
    """Removes all files in the download directory to prevent storage leaks from previous crashes."""
    if config.KEEP_DOWNLOADS:
        logger.info("KEEP_DOWNLOADS is True. Skipping startup cleanup.")
        return
        
    logger.info("Performing startup cleanup...")
    if not os.path.exists(config.DOWNLOAD_DIR):
        os.makedirs(config.DOWNLOAD_DIR)
        return

    count = 0
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
            
    logger.info(f"Startup cleanup complete. Removed {count} items.")

async def main():
    if not config.BOT_TOKEN or not config.API_ID or not config.API_HASH:
        logger.error("Missing BOT_TOKEN, API_ID, or API_HASH in environment variables! Exiting.")
        return

    perform_startup_cleanup()

    proxy_dict = None
    if config.PROXY_URL:
        logger.info(f"Using proxy: {config.PROXY_URL}")
        from urllib.parse import urlparse
        p = urlparse(config.PROXY_URL)
        proxy_dict = {
            "scheme": p.scheme,
            "hostname": p.hostname,
            "port": p.port
        }
        if p.username:
            proxy_dict["username"] = p.username
            proxy_dict["password"] = p.password

    app = Client(
        "ytdlp_bot",
        bot_token=config.BOT_TOKEN,
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        proxy=proxy_dict,
        plugins=dict(root="handlers")
    )

    logger.info("Starting background queue worker...")
    # Because queue_manager uses asyncio.create_task internally, 
    # it must be started inside the running event loop.
    queue_manager.start()

    logger.info("Bot is starting polling...")
    await app.start()
    
    await idle()
    
    await app.stop()

if __name__ == '__main__':
    asyncio.run(main())
