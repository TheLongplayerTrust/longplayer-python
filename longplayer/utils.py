import requests
import zipfile
import logging
import os
import configparser

from .constants import AUDIO_URL, AUDIO_ROOT, AUDIO_PATH
from .streaming import IcecastConfig

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


def parse_icecast_config() -> IcecastConfig | None:
    """
    Parse the Longplayer config file at ~/.config/longplayer/config.

    Returns:
        IcecastConfig if the [stream] section exists and all fields are present,
        None if the config file doesn't exist or [stream] section is not present.

    Raises:
        ValueError: If any required field is empty or missing.
    """
    config_dir = os.path.join(os.path.expanduser("~"), ".config", "longplayer")
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, "config")
    if not os.path.exists(config_path):
        return None

    config_parser = configparser.ConfigParser()
    config_parser.read(config_path)

    if not config_parser.has_section("stream"):
        return None

    # Extract all required fields
    required_fields = ["host", "mount", "port", "user", "password"]
    config_values = {}

    for field in required_fields:
        if not config_parser.has_option("stream", field):
            raise ValueError(f"Config file is missing required field: {field}")

        value = config_parser.get("stream", field).strip()
        if not value:
            raise ValueError(f"Config field '{field}' cannot be empty")

        config_values[field] = value

    # Convert port to int
    try:
        port = int(config_values["port"])
    except ValueError:
        raise ValueError(f"Config field 'port' must be a valid integer, got: {config_values['port']}")

    return IcecastConfig(host=config_values["host"],
                         mount=config_values["mount"],
                         port=port,
                         user=config_values["user"],
                         password=config_values["password"])
