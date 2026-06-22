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
    
    # Build keyboard
    keyboard = []
    
    # Store url in memory
    if user_id not in USER_DATA:
        USER_DATA[user_id] = {}
    USER_DATA[user_id]['last_url'] = url

    # 1. Default Best Options
    keyboard.append([
        InlineKeyboardButton("🌟 Best Video & Audio", callback_data="dl|best|v"),
        InlineKeyboardButton("🎵 Best Audio Only", callback_data="dl|bestaudio|a")
    ])

    # 2. Extract formats
    video_formats = {}
    audio_formats = {}

    for f in formats:
        format_id = f.get('format_id')
        ext = f.get('ext', 'unk')
        size_bytes = f.get('filesize') or f.get('filesize_approx') or 0
        
        if size_bytes > config.MAX_FILE_SIZE_BYTES:
            continue

        # Audio only
        if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
            if ext not in audio_formats or size_bytes > audio_formats[ext]['size']:
                audio_formats[ext] = {'id': format_id, 'size': size_bytes}
            continue

        # Video
        height = f.get('height')
        if not height:
            continue
            
        fps = f.get('fps')
        fps_str = f"{fps}" if fps and fps > 30 else ""
        res_label = f"{height}p{fps_str}"
        
        # Group by resolution + extension
        group_key = f"{res_label}_{ext}"
        
        # Keep the one with the highest bitrate/size in this group
        if group_key not in video_formats or size_bytes > video_formats[group_key]['size']:
            video_formats[group_key] = {
                'id': format_id,
                'res': res_label,
                'ext': ext,
                'size': size_bytes,
                'has_audio': f.get('acodec') != 'none'
            }

    # Sort video formats highest resolution first
    sorted_videos = sorted(video_formats.values(), key=lambda x: int(x['res'].split('p')[0]), reverse=True)
    
    # Add video buttons (2 per row)
    row = []
    for vf in sorted_videos[:20]:  # Limit to top 20 to avoid massive keyboards
        label = f"🎥 {vf['res']} {vf['ext']}"
        if vf['size'] > 0:
            label += f" ({format_size(vf['size'])})"
        
        cb_data = f"dl|{vf['id']}|v"
        if len(cb_data) <= 64:
            row.append(InlineKeyboardButton(label, callback_data=cb_data))
            if len(row) == 2:
                keyboard.append(row)
                row = []
    if row:
        keyboard.append(row)

    # Add audio buttons (if any explicitly requested, but 'Best Audio Only' usually suffices)
    # We will just append them at the bottom if found
    row = []
    for ext, af in audio_formats.items():
        if ext in ['m4a', 'mp3', 'webm', 'opus']:  # common audio formats
            label = f"🎧 {ext}"
            if af['size'] > 0:
                label += f" ({format_size(af['size'])})"
            cb_data = f"dl|{af['id']}|a"
            if len(cb_data) <= 64:
                row.append(InlineKeyboardButton(label, callback_data=cb_data))
                if len(row) == 2:
                    keyboard.append(row)
                    row = []
    if row:
        keyboard.append(row)

    if len(keyboard) == 1: # Only Best options exist, maybe no formats found
        pass
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text_content = f"🎬 **{title}**\n⏱ {duration_str}\n\nSelect a format to download:"
    await processing_msg.edit_text(text_content, reply_markup=reply_markup)
