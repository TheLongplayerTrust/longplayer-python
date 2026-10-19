import datetime
from .constants import INCREMENT_INTERVAL, LAYER_RATES, LAYER_INCREMENTS_SAMPLES, SAMPLE_RATE, AUDIO_DURATION


def get_total_time_elapsed() -> datetime.timedelta:
    """
    Calculate the total running time of Longplayer to date.

    This is derived by converting the current time into UTC, and then calculating the
    time elapsed since 2000-01-01 00:00:00 (at the international date line).

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


def get_position_for_layer(increments, layer: int = 0) -> tuple[float, float]:
    """
    For a given layer, calculate the position of the playback head given a specific number of elapsed increments.
    Each section moves forward every 120 seconds, at a rate specific to each layer.
    At this point, the playback head resets to the start of the section.
    Over the course of the 120-second section, the playback head sweeps forward at the layer's playback rate.

    Args:
        increments (float): The total number of increments elapsed since 2000-01-01 00:00:00.
        layer (int): Index of the layer number.

    Returns:
        (section_start_position (float), section_playhead_position(float)):
            Tuple containing the start point of the current section and the position within
            the section, both in seconds.
    """
    layer_rate = LAYER_RATES[layer]
    layer_increment = LAYER_INCREMENTS_SAMPLES[layer]
    increments_int = int(increments)
    increments_frac = increments - increments_int
    section_start_position = increments_int * layer_increment / SAMPLE_RATE
    
    #--------------------------------------------------------------------------------
    # Be careful here to modulo by AUDIO_DURATION (1220 seconds), rather than the
    # actual length of the audio sample, because the sample contains additional
    # audio at the end to make it easier to loop.
    #--------------------------------------------------------------------------------
    section_start_position = section_start_position % AUDIO_DURATION

    section_playhead_position = increments_frac * layer_rate * INCREMENT_INTERVAL
    return section_start_position, section_playhead_position
