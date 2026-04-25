import numpy as np

def amplitude_spectrum(samples: np.ndarray, num_of_samples: int) -> np.ndarray:
        """Returns scaled amplitude spectrum of the signal"""
        fft = np.fft.fft(samples)
        return np.abs(fft / num_of_samples)

def FFT_bin_to_hertz(bin_index: int, samplerate: int, num_of_samples: int):
        """Returns the value of a frequency in Hz that corresponds to a given bin in FFT"""
        return bin_index * (samplerate / num_of_samples)