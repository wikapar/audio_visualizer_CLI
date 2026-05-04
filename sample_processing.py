import sounddevice as sd
import soundfile as sf
import numpy as np
import math
import amplitude_helper
from amplitude_display import AmplitudeDisplay
from amplitude_display import LogScaling

class SampleProcessor:
    def __init__(self, file: sf.SoundFile, framerate: int):
        self._file: sf.SoundFile = file
        self._framerate: int = framerate
        self._samplerate: int = file.samplerate

    @property
    def framerate(self):
        return self._framerate

    @property
    def samplerate(self):
        return self._samplerate

    def _process_audio(self, audio_frames: np.ndarray, step: int) -> np.ndarray:
        """Plays the audio and calculates amplitude spectrum"""
        sd.play(audio_frames, self._samplerate)
        left_channel = audio_frames[:, 0]
        return amplitude_helper.amplitude_spectrum(left_channel, step)

    def process_samples(self, stdscr):
        """
        Coordinates processing of the samples.
        Needs to be called wrapped with curses.wrapper to provide stdscr.
        """
        step = math.ceil(self._samplerate / self._framerate) #number of audio frames to be processed per visual frame
        amp_display = AmplitudeDisplay(stdscr, LogScaling(), self._samplerate)
        with self._file as file:
            audio_frames = np.zeros(step)
            while len(audio_frames) != 0:
                audio_frames = file.read(frames=step, fill_value=0)
                amplitude = self._process_audio(audio_frames, step)
                amp_display.display_amplitude(amplitude)
                sd.wait()
