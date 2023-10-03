import samplerate
import numpy as np

from .constants import SAMPLE_RATE, AUDIO_FADE_TIME


class AudioPlayerVarispeed(object):
    def __init__(self, audio_data, initial_phase, rate):
        """
        Variable speed sample player. Resamples input audio in real-time
        using libsamplerate's high-quality sinc resampler.

        Args:
            audio_data (np.ndarray): 1D array of floating-point samples
            initial_phase (int): Initial phase in samples
            rate (float): Playback rate
        """
        self.audio_data = audio_data
        self.phase = int(initial_phase)
        self.rate = rate
        self.buffer = np.ndarray((0,))
        self.resampler = samplerate.Resampler('sinc_fastest', channels=1)

        #---------------------------------------------------------------------------------------------------------------
        # Amplitude target/steps, used for volume fades when starting/ending playback.
        #---------------------------------------------------------------------------------------------------------------
        self.amplitude_level = 0
        self.amplitude_target = 0
        self.amplitude_steps_remaining = 0
        self.amplitude_step = 0
        self.fade_up()

    def set_phase(self, phase):
        """
        Sets the position of the playback within the audio data to a new location.

        Args:
            phase (float): The new phase within the audio, specified in samples

        Raises:
            ValueError: If the phase is outside of the permitted playback bounds.
        """
        if phase < 0 or phase >= len(self.audio_data):
            raise ValueError("Phase is outside audio bounds")
        self.phase = int(phase)

    def fade_up(self):
        self.fade_to(1.0)

    def fade_down(self):
        self.fade_to(0.0)

    def fade_to(self, target):
        self.amplitude_target = target
        self.amplitude_steps_remaining = AUDIO_FADE_TIME * SAMPLE_RATE
        self.amplitude_step = (self.amplitude_target - self.amplitude_level) / self.amplitude_steps_remaining

    def get_samples(self, sample_count):
        """
        Returns `sample_count` samples, resampled to the new rate.

        Returns:
              numpy.ndarray: A 1-dimensional numpy array of exactly `sample_count` floating-point samples.
        """

        #---------------------------------------------------------------------------------------------------------------
        # Generate output samples.
        # Because resampling may generate too few samples for the required output block size, maintain an internal
        # buffer of samples and refill it as needed.
        #---------------------------------------------------------------------------------------------------------------
        while len(self.buffer) < sample_count:
            input_block = self.audio_data[self.phase:self.phase + sample_count]
            resampled_block = self.resampler.process(input_block, 1 / self.rate, end_of_input=False)
            self.buffer = np.concatenate((self.buffer, resampled_block))
            self.phase += sample_count

        rv = self.buffer[:sample_count]
        self.buffer = self.buffer[sample_count:]

        #---------------------------------------------------------------------------------------------------------------
        # Generate amplitude envelope, and perform linear fading between amplitudes.
        #---------------------------------------------------------------------------------------------------------------
        amp_envelope = np.full(sample_count, self.amplitude_level)
        if self.amplitude_steps_remaining > 0:
            for n in range(sample_count):
                if self.amplitude_steps_remaining > 0:
                    self.amplitude_level += self.amplitude_step
                    self.amplitude_steps_remaining -= 1
                amp_envelope[n] = self.amplitude_level
        else:
            self.amplitude_level = self.amplitude_target
        rv *= amp_envelope

        return rv
