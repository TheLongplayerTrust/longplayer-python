# Installation instructions for a Raspberry Pi Listening Post

This guide includes information on setting up a Raspberry Pi Longplayer listening post. You will need a good working understanding of the command line and general Pi/Linux configuration.

Clock synchronisation can either be done via the internet (using NTP, either by ethernet or Wi-Fi), or via a GPS board with an integrated real-time clock. The latter option enables accurate time-sync in offline situations.

It also includes support for an optional OLED status display.

# Parts list

Below is a list of recommended parts. 

- Computing
    - [Raspberry Pi 5 4GB](https://thepihut.com/products/raspberry-pi-5?variant=42531604922563)
    - [27W power supply](https://thepihut.com/products/raspberry-pi-27w-usb-c-power-supply?variant=42531604168899)
    - [Sandisk Extreme microSD card](https://shop.sandisk.com/en-gb/products/memory-cards/microsd-cards/sandisk-extreme-uhs-i-microsd?sku=SDSQXAF-032G-GN6MA)
- Audio
    - Any good-quality class-compliant audio interface capable of 44100Hz is fine. 
    - Recommended for stereo (2-channel) output: [Creative Sound Blaster Play!3](https://www.amazon.co.uk/Creative-Sound-Blaster-Resolution-External/dp/B073KTPNDR/) 
    - Recommended for multichannel (6-channel) output: [ESI Gigaport EX](https://www.amazon.co.uk/ESI-Gigaport-USB-Audio-Interface/dp/B08CY57864)
- GPS/RTC (optional)
    - [Uputronics GPS/RTC board](https://thepihut.com/products/raspberry-pi-gps-hat?variant=20063163711550)
    - [5M GPS antenna](https://thepihut.com/products/gps-antenna-external-active-antenna-3-5v-28db-5-meter-sma?variant=27740548753) 
- OLED display (optional)
    - [Extra-tall stacking GPIO header](https://thepihut.com/products/40-pin-extra-tall-header-push-fit-version-single-shroud?variant=20063047942206) 
    - [2.23” OLED HAT](https://thepihut.com/products/128x32-2-23inch-oled-display-hat-for-raspberry-pi?variant=31844782374974)
    - [Black nylon M2.5 standoffs](https://thepihut.com/products/adafruit-black-nylon-screw-and-stand-off-set-m2-5-thread?variant=31955887377)


# Guide

## 1. General device setup

- Using Raspberry Pi Imager, flash a high-endurance microSD card (8GB or above) with the latest Raspberry Pi OS Lite
- Update the system: `sudo apt update`

## 2. Install the Longplayer player code

```sh
# cmake and python3-dev are needed for to build libsamplerate
# libsndfile needed to read audio file
sudo apt install -y git cmake python3-dev libsndfile1 libportaudio2
git clone git@github.com:TheLongplayerTrust/longplayer-python
cd longplayer-python
python3 -m venv .venv
. .venv/bin/activate
pip3 install -e .

# List available audio devices
python3 -m longplayer --list-output-devices

# Play Longplayer through the selected output device
python3 -m longplayer --output-device 0 --gain -12
```

To install the player as a system service, to boot on startup:

```
sudo cp auxiliary/longplayer.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable longplayer
sudo systemctl start longplayer
```

## 3. Install the GPS/RTC drivers and daemons

- In general, Raspberry Pi's default NTP time sync is sufficient. However, devices that have no internet connectivity may wish to use GPS/RTC sync to maintain an accurate clock.
- If using the Uputronics GPS/RTC board, install the kernel modules, drivers and daemons as per the [Uputronics GPS/RTC datasheet](https://store.uputronics.com/products/raspberry-pi-gps-rtc-expansion-board)
- No specific link is needed between the Longplayer code and GPS board. The board simply ensures that the system clock is accurate, which the Longplayer code uses to calculate the algorithm's output.

## 4. OLED display

First, enable SPI within `sudo raspi-config`, and reboot. Then, install and run the `longplayer-oled-display` package, from within `/home/pi`:

```sh
git clone git@github.com:TheLongplayerTrust/longplayer-oled-display
cd longplayer-oled-display
python3 -m venv .venv
. .venv/bin/activate

pip3 install -r requirements.txt
python3 display-status.py
```

To install the package as a system service, to boot on startup:

```
sudo cp auxiliary/longplayer-oled-display.service /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable longplayer-oled-display
sudo systemctl start longplayer-oled-display
```