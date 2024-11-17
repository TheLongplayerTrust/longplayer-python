# Longplayer in Python

[Longplayer](https://longplayer.org/) is a thousand year long musical composition by Jem Finer.

This is an open-source implementation of Longplayer in Python, which can be run on any compatible computer with audio output.

For more information about Longplayer, read an [overview of the piece](https://longplayer.org/about/overview/).

## Requirements

- Python 3
- A Linux or macOS system with audio output

## Installation

The `libsamplerate` and `portaudio` libraries are required for audio playback.

* On macOS: `brew install libsamplerate`
* On Raspberry Pi: `sudo apt install libportaudio2`

To install Longplayer from the command line:

```
pip3 install longplayer
```

## Usage

To run Longplayer from the command line:

```
longplayer
```

Press Ctrl-C to stop playback.
