import sounddevice as sd
import soundfile as sf
import display
import numpy as np
import math
import amplitude_helper

class SampleProcessor:
    def __init__(self, file: sf.SoundFile, framerate: int):
        self._file = file
        self._framerate = framerate
        self._samplerate = file.samplerate

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
        with self._file as file:
            audio_frames = file.read(step)
            amplitude = self._process_audio(audio_frames, step)
            display.display_amplitude(stdscr, amplitude, self._samplerate)
