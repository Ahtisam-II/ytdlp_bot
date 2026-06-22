import os
import time
import asyncio
from pyrogram import Client
from pyrogram.types import CallbackQuery, Message
import config
from logger import get_logger
from services.queue_manager import queue_manager
from services.downloader import DownloaderService
from handlers.messages import USER_DATA

logger = get_logger(__name__)

@Client.on_callback_query()
async def handle_callback(client: Client, query: CallbackQuery):
    """Handles button clicks from inline keyboards."""
    await query.answer()
    
    user_id = query.from_user.id
    if not config.is_user_allowed(user_id):
        return
        
    data = query.data
    if not data.startswith("dl|"):
        return
        
    parts = data.split("|")
    format_id = parts[1]
    is_audio = parts[2] == 'a' if len(parts) > 2 else False
    
    url = None
    if user_id in USER_DATA:
        url = USER_DATA[user_id].get('last_url')
    
    if not url:
        await query.message.edit_text("❌ Session expired. Please send the link again.")
        return
        
    # We have the URL and format_id. Let's add to queue.
    job_data = {
        "app": client,
        "chat_id": query.message.chat.id,
        "message_id": query.message.id,
        "url": url,
        "format_id": format_id,
        "is_audio": is_audio,
        "user_id": user_id
    }
    
    pos = await queue_manager.add_job(user_id, job_data, process_download)
    
    if pos == 1 and queue_manager.get_queue_stats()["active"] is None:
        await query.message.edit_text("🚀 Download starting...")
    else:
        await query.message.edit_text(f"📝 Added to queue. You are position {pos}.")

async def upload_progress(current, total, message, start_time):
    now = time.time()
    if not hasattr(message, "last_updated"):
        message.last_updated = 0
    
    # Update every 5 seconds to avoid FloodWait from Telegram
    if now - message.last_updated > 5 or current == total:
        message.last_updated = now
        percent = current * 100 / total
        elapsed = now - start_time
        speed = current / elapsed if elapsed > 0 else 0
        
        try:
            await message.edit_text(
                f"⏳ **Uploading...**\n"
                f"📊 Progress: {percent:.1f}%\n"
                f"💾 Size: {current/(1024*1024):.1f} MB / {total/(1024*1024):.1f} MB\n"
                f"🚀 Speed: {speed/(1024*1024):.1f} MB/s"
            )
        except Exception:
            pass # Ignore MessageNotModified or FloodWait exceptions during progress updates

async def process_download(job_data: dict):
    """The actual worker function executed by QueueManager."""
    app: Client = job_data["app"]
    chat_id = job_data["chat_id"]
    message_id = job_data["message_id"]
    url = job_data["url"]
    format_id = job_data["format_id"]
    is_audio = job_data.get("is_audio", False)
    user_id = job_data["user_id"]
    
    if is_audio:
        download_format = format_id if format_id != 'bestaudio' else 'bestaudio/best'
    else:
        if format_id == 'best':
            download_format = 'bestvideo+bestaudio/best'
        else:
            download_format = f"{format_id}+bestaudio/best"
    
    timestamp = int(time.time())
    download_dir = os.path.join(config.DOWNLOAD_DIR, f"{user_id}_{timestamp}")
    downloaded_file = None
    
    status_msg = await app.get_messages(chat_id, message_id)
    
    try:
        await status_msg.edit_text("⏳ Downloading... Please wait.")
        
        # Download
        downloaded_file = await DownloaderService.download_format(url, download_format, download_dir, is_audio)
        
        file_size = os.path.getsize(downloaded_file)
        if file_size > config.MAX_FILE_SIZE_BYTES:
            await status_msg.edit_text(
                f"❌ Downloaded file is too large ({file_size // (1024*1024)} MB). Max allowed is {config.MAX_FILE_SIZE_MB} MB."
            )
            return

        start_time = time.time()
        
        if file_size < 50 * 1024 * 1024:
            # File is under 50MB, upload using fast HTTP Bot API
            await status_msg.edit_text("⏳ Uploading via HTTP API (Fast)...")
            import httpx
            api_url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendDocument"
            
            # Setup proxy if configured
            proxy = config.PROXY_URL if config.PROXY_URL else None
                
            async with httpx.AsyncClient(proxy=proxy) as client:
                with open(downloaded_file, 'rb') as f:
                    files = {'document': f}
                    data = {'chat_id': chat_id, 'caption': "Here is your video! 🎬"}
                    response = await client.post(api_url, data=data, files=files, timeout=300)
            
            if response.status_code == 200:
                await status_msg.delete()
            else:
                # If HTTP fails (e.g., due to strict proxy rules), fallback to MTProto
                logger.warning(f"HTTP upload failed ({response.status_code}): {response.text}. Falling back to MTProto.")
                await app.send_document(
                    chat_id=chat_id,
                    document=downloaded_file,
                    caption="Here is your video! 🎬 (Fallback)",
                    progress=upload_progress,
                    progress_args=(status_msg, start_time)
                )
                await status_msg.delete()
        else:
            # File is over 50MB, MUST upload using MTProto
            await status_msg.edit_text("⏳ Uploading via MTProto (>50MB)...")
            await app.send_document(
                chat_id=chat_id,
                document=downloaded_file,
                caption="Here is your video! 🎬",
                progress=upload_progress,
                progress_args=(status_msg, start_time)
            )
            await status_msg.delete()
        
    except Exception as e:
        logger.error(f"Download process failed for {user_id}: {e}")
        try:
            await status_msg.edit_text(f"❌ Error during download/upload:\n`{str(e)}`")
        except Exception:
            pass
    finally:
        if not config.KEEP_DOWNLOADS:
            import shutil
            # Cleanup the unique download directory
            if os.path.exists(download_dir):
                try:
                    shutil.rmtree(download_dir, ignore_errors=True)
                    logger.info(f"Cleaned up directory: {download_dir}")
                except Exception as cleanup_err:
                    logger.error(f"Failed to clean up {download_dir}: {cleanup_err}")
        else:
            logger.info(f"Keeping downloaded files in: {download_dir} as per KEEP_DOWNLOADS config.")
