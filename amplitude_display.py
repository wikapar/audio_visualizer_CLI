import curses
from typing import List
import numpy as np
import amplitude_helper
from abc import ABC, abstractmethod

BLACK_SQUARE = 254
#minimum and maximum frequency that will be displayed in hokertz
MAX_FREQUENCY = 10000
MIN_FREQUENCY = 40

class ScalingStrategy(ABC):
    @abstractmethod
    def get_next_bin(self, low_edge: float, high_edge: float, increment: float) -> tuple[float, float]:
        pass

    @abstractmethod
    def get_increment(self, num_of_bins: int, max_frequency: float, min_frequency: float)-> float:
        pass
"""
    @abstractmethod
    def get_bin_from_value(self, num_of_bins: int, increment: float, min_frequency: float) -> float:
        pass
"""
class LogScaling(ScalingStrategy):
    def get_next_bin(self, high_edge: float, increment: float) -> tuple[float, float]:
        return high_edge, high_edge*increment

    def get_increment(self, num_of_bins: int, max_frequency: float, min_frequency: float)-> float:
        return (max_frequency / min_frequency)**(1/(num_of_bins))

class LinearScaling(ScalingStrategy):
    def get_next_bin(self, high_edge: float, increment: float) -> tuple[float, float]:
        return high_edge, high_edge + increment

    def get_increment(self, num_of_bins: int, max_frequency: float, min_frequency: float)-> float:
        return (max_frequency - min_frequency) / num_of_bins

class AmplitudeDisplay:
    def __init__(self, stdscr: curses.window, scaling_strategy: ScalingStrategy, samplerate: int):
        self._scaling_strategy = scaling_strategy #determines how the bins are spaced
        self._stdscr = stdscr
        self._samplerate = samplerate

    @property
    def stdscr(self)->curses.window:
        return self._stdscr

    def plot_values(self, x_values: np.ndarray, y_values: np.ndarray):
        """Plots x and y values onto stdscr.
        x_values and y_values should be the same length.
        The corresponding x and y values should have corresponding indices."""
        for x_val, y_val in zip(x_values, y_values):
            print(f"Max y index: {curses.LINES - 1}")
            print(int(y_val) - 1)
            for y in range(curses.LINES - 1, int(y_val) - 1, -1):
                print("????")
                self._stdscr.addch(y=y, x=x_val, ch=BLACK_SQUARE)
        self._stdscr.refresh()

    def display_amplitude(self, amplitude: np.ndarray):
        num_of_bins = curses.COLS
        #index from aggregated_values corresponds to x
        agregated_values = self.agregate_amplitude_values(amplitude, num_of_bins)
        values_to_draw = self.scale_amplitude_values_to_screen(agregated_values, curses.LINES)
        self.plot_values(np.arange(len(values_to_draw)), values_to_draw)

    def scale_amplitude_values_to_screen(self, amplitude: np.array, max_y: int) -> np.ndarray:
        """Scales amplitude values (range 0 - 1/2 for real signals) to screen values (range max_y - 0)"""
        values_to_draw = np.rint(amplitude * max_y * 2)
        values_to_draw = np.abs(values_to_draw - max_y) #inverting values since 0,0 is the top left of the screen
        return values_to_draw

    def agregate_amplitude_values(self, amplitude: np.ndarray, num_of_bins: int) -> np.ndarray:
        """Aggregates FFT amplitude values into spaced bins.
        The agregated frequency values span from MIN_FREQUENCY to MAX_FREQUENCY.
        Values inside bins are combined using root mean square."""
        increment = self._scaling_strategy.get_increment(num_of_bins, MAX_FREQUENCY, MIN_FREQUENCY)
        low_edge, high_edge = self._scaling_strategy.get_next_bin(MIN_FREQUENCY, increment)
        bin_values = []
        rms_values = []
        for bin_index, amp_value in enumerate(amplitude):
            if len(rms_values) >= curses.COLS:
                break
            frequency = amplitude_helper.FFT_bin_to_hertz(bin_index, self._samplerate, len(amplitude))
            if frequency > low_edge and frequency <= high_edge:
                bin_values.append(amp_value)
            elif frequency > high_edge:
                rms_values.append(AmplitudeDisplay.rms(np.array(bin_values)))
                bin_values = []
                while frequency > high_edge and high_edge <= MAX_FREQUENCY:
                    low_edge, high_edge = self._scaling_strategy.get_next_bin(high_edge, increment)
                    rms_values.append(AmplitudeDisplay.rms(np.array(bin_values)))
                    bin_values = []
                if high_edge <= MAX_FREQUENCY:
                    bin_values.append(amp_value)
        return np.array(rms_values)

    @staticmethod
    def rms(array:np.ndarray) -> float:
        if not len(array):
            return 0
        return np.sqrt(np.mean(np.pow(array, 2)))
