import asyncio
import json
from logger import get_logger

logger = get_logger(__name__)

class DownloaderService:
    @staticmethod
    async def extract_info(url: str) -> dict:
        """
        Extracts metadata using yt-dlp -J.
        Returns the parsed JSON dictionary.
        """
        logger.info(f"Extracting info for URL: {url}")
        process = await asyncio.create_subprocess_exec(
            "yt-dlp", "-J", "--no-playlist", url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            logger.error(f"yt-dlp extraction failed: {error_msg}")
            raise RuntimeError(f"Failed to extract video info: {error_msg}")
        
        try:
            info = json.loads(stdout.decode())
            return info
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse yt-dlp output: {e}")
            raise RuntimeError("Invalid output from yt-dlp.")

    @staticmethod
    async def download_format(url: str, format_id: str, download_dir: str, is_audio: bool = False) -> str:
        """
        Downloads a specific format. It saves it inside download_dir with its original title.
        """
        import os
        os.makedirs(download_dir, exist_ok=True)
        output_template = os.path.join(download_dir, "%(title)s.%(ext)s")
        
        logger.info(f"Downloading format {format_id} for URL: {url} to {output_template} (Audio Only: {is_audio})")
        
        args = [
            "yt-dlp",
            "-f", format_id,
            "--no-playlist",
            "-o", output_template
        ]
        
        if is_audio:
            args.extend(["--extract-audio", "--audio-format", "best"])
        else:
            args.extend(["--merge-output-format", "mkv", "--remux-video", "mkv"])
            
        args.append(url)
        
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode().strip()
            logger.error(f"yt-dlp download failed: {error_msg}")
            raise RuntimeError(f"Download failed: {error_msg}")
        
        logger.info(f"Download completed for URL: {url}")
        
        downloaded_files = os.listdir(download_dir)
        if not downloaded_files:
            raise FileNotFoundError(f"Could not find downloaded file in {download_dir}")
        
        return os.path.join(download_dir, downloaded_files[0])
