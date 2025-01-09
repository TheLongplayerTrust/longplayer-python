import requests
import zipfile
import logging
import os

from .constants import AUDIO_URL, AUDIO_ROOT, AUDIO_PATH

logger = logging.getLogger(__name__)


def download_longplayer_audio():
    zip_file_name = os.path.basename(AUDIO_URL)
    zip_file_path = os.path.join(AUDIO_ROOT, zip_file_name)

    if not os.path.exists(AUDIO_PATH):
        logger.warning("Downloading Longplayer audio file...")
        download_file(AUDIO_URL, zip_file_path)
        with zipfile.ZipFile(zip_file_path, "r") as zip_fd:
            zip_fd.extractall(AUDIO_ROOT)
    
def download_file(url, local_path):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:106.0) Gecko/20100101 Firefox/106.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

    with requests.get(url, stream=True, headers=headers) as r:
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
