from .time import get_total_time_elapsed, get_total_increments_elapsed, get_position_for_layer
from .audio import AudioPlayer
from .constants import LAYER_RATES, SAMPLE_RATE, DEFAULT_BUFFER_SIZE, DEFAULT_AUDIO_GAIN, AUDIO_PATH
from .utils import download_longplayer_audio
from typing import Optional

import math
import time
import logging
import threading
import soundfile
import sounddevice
import blockbuffer
import numpy as np

logger = logging.getLogger(__name__)


class Longplayer:
    def __init__(self,
                 output_device: int = None,
                 num_channels: int = 2,
                 buffer_size: int = DEFAULT_BUFFER_SIZE,
                 gain: float = DEFAULT_AUDIO_GAIN,
                 solo: Optional[int] = None):
        """
        Longplayer composition logic.

        Connects to the system's default audio output device,
        creates a mono sample player for each layer of audio,
        and performs the timing logic of stepping forwards through increments.

        Args:
            output_device (int, optional): Index of the audio output device to use.
                                           If not specified, use the system default.
            num_channels (int, optional): Number of audio output channels. Can be 1, 2 or 6.
                                          When 1, output is a mono mix.
                                          When 2, output is spread across a stereo field.
                                          When 6, output is separated into 6 individual channels.
                                          Defaults to 2.
            buffer_size (int): Length of audio output buffer, in samples.
            gain (float, optional): Output gain, in decibels. Defaults to -6.0.
            solo (int, optional): If specified, solo a particular layer number, from 0 to 5.

        Raises:
            ValueError: _description_
        """
        self.output_device = output_device
        self.num_channels = num_channels
        self.buffer_size = buffer_size
        self.solo = solo
        if self.solo not in [0, 1, 2, 3, 4, 5, None]:
            raise ValueError("Invalid value for solo (must be within 0..5)")

        if num_channels not in (1, 2, 6):
            raise ValueError("Invalid number of channels: %d (must be one of 1, 2, 6)" % num_channels)
        if output_device is not None:
            sounddevice.default.device = output_device


        #--------------------------------------------------------------------------------
        # Do not specify the number of channels to use, but instead use
        # all available channels on the device.
        #--------------------------------------------------------------------------------
        self.output_stream = sounddevice.OutputStream(samplerate=SAMPLE_RATE,
                                                      blocksize=self.buffer_size,
                                                      callback=self.audio_callback)
        self.audio_players: list[AudioPlayer] = []
        
        self.thread = None
        self.gain_linear = 10 ** (gain / 20)
        self.is_running = False
        self.output_block = np.zeros((buffer_size, num_channels))
        self.blockbuffer = blockbuffer.BlockBuffer(block_size=self.buffer_size, num_channels=num_channels, always_2d=True)

        self.render_thread = threading.Thread(target=self.render_audio_loop)
        self.render_thread.daemon = True
        self.render_thread.start()
        
    def audio_callback(self, outdata, num_frames, time, status):
        # Be sure to write silence to all channels.
        # Otherwise, some backends (e.g. pulseaudio) will generate noise to unused channels.

        block = self.blockbuffer.get()
        if block is not None:
            outdata[:,:self.num_channels] = block
            outdata[:,self.num_channels:] = 0
        else:
            outdata[:] = 0
            logger.warning("audio_callback: No samples available!")

    def render_audio_loop(self):
        while True:
            if self.blockbuffer.length < self.buffer_size * 4:
                self.render_block(self.buffer_size)
            time.sleep(0.005)

    def render_block(self, num_frames):
        self.output_block[:] = 0.0
        if len(self.audio_players) > 0:
            for player_index, audio_player in enumerate(self.audio_players):
                channel_index = player_index % 6

                if self.solo is not None and self.solo != channel_index:
                    continue
                if audio_player.is_finished:
                    continue

                channel_samples = audio_player.get_samples(num_frames)
                if self.num_channels == 1:
                    self.output_block[:,0] += channel_samples
                elif self.num_channels == 2:
                    pan = channel_index / 5
                    self.output_block[:,0] += channel_samples * (1 - math.sqrt(pan)) / self.num_channels
                    self.output_block[:,1] += channel_samples * (math.sqrt(pan)) / self.num_channels
                elif self.num_channels == 6:
                    self.output_block[:,channel_index] += channel_samples / self.num_channels

        self.output_block *= self.gain_linear
        self.blockbuffer.extend(self.output_block)
    
    def print_run_time(self):
        #--------------------------------------------------------------------------------
        # Calculate the number of units elapsed since the beginning of the piece,
        # for terminal display.
        #--------------------------------------------------------------------------------
        timedelta = get_total_time_elapsed()
        days_per_year = 365.2425
        years = timedelta.days // days_per_year
        days = timedelta.days - (years * days_per_year)
        hours = timedelta.seconds // 3600
        minutes = (timedelta.seconds - hours * 3600) // 60
        seconds = timedelta.seconds % 60
        logger.info("Longplayer has been running for %d years, %d days, %d hours, %d minutes, %d seconds." % (years, days, hours, minutes, seconds))

        increments = get_total_increments_elapsed()
        logger.debug("-------------------------------------------------------------------------------------")
        logger.debug("Total increments elapsed: %f" % increments)

    def run(self):
        """
        Begin playback. Blocks indefinitely.
        """

        download_longplayer_audio()
        audio_fd = soundfile.SoundFile(AUDIO_PATH)
        assert audio_fd.samplerate == SAMPLE_RATE
        audio_data = audio_fd.read()

        logger.info("Longplayer, by Jem Finer.")
        self.print_run_time()

        #---------------------------------------------------------------------------------------------------------------
        # Open the default sound output device.
        #---------------------------------------------------------------------------------------------------------------
        self.output_stream.start()

        last_increments_int = None
        self.is_running = True

        while self.is_running:
            #--------------------------------------------------------------------------------
            # Audio loop.
            #  - Check whether we are beginning a new section. If so:
            #     - begin fade down of existing AudioPlayers
            #     - create an array of new AudioPlayer objects to play the six sections
            #  - Mix the output of all currently-playing AudioPlayers
            #  - Write the output (synchronously) to the audio device
            #--------------------------------------------------------------------------------
            increments = get_total_increments_elapsed()
            increments_int = int(increments)

            if last_increments_int is None or increments_int > last_increments_int:
                logger.debug("-------------------------------------------------------------------------------------")
                if last_increments_int is None:
                    logger.debug("Current increment index: %d" % (increments_int))
                else:
                    logger.debug("Beginning new increment, new increment index: %d" % (increments_int))

                for audio_player in self.audio_players:
                    audio_player.fade_down()

                for layer_index, rate in enumerate(LAYER_RATES):
                    section_start_position, section_playhead_position = get_position_for_layer(increments, layer_index)
                    logger.debug(" - layer %d: start position %.3fs, playhead position %.3fs" % (layer_index, section_start_position, section_playhead_position))

                    section_start_position_samples = section_start_position * SAMPLE_RATE
                    section_playhead_position_samples = section_playhead_position * SAMPLE_RATE
                    initial_phase = int(section_start_position_samples + section_playhead_position_samples)
                    player = AudioPlayer(audio_data=audio_data,
                                         initial_phase=initial_phase,
                                         rate=rate)
                    self.audio_players.append(player)

                last_increments_int = increments_int

            for audio_player in self.audio_players[:]:
                if audio_player.is_finished:
                    self.audio_players.remove(audio_player)

            time.sleep(0.1)

        for audio_player in self.audio_players[:]:
            audio_player.fade_down(0.2)

    def start(self):
        """
        Begin playback using the default system audio output device, based on the system's current timestamp.
        """

        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False
