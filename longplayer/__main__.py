from longplayer import Longplayer, DEFAULT_AUDIO_GAIN
import argparse
import logging
import time


def main(num_channels: int,
         gain: float):
    try:
        longplayer = Longplayer(num_channels=num_channels,
                                gain=gain)
        longplayer.start()
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        longplayer.stop()
        time.sleep(0.5)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Longplayer command-line application")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose output")
    parser.add_argument("-q", "--quiet", action="store_true", help="quiet output")
    parser.add_argument("--gain", type=float, help="gain, in decibels (default: -6.0)", default=-6)
    parser.add_argument("-c", "--num-channels", type=int, help="number of channels (default: 2)", default=2)
    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    elif args.quiet:
        log_level = logging.WARNING
    logging.basicConfig(level=log_level, format="%(message)s")

    main(num_channels=args.num_channels,
         gain=args.gain)