from .time import get_total_time_elapsed, get_total_increments_elapsed, get_offset_for_channel
from .audio import AudioPlayerVarispeed
from .constants import AUDIO_DATA, CHANNEL_RATES, SAMPLE_RATE, BLOCK_SIZE
from .renderer import BarRenderer

import sys
import logging
import sounddevice
import numpy as np

logger = logging.getLogger(__name__)


class Longplayer (object):
    def __init__(self, render_score=False):
        self.render_score = render_score
        self.channel_offsets = [ 0 ] * len(CHANNEL_RATES)

    def start(self):
        """
        Begin playback using the default system audio output device, based on the system's current timestamp.
        """
        print("Longplayer, by Jem Finer.")
        self.print_time_elapsed()

        increments = get_total_increments_elapsed()
        logger.info("-------------------------------------------------------------------------------------")
        logger.info("Total increments elapsed: %f" % increments)

        #---------------------------------------------------------------------------------------------------------------
        # Open the default sound output device.
        #---------------------------------------------------------------------------------------------------------------
        out = sounddevice.OutputStream(channels=1, blocksize=BLOCK_SIZE)
        out.start()

        audio_players = []
        last_increments_int = None

        if self.render_score:
            self.renderer = BarRenderer(75, 6)

        while True:
            #-----------------------------------------------------------------------------------------------------------
            # Audio loop.
            #  - Check whether we are beginning a new segment. If so:
            #     - begin fade down of existing AudioPlayers
            #     - create an array of new AudioPlayer objects to play the six segments
            #  - Mix the output of all currently-playing AudioPlayers
            #  - Write the output (synchronously) to the audio device
            #-----------------------------------------------------------------------------------------------------------
            increments = get_total_increments_elapsed()
            increments_int = int(increments)
            increments_frac = increments - increments_int

            if last_increments_int is None or increments_int > last_increments_int:
                logger.info("-------------------------------------------------------------------------------------")
                logger.info("Begun new increment, currently elapsed: %d" % increments_int)

                for audio_player in audio_players:
                    audio_player.fade_down()

                for channel_index, rate in enumerate(CHANNEL_RATES):
                    offset, position = get_offset_for_channel(increments, channel_index)
                    logger.debug(" - channel %d: offset %.3fs, position %.3fs" % (channel_index, offset, position))

                    offset_samples = offset * SAMPLE_RATE
                    self.channel_offsets[channel_index] = offset_samples
                    position_samples = position * SAMPLE_RATE
                    audio_players.append(AudioPlayerVarispeed(AUDIO_DATA, offset_samples + position_samples, rate))

            last_increments_int = increments_int

            output = np.zeros(BLOCK_SIZE)
            for audio_player in audio_players:
                channel_samples = audio_player.get_samples(BLOCK_SIZE)
                output = output + channel_samples
                if audio_player.amplitude_level == 0.0:
                    audio_players.remove(audio_player)
            output = output.astype(np.float32) / len(audio_players)
            out.write(output)

            #-----------------------------------------------------------------------------------------------------------
            # Render score
            #-----------------------------------------------------------------------------------------------------------
            if self.render_score:
                position_int = int(increments_frac * 8)
                self.renderer.clear()
                sys.stdout.write("\u001b[1A\u001b[1000D")
                self.print_time_elapsed()
                self.renderer.draw_bar(int(self.renderer.width * self.channel_offsets[0] / len(AUDIO_DATA)), position_int, 8)
                self.renderer.draw_bar(int(self.renderer.width * self.channel_offsets[1] / len(AUDIO_DATA)), position_int, 8)
                self.renderer.draw_bar(int(self.renderer.width * self.channel_offsets[2] / len(AUDIO_DATA)), position_int, 8)
                self.renderer.draw_bar(int(self.renderer.width * self.channel_offsets[3] / len(AUDIO_DATA)), position_int, 8)
                self.renderer.draw_bar(int(self.renderer.width * self.channel_offsets[4] / len(AUDIO_DATA)), position_int, 8)
                self.renderer.draw_bar(int(self.renderer.width * self.channel_offsets[5] / len(AUDIO_DATA)), position_int, 8)

    def print_time_elapsed(self):
        #---------------------------------------------------------------------------------------------------------------
        # Calculate the number of units elapsed since the beginning of the piece, for terminal display.
        #---------------------------------------------------------------------------------------------------------------
        timedelta = get_total_time_elapsed()
        days_per_year = 365.2425
        years = timedelta.days // days_per_year
        days = timedelta.days - (years * days_per_year)
        hours = timedelta.seconds // 3600
        minutes = (timedelta.seconds - hours * 3600) // 60
        seconds = timedelta.seconds % 60
        print("Longplayer has been running for %d years, %d days, %d hours, %d minutes, %d seconds." % (years, days, hours, minutes, seconds))

