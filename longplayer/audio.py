import math

from .constants import SAMPLE_RATE, AUDIO_FADE_TIME, AUDIO_DURATION_SAMPLES

class Resampler:
    def __init__(self):
        """
        Resampler with linear interpolation.
        """
        self.phase = 0.0
        self.buffer = []

    def process(self, samples: list, ratio: float):
        """
        Resample a block of samples.
        
        Args:
            audio_data (list): 1D array of floating-point samples
            ratio (float): Resampling ratio
        """
        buffer = []
        samples = self.buffer + list(samples)
        while self.phase < len(samples) - 1:
            phase_int = int(self.phase)
            phase_frac = self.phase - phase_int
            s0 = samples[phase_int]
            s1 = samples[phase_int + 1]
            sample = (s1 * phase_frac) + (s0 * (1 - phase_frac))
            buffer.append(sample)
            self.phase += ratio
        self.phase -= len(samples) - 1
        self.buffer = [samples[-1]]
        return buffer

class AudioPlayer:
    def __init__(self, audio_data, initial_phase, rate):
        """
        Variable speed sample player. Resamples input audio in real-time
        with linear interpolation.

        Args:
            audio_data (list): 1D array of floating-point samples
            initial_phase (int): Initial phase in samples
            rate (float): Playback rate
        """
        self.audio_data = audio_data
        self._phase = initial_phase
        self.rate = rate
        self.buffer = [0]
        self.resampler = Resampler()

        #--------------------------------------------------------------------------------
        # Amplitude target/steps, used for volume fades when starting/ending playback.
        #--------------------------------------------------------------------------------
        self.amplitude_level = 0
        self.amplitude_target = 0
        self.amplitude_steps_remaining = 0
        self.amplitude_step = 0
        self.is_finished = False

        self.fade_up()

    def get_phase(self):
        return self._phase

    def set_phase(self, phase):
        """
        Sets the position of the playback within the audio data to a new location.

        Args:
            phase (float): The new phase within the audio, specified in samples

        Raises:
            ValueError: If the phase is outside of the permitted playback bounds.
        """
        if phase < 0:
            raise ValueError("Phase is outside audio bounds")
        if phase > AUDIO_DURATION_SAMPLES:
            phase -= AUDIO_DURATION_SAMPLES
        self._phase = int(phase)
    
    phase = property(get_phase, set_phase)

    def fade_up(self, duration: float = AUDIO_FADE_TIME):
        self.fade_to(target=1.0,
                     duration=duration)

    def fade_down(self, duration: float = AUDIO_FADE_TIME):
        self.fade_to(target=0.0,
                     duration=duration)

    def fade_to(self, target: float, duration: float):
        self.amplitude_target = target
        self.amplitude_steps_remaining = duration * SAMPLE_RATE
        self.amplitude_step = (self.amplitude_target - self.amplitude_level) / self.amplitude_steps_remaining

    def get_samples(self, sample_count) -> list:
        """
        Returns `sample_count` samples, resampled to the new rate.

        Returns:
              list: A 1-dimensional array of exactly `sample_count` floating-point samples.
        """

        #--------------------------------------------------------------------------------
        # Generate output samples.
        # Because resampling may generate too few samples for the required output block
        # size, maintain an internal buffer of samples and refill it as needed.
        #--------------------------------------------------------------------------------
        while len(self.buffer) < sample_count:
            input_block = self.audio_data[self.phase:self.phase + sample_count]
            resampled_block = self.resampler.process(input_block, self.rate)
            self.buffer = self.buffer + resampled_block
            self.phase = self.phase + sample_count

        rv = self.buffer[:sample_count]
        self.buffer = self.buffer[sample_count:]

        #--------------------------------------------------------------------------------
        # Generate amplitude envelope, and perform linear fading between amplitudes.
        #--------------------------------------------------------------------------------
        amp_envelope = [self.amplitude_level] * sample_count
        for n in range(sample_count):
            if self.amplitude_steps_remaining > 0:
                self.amplitude_level += self.amplitude_step
                self.amplitude_steps_remaining -= 1
                if self.amplitude_steps_remaining == 0:
                    self.amplitude_level = self.amplitude_target
                    if self.amplitude_level == 0.0:
                        self.is_finished = True
            amp_envelope[n] = math.sqrt(self.amplitude_level)

        for n in range(sample_count):
            rv[n] *= amp_envelope[n]

        return rv
