from .time import get_total_time_elapsed, get_total_increments_elapsed, get_offset_for_channel
from .audio import AudioPlayer
from .constants import AUDIO_DATA, CHANNEL_RATES, SAMPLE_RATE, BLOCK_SIZE

import time
import logging
import sounddevice
import numpy as np

logger = logging.getLogger(__name__)


class Longplayer:
    def __init__(self, gain: float = -12.0):
        self.output_stream = sounddevice.OutputStream(samplerate=SAMPLE_RATE,
                                                      channels=2,
                                                      blocksize=BLOCK_SIZE,
                                                      callback=self.audio_callback)
        self.audio_players: list[AudioPlayer] = []
        self.output_left = np.zeros(BLOCK_SIZE)
        self.output_right = np.zeros(BLOCK_SIZE)
        self.gain_linear = 10.0 ** (gain / 20)

    def audio_callback(self, outdata, num_frames, time, status):
        self.output_left[:] = 0
        self.output_right[:] = 0
        if len(self.audio_players) > 0:
            for channel_index, audio_player in enumerate(self.audio_players[:]):
                channel_samples = audio_player.get_samples(num_frames)
                pan = channel_index / 5
                self.output_left += channel_samples * (1 - np.sqrt(pan)) / len(self.audio_players)
                self.output_right += channel_samples * (np.sqrt(pan)) / len(self.audio_players)

        outdata[:,0] = self.output_left * self.gain_linear
        outdata[:,1] = self.output_right * self.gain_linear

    def start(self):
        """
        Begin playback using the default system audio output device, based on the system's current timestamp.
        """

        print("Longplayer, by Jem Finer.")

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
        print("Longplayer has been running for %d years, %d days, %d hours, %d minutes, %d seconds." % (years, days, hours, minutes, seconds))

        increments = get_total_increments_elapsed()
        logger.info("-------------------------------------------------------------------------------------")
        logger.info("Total increments elapsed: %f" % increments)

        #---------------------------------------------------------------------------------------------------------------
        # Open the default sound output device.
        #---------------------------------------------------------------------------------------------------------------
        self.output_stream.start()

        last_increments_int = None

        while True:
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
                logger.info("-------------------------------------------------------------------------------------")
                if last_increments_int is None:
                    logger.info("Current increment index: %d" % (increments_int))
                else:
                    logger.info("Beginning new increment, new increment index: %d" % (increments_int))

                for audio_player in self.audio_players:
                    audio_player.fade_down()

                for channel_index, rate in enumerate(CHANNEL_RATES):
                    offset, position = get_offset_for_channel(increments, channel_index)
                    logger.info(" - channel %d: offset %.3fs, position %.3fs" % (channel_index, offset, position))

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

            time.sleep(0.2)
