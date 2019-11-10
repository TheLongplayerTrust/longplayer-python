from .time import get_total_time_elapsed, get_total_increments_elapsed, get_offset_for_channel
from .audio import AudioPlayerVarispeed
from .constants import AUDIO_DATA, CHANNEL_RATES, SAMPLE_RATE, BLOCK_SIZE

import logging
import sounddevice
import numpy as np

logger = logging.getLogger(__name__)


class Longplayer(object):
    def start(self):
        print("Longplayer, by Jem Finer.")

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

        audio_players = []
        for channel_index, rate in enumerate(CHANNEL_RATES):
            audio_players.append(AudioPlayerVarispeed(AUDIO_DATA, 0, rate))

        out = sounddevice.OutputStream(channels=1, blocksize=BLOCK_SIZE)
        out.start()

        last_increments_int = None

        while True:
            increments = get_total_increments_elapsed()
            increments_int = int(increments)
            if last_increments_int is None or increments_int > last_increments_int:
                logger.info("-------------------------------------------------------------------------------------")
                logger.info("Begun new increment, currently elapsed: %d" % increments_int)
                for channel_index, rate in enumerate(CHANNEL_RATES):
                    offset, position = get_offset_for_channel(increments, channel_index)
                    logger.debug(" - channel %d: offset %.3fs, position %.3fs" % (channel_index, offset, position))

                    offset_samples = offset * SAMPLE_RATE
                    position_samples = position * SAMPLE_RATE
                    audio_players[channel_index].set_phase(offset_samples + position_samples)
            last_increments_int = increments_int
            output = np.zeros(BLOCK_SIZE)
            for player in audio_players:
                channel_samples = player.get_samples(BLOCK_SIZE)
                output = output + channel_samples
            output = output.astype(np.float32) / len(audio_players)
            out.write(output)
