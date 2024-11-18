from .time import get_total_time_elapsed, get_total_increments_elapsed, get_offset_for_channel
from .audio import AudioPlayer
from .constants import AUDIO_DATA, CHANNEL_RATES, SAMPLE_RATE, BLOCK_SIZE

import math
import time
import logging
import threading
import sounddevice

logger = logging.getLogger(__name__)


class Longplayer:
    def __init__(self, num_channels: int = 2, gain: float = -6.0):
        """
        Longplayer composition logic.

        Connects to the system's default audio output device,
        creates a mono sample player for each layer of audio,
        and performs the timing logic of stepping forwards through increments.

        Args:
            num_channels (int, optional): Number of audio output channels. Can be 1, 2 or 6.
                                          When 1, output is a mono mix.
                                          When 2, output is spread across a stereo field.
                                          When 6, output is separated into 6 individual channels.
                                          Defaults to 2.
            gain (float, optional): Output gain, in decibels. Defaults to -6.0.

        Raises:
            ValueError: _description_
        """
        self.num_channels = num_channels
        if num_channels not in (1, 2, 6):
            raise ValueError("Invalid number of channels: %d (must be one of 1, 2, 6)" % num_channels)
        self.output_stream = sounddevice.OutputStream(samplerate=SAMPLE_RATE,
                                                      channels=self.num_channels,
                                                      blocksize=BLOCK_SIZE,
                                                      callback=self.audio_callback)
        self.audio_players: list[AudioPlayer] = []
        self.output_block = [[0] * BLOCK_SIZE for channel in range(self.num_channels)]
        self.thread = None
        self.gain_linear = 10 ** (gain / 20)
        self.is_running = False

    def audio_callback(self, outdata, num_frames, time, status):
        for channel in range(self.num_channels):
            for frame in range(num_frames):
                self.output_block[channel][frame] = 0

        if len(self.audio_players) > 0:
            for channel_index, audio_player in enumerate(self.audio_players):
                channel_samples = audio_player.get_samples(num_frames)
                if self.num_channels == 1:
                    for frame in range(num_frames):
                        self.output_block[0][frame] += channel_samples[frame] / self.num_channels
                elif self.num_channels == 2:
                    pan = (channel_index % 6) / 5
                    for frame in range(num_frames):
                        self.output_block[0][frame] += channel_samples[frame] * (1 - math.sqrt(pan)) / self.num_channels
                        self.output_block[1][frame] += channel_samples[frame] * (math.sqrt(pan)) / self.num_channels
                elif self.num_channels == 6:
                    for frame in range(num_frames):
                        self.output_block[channel_index][frame] = channel_samples[frame]

        for channel in range(self.num_channels):
            for frame in range(num_frames):
                outdata[frame][channel] = self.output_block[channel][frame] * self.gain_linear
    
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
            #  - Check whether we are beginning a new segment. If so:
            #     - begin fade down of existing AudioPlayers
            #     - create an array of new AudioPlayer objects to play the six segments
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

                for channel_index, rate in enumerate(CHANNEL_RATES):
                    offset, position = get_offset_for_channel(increments, channel_index)
                    logger.debug(" - channel %d: offset %.3fs, position %.3fs" % (channel_index, offset, position))

                    offset_samples = offset * SAMPLE_RATE
                    position_samples = position * SAMPLE_RATE
                    player = AudioPlayer(audio_data=AUDIO_DATA,
                                         initial_phase=offset_samples + position_samples,
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
