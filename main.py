import argparse
import os
from typing import Tuple
import soundfile as sf
import numpy as np
import sounddevice as sd

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

def amplitude_spectrum(samples: np.ndarray, num_of_samples: int) -> np.ndarray:
    """Returns scaled amplitude spectrum of the signal"""
    fft = np.fft.fft(samples)
    return np.abs(fft / num_of_samples)

def process_samples(file: sf.SoundFile, framerate: int):
    step = file.samplerate / framerate #number of audio frames to be processed per visual frame
    with file:
        audio_frames = file.read(step)
        sd.play(audio_frames, file.samplerate)
        left_channel = audio_frames[0]
        amplitude = amplitude_spectrum(left_channel)

def main():
    parser = argparse.ArgumentParser(
                    prog='music_visualiser',
                    description='Visualises and plays music from a given audio file',
                    epilog='Pass the filename when starting the program')
    parser.add_argument('filename', type=str)
    parser.add_argument('-f', '--frame-rate', type=int)
    args = parser.parse_args()
    try:
        file = read_to_soundfile_obj(args.filename)
    except FileNotFoundError:
        print("The specified file doesn't exist")
    except sf.LibsndfileError as e:
        print(e)

    process_samples(file)






if __name__ == "__main__":
    main()