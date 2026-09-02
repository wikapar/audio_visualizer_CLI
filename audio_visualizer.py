import argparse
import curses
import os
from typing import Tuple
import soundfile as sf
import numpy as np
from amplitude_display import LinearScaling, LogScaling
from sample_processing import SampleProcessor

def read_file(filename: str) -> Tuple[np.ndarray, int]:
    """Reads the entire audio file"""
    if os.path.exists(filename):
        data, samplerate = sf.read(filename)
        return data, samplerate
    
    else:
        raise FileNotFoundError

def read_to_soundfile_obj(filename: str) -> sf.SoundFile:
    """Reads an audio file to a SoundFile object"""
    if os.path.exists(filename):
        file = sf.SoundFile(filename)
        return file
    
    else:
        raise FileNotFoundError

def one_char(arg: str) -> str:
    """Validator for parsng the symbol argument. Checks if the string is one character long."""
    if len(arg) != 1:
        raise argparse.ArgumentTypeError("Symbol must be exactly one character")
    return arg

def scale_strategy_factory(name: str):
    """Simple factory method returning ScalingStrategy object based on a name"""
    strategies = {
    "linear": LinearScaling,
    "log": LogScaling,
}
    return strategies[name]()

def main():
    parser = argparse.ArgumentParser(
                    prog='music_visualiser',
                    description='Visualises and plays music from a given audio file',
                    epilog='Pass the filename when starting the program')
    parser.add_argument('filename', type=str)
    parser.add_argument('-f', '--frame-rate', type=int, help="framerate of the display")
    parser.add_argument('-s','--symbol',type=one_char, help="symbol that will be used for display")
    parser.add_argument('-sc', '--scale', choices=['linear', 'log'], 
                        help="choose the scale the display will use", default='log')
    args = parser.parse_args()
    try:
        file = read_to_soundfile_obj(args.filename)
    except FileNotFoundError:
        print("The specified file doesn't exist")
        return
    except sf.LibsndfileError as e:
        print(e)
        return

    if not (framerate := args.frame_rate):
        framerate = 30

    if not (symbol := args.symbol):
        symbol = '■'

    scale = scale_strategy_factory(args.scale)

    sp = SampleProcessor(file, framerate, symbol, scale)
    curses.wrapper(sp.process_samples)

if __name__ == "__main__":
    main()