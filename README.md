# Longplayer in Python

[Longplayer](https://longplayer.org/) is a thousand year long musical composition by Jem Finer.

This is an open-source implementation of Longplayer in Python, which can be run on any compatible computer with audio output.

For more information about Longplayer, read an [overview of the piece](https://longplayer.org/about/overview/).

## Requirements

- Python 3
- A Linux or macOS system with audio output

## Installation

On Linux (including Raspberry Pi), the `portaudio` library must be installed: `sudo apt install libportaudio2`

To install Longplayer from the command line:

```
pip3 install longplayer
```

## Usage

To run Longplayer from the command line, run:

```
python3 -m longplayer
```

Press Ctrl-C to stop playback.
