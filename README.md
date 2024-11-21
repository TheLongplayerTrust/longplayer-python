# Longplayer in Python

[Longplayer](https://longplayer.org/) is a thousand year long musical composition by Jem Finer.

This is an open-source implementation of Longplayer in Python, which can be run on any compatible computer with audio output.

For more information about Longplayer, read an [overview of the piece](https://longplayer.org/about/overview/).

## Requirements

- A Linux (including Raspberry Pi), macOS or Windows system with audio output
- Python 3.9 or above ([python.org](https://www.python.org/downloads/))

## Installation

If you're using Linux (including Raspberry Pi), you will need to install the `portaudio` library for audio output: `sudo apt install libportaudio2`

To install Longplayer from the command line, for any platform, open up a terminal session and enter:

```
pip3 install longplayer
```

## Usage

To run Longplayer from the command line, run:

```
python3 -m longplayer
```

Press Ctrl-C to stop playback.

## Troubleshooting

If you are hearing stuttery playback, try:

- increasing the audio buffer size: `python3 -m longplayer --buffer-size 4096`
- mono (single-channel) playback: `python3 -m longplayer --channels 1`

To see all of the command-line options: `python -m longplayer --help`