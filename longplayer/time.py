import datetime
from .constants import INCREMENT_INTERVAL, CHANNEL_RATES, CHANNEL_INCREMENT_SAMPLES, SAMPLE_RATE, AUDIO_DURATION


def get_total_time_elapsed() -> datetime.timedelta:
    """
    Calculate the total running time of Longplayer to date.

    This is derived by converting the current time into UTC, and then calculating the
    time elapsed since 2000-01-01 00:00:00.

    Returns:
        datetime.timedelta: The time delta.
    """
    start_time = datetime.datetime.strptime("2000-01-01T00:00:00+1200", "%Y-%m-%dT%H:%M:%S%z")
    current_time = datetime.datetime.now(datetime.timezone.utc)
    return current_time - start_time


def get_total_increments_elapsed() -> float:
    """
    Calculate the total number of two-minute increments elapsed to date.

    Returns:
        float: The total number of increments elapsed.
    """
    seconds_elapsed = get_total_time_elapsed().total_seconds()
    increments_elapsed = seconds_elapsed / INCREMENT_INTERVAL
    return increments_elapsed


def get_offset_for_channel(increments, channel: int = 0) -> tuple[float, float]:
    """
    For a given channel, calculate the position of the playback head given a specific number of elapsed increments.
    Each segment moves forward every 120 seconds, at a rate specific to each channel.
    At this point, the playback head resets to the start of the segment.
    Over the course of the 120-second segment, the playback head sweeps forward at the channel's playback rate.

    Args:
        increments (float): The total number of increments elapsed since 2000-01-01 00:00:00.
        channel (int): Index of the channel number.

    Returns:
        (offset (float), position(float)): Tuple containing the offset of the current segment and the position within
                                           the segment, both in seconds.
    """
    channel_rate = CHANNEL_RATES[channel]
    channel_increment = CHANNEL_INCREMENT_SAMPLES[channel]
    increments_int = int(increments)
    increments_frac = increments - increments_int
    segment_offset = increments_int * channel_increment / SAMPLE_RATE
    segment_offset = segment_offset % AUDIO_DURATION
    segment_position = increments_frac * channel_rate * INCREMENT_INTERVAL
    return segment_offset, segment_position
