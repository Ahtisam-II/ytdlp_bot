import asyncio
import os
import sys

# Ensure the workspace directory is in the python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.downloader import DownloaderService
from logger import get_logger

logger = get_logger("test_script")

async def test_download():
    url = "https://youtu.be/3j7bhOvW6jw?si=iq7gyhNKFHrSYJoH"
    logger.info(f"Testing info extraction for {url}")
    
    try:
        # Extract metadata
        info = await DownloaderService.extract_info(url)
        title = info.get('title', 'Unknown Title')
        logger.info(f"Extracted info successfully. Title: {title}")
        
        # We will pick the best video format that has audio or merge it with audio.
        # Actually yt-dlp 'best' usually gives a decent format or we can use 'bestvideo+bestaudio/best'
        # To test our service logic, we'll download 'best' or 'bestvideo+bestaudio/best'.
        format_id = "bestvideo+bestaudio/best"
        
        output_template = "./downloads/test_video.%(ext)s"
        os.makedirs("./downloads", exist_ok=True)
        
        logger.info(f"Starting download of format {format_id}")
        file_path = await DownloaderService.download_format(url, format_id, output_template)
        logger.info(f"Download complete! File saved at: {file_path}")
        
        # Verify file exists
        if os.path.exists(file_path):
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            logger.info(f"Verified file exists! Size: {file_size_mb:.2f} MB")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_download())
