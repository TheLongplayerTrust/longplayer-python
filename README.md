# Longplayer in Python

[Longplayer](https://longplayer.org/) is a thousand year long musical composition by Jem Finer.

This is an open-source implementation of Longplayer in Python, which can be run on any compatible computer with audio output.

For more information about Longplayer, read an [overview of the piece](https://longplayer.org/about/overview/).

## Requirements

- Python 3
- A Linux or macOS system with audio output
- The Longplayer audio file (20-20.wav)

## Installation

The `libsamplerate` library is required for audio playback.

* On macOS: `brew install libsamplerate`

To install Longplayer, clone this repository and run:

```
pip3 install .
```

## Usage

To run Longplayer from within the repository directory, you must first copy the Longplayer audio file `20-20.wav` to the `audio` directory. Then, run:

```
bin/longplayer
```
