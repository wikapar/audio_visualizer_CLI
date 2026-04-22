import sounddevice as sd
import soundfile as sf
import display
import numpy as np

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

    @staticmethod
    def amplitude_spectrum(samples: np.ndarray, num_of_samples: int) -> np.ndarray:
        """Returns scaled amplitude spectrum of the signal"""
        fft = np.fft.fft(samples)
        return np.abs(fft / num_of_samples)

    def _process_audio(self, audio_frames: np.ndarray, step: int) -> np.ndarray:
        """Plays the audio and calculates amplitude spectrum"""
        sd.play(audio_frames, self._samplerate)
        left_channel = audio_frames[0]
        return SampleProcessor.amplitude_spectrum(left_channel, step)

    def process_samples(self, stdscr):
        """
        Coordinates processing of the samples.
        Needs to be called wrapped with curses.wrapper to provide stdscr.
        """
        step = self.file.samplerate / self.framerate #number of audio frames to be processed per visual frame
        with self.file as file:
            audio_frames = file.read(step)
            self._process_audio(audio_frames, step)
