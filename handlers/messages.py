import json
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
import config
from logger import get_logger
from utils.helpers import is_valid_url, format_size, format_duration
from services.downloader import DownloaderService

logger = get_logger(__name__)

# Global memory to store the last URL sent by a user, 
# because callback_data is limited to 64 bytes.
USER_DATA = {}

@Client.on_message(filters.text & ~filters.command(["start", "help", "stats", "showqueue", "cancel", "cleanup", "ping"]))
async def handle_message(client: Client, message: Message):
    """Handles text messages, checking for URLs and responding with available formats."""
    user_id = message.from_user.id
    if not config.is_user_allowed(user_id):
        return

    text = message.text
    if not text:
        return
        
    # Extract first word as URL candidate
    url = text.split()[0]
    
    if not is_valid_url(url):
        # Ignore normal chat messages, maybe reply if it looks like they tried
        if "http" in text:
            await message.reply_text("That does not look like a valid URL.")
        return

    processing_msg = await message.reply_text("⏳ Fetching metadata... Please wait.")
    
    try:
        info = await DownloaderService.extract_info(url)
    except Exception as e:
        logger.error(f"Error fetching info for {url}: {e}")
        await processing_msg.edit_text(f"❌ Error fetching metadata:\n`{str(e)}`")
        return

    # Check duration limit
    duration = info.get('duration', 0)
    if duration > config.MAX_VIDEO_DURATION:
        await processing_msg.edit_text(f"❌ Video is too long. Max allowed is {format_duration(config.MAX_VIDEO_DURATION)}.")
        return

    title = info.get('title', 'Unknown Title')
    duration_str = format_duration(duration)
    formats = info.get('formats', [])
    
    # Let's collect unique resolutions
    filtered_formats = []
    seen_resolutions = set()
    
    # Sort formats by resolution, then size
    formats.sort(key=lambda x: (x.get('height', 0) or 0, x.get('filesize', 0) or x.get('filesize_approx', 0) or 0), reverse=True)
    
    for f in formats:
        # We want video formats
        if f.get('vcodec') == 'none':
            continue # audio only
            
        height = f.get('height')
        if not height:
            continue
            
        res_label = f"{height}p"
        
        # Skip if we already have a better format for this resolution
        if res_label in seen_resolutions:
            continue
            
        size_bytes = f.get('filesize') or f.get('filesize_approx') or 0
        
        if size_bytes > config.MAX_FILE_SIZE_BYTES:
            continue # Skip formats that are too large
            
        ext = f.get('ext', 'mkv')
        format_id = f.get('format_id')
        has_audio = f.get('acodec') != 'none'
        
        label = f"{res_label} | {ext} | {format_size(size_bytes)}"
        if not has_audio:
            label += " (merged)" # Will be merged with audio
            
        # Store url in memory
        if user_id not in USER_DATA:
            USER_DATA[user_id] = {}
        USER_DATA[user_id]['last_url'] = url
        
        cb_data = f"dl|{format_id}"
        if len(cb_data) <= 64:
            filtered_formats.append(
                InlineKeyboardButton(label, callback_data=cb_data)
            )
            seen_resolutions.add(res_label)
            
    if not filtered_formats:
        await processing_msg.edit_text(
            f"🎬 **{title}**\n⏱ {duration_str}\n\n"
            f"❌ No suitable formats found under {config.MAX_FILE_SIZE_MB}MB."
        )
        return

    # Build keyboard (2 buttons per row)
    keyboard = []
    row = []
    for btn in filtered_formats:
        row.append(btn)
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text_content = f"🎬 **{title}**\n⏱ {duration_str}\n\nSelect a format to download:"
    await processing_msg.edit_text(text_content, reply_markup=reply_markup)
