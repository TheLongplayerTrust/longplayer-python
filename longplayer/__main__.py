from longplayer import Longplayer, DEFAULT_AUDIO_GAIN, DEFAULT_BUFFER_SIZE
from longplayer.utils import parse_icecast_config

import sounddevice
import argparse
import logging
import time
import sys
import os

logger = logging.getLogger("longplayer")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Longplayer command-line application")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet output")
    parser.add_argument("--gain", type=float, help="Gain, in decibels (default: 0.0)", default=DEFAULT_AUDIO_GAIN)
    parser.add_argument("-c", "--channels", type=int, help="Number of channels (default: 2)", default=2)
    parser.add_argument("-b", "--buffer-size", type=int, help="Audio buffer size (default: 1024)", default=DEFAULT_BUFFER_SIZE)
    parser.add_argument("--list-output-devices", action="store_true", help="List available audio output devices")
    parser.add_argument("--output-device", type=int, help="Selected audio output device (use system default if not specified)", default=None)
    parser.add_argument("--solo", type=int, help="Solo a specified layer, from 0 to 5", default=None)
    parser.add_argument("--log", action="store_true", help="Enable logging to logs/longplayer.log")
    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.WARNING
    logging.basicConfig(level=log_level, format="%(message)s")

    if args.log:
        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler("logs/longplayer.log")
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        file_handler.setFormatter(formatter)
        logging.getLogger().addHandler(file_handler)

    if args.list_output_devices:
        print(sounddevice.query_devices())
        sys.exit(1)

    # Parse Icecast configuration if available
    icecast_config = parse_icecast_config()

    try:
        longplayer = Longplayer(output_device=args.output_device,
                                num_channels=args.channels,
                                buffer_size=args.buffer_size,                        
                                gain=args.gain,
                                solo=args.solo,
                                icecast_config=icecast_config)
        longplayer.start()
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        logger.info("\nExiting Longplayer...")
        longplayer.stop()