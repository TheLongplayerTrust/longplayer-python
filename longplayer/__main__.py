from longplayer import Longplayer, DEFAULT_AUDIO_GAIN, DEFAULT_BUFFER_SIZE
import argparse
import logging
import time


def main(num_channels: int,
         buffer_size: int,
         gain: float):
    try:
        longplayer = Longplayer(num_channels=num_channels,
                                buffer_size=buffer_size,
                                gain=gain)
        longplayer.start()
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting...")
        longplayer.stop()
        time.sleep(0.5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Longplayer command-line application")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="Quiet output")
    parser.add_argument("--gain", type=float, help="Gain, in decibels (default: -6.0)", default=DEFAULT_AUDIO_GAIN)
    parser.add_argument("-c", "--num-channels", type=int, help="Number of channels (default: 2)", default=2)
    parser.add_argument("-b", "--buffer-size", type=int, help="Audio buffer size (default: 1024)", default=DEFAULT_BUFFER_SIZE)
    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.WARNING
    logging.basicConfig(level=log_level, format="%(message)s")

    main(num_channels=args.num_channels,
         buffer_size=args.buffer_size,
         gain=args.gain)