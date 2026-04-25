import curses
from typing import List
import numpy as np
import amplitude_helper

BLACK_SQUARE = 254
#minimum and maximum frequency that will be displayed in hokertz
MAX_FREQUENCY = 10000
MIN_FREQUENCY = 40

def plot_values(stdscr: curses.window, x_values: np.ndarray, y_values: np.ndarray):
    for x_val, y_val in zip(x_values, y_values):
        print(y_val)
        print(type(y_val - 1))
        for y in range(curses.LINES - 1, int(y_val) - 1, -1):
            stdscr.addch(y=y, x=x_val, ch=BLACK_SQUARE)
    stdscr.refresh()

def display_amplitude(stdscr: curses.window, amplitude: np.ndarray, samplerate: int):
    num_of_bins = curses.COLS
    #index from aggregated_values corresponds to x
    agregated_values = agregate_amplitude_values(amplitude, num_of_bins, samplerate)
    values_to_draw = scale_amplitude_values_to_screen(agregated_values, curses.LINES)
    plot_values(stdscr, np.arange(len(values_to_draw)), values_to_draw)

def scale_amplitude_values_to_screen(amplitude: np.array, max_y: int) -> np.ndarray:
    """Scales amplitude values (range 0 - 1/2 for real signals) to screen values (range max_y - 0)"""
    values_to_draw = np.rint(amplitude * max_y * 2)
    values_to_draw = np.abs(values_to_draw - max_y) #inverting values since 0,0 is the top left of the screen
    return values_to_draw

def agregate_amplitude_values(amplitude: np.ndarray, num_of_bins: int, samplerate: int) -> np.ndarray:
    """Aggregates FFT amplitude values into logarithmically spaced bins.
    The agregated frequency values span from MIN_FREQUENCY to MAX_FREQUENCY.
    Values inside bins are combined using root mean square."""
    multiplier = get_bin_multiplier(num_of_bins)
    low_edge = MIN_FREQUENCY
    high_edge = low_edge * multiplier
    bin_values = []
    rms_values = []
    for bin_index, amp_value in enumerate(amplitude):
        if len(rms_values) >= curses.COLS:
            break
        frequency = amplitude_helper.FFT_bin_to_hertz(bin_index, samplerate, len(amplitude))
        if frequency > low_edge and frequency <= high_edge:
            bin_values.append(amp_value)
        elif frequency > high_edge:
            rms_values.append(rms(np.array(bin_values)))
            bin_values = []
            while frequency > high_edge and high_edge <= MAX_FREQUENCY:
                low_edge = high_edge
                high_edge = low_edge * multiplier
                rms_values.append(rms(np.array(bin_values)))
                bin_values = []
            if high_edge <= MAX_FREQUENCY:
                bin_values.append(amp_value)
    return np.array(rms_values)

def get_bin_multiplier(num_of_bins: int) -> float:
    """Return the multiplier needed to divide frequencies from min to max logarithmically"""
    return (MAX_FREQUENCY / MIN_FREQUENCY)**(1/(num_of_bins))

def rms(array:np.ndarray) -> float:
    if not len(array):
        return 0
    return np.sqrt(np.mean(np.pow(array, 2)))
