import sounddevice as sd
import soundfile as sf
import numpy as np
import math
import amplitude_helper
from amplitude_display import AmplitudeDisplay
from amplitude_display import LogScaling
from sounddevice import CallbackFlags
from queue import Queue
import queue as q
from threading import Thread, Event
from typing import Any

class DisplayDesyncError(Exception):
    """To be thrown when the producer fails to produce amplitude values on time -
    audio and display get desynced."""
    def __init__(self):
        message = "Display got desynced from the audio. No amplitude value in the queue."
        super().__init__(message)

class SampleProcessor:
    def __init__(self, file: sf.SoundFile, framerate: int):
        self._file: sf.SoundFile = file
        self._framerate: int = framerate
        self._samplerate: int = file.samplerate
        self._step = math.ceil(self._samplerate / self._framerate) #number of audio frames to be processed per visual frame
        self._stream: sd.OutputStream = sd.OutputStream(samplerate=self._samplerate,
        blocksize=self._step, latency='low', callback=self.callback, channels=2)
        self._audio_queue: Queue = Queue() #queue for playback
        self._amplitude_queue: Queue = Queue() #queue for drawing
        self._error_queue: Queue = Queue() #queue for passing errors from different threads
        self._error_event: Event = Event()
        self._consumed_blocks: int = 0
        self._last_drawn_block: int = 0

    @property
    def framerate(self):
        return self._framerate

    @property
    def step(self):
        return self._step

    @property
    def samplerate(self):
        return self._samplerate

    def _process_audio(self, audio_frames: np.ndarray, step: int) -> np.ndarray:
        """Calculates the amplitude spectrum."""
        left_channel = audio_frames[:, 0]
        return amplitude_helper.amplitude_spectrum(left_channel, step)

    CData = Any #ctypes doesnt expose the type CData
    def callback(self, outdata: np.ndarray, frames: int,
         time: CData, status: CallbackFlags) -> None:
        """Callback passed to the output stream.
        Returns sd.CallbackAbort in case of underflow or when no audio data is in the audio queue.
        Returns sd.CallbackStop when playback is finished."""
        assert frames == self._step
        if status.output_underflow:
            print('Detected stream underflow')
            self._error_queue.put(sd.CallbackAbort())
            self._error_event.set()
            raise sd.CallbackAbort()
        assert not status

        try:
            next_audio = self._audio_queue.get_nowait()
        except q.Empty as e:
            print('No new audio data to play')
            self._error_queue.put(sd.CallbackAbort())
            self._error_event.set()
            raise sd.CallbackAbort()

        if next_audio is None:
            print('audio playback finished')
            self._consumed_blocks += 1
            raise sd.CallbackStop

        #case for the last block of data - padding with 0
        len_difference = len(outdata) - len(next_audio)
        if len_difference > 0:
            outdata[:len(next_audio)] = next_audio
            outdata[len(next_audio):] = b'\x00' * len_difference
            self._consumed_blocks += 1
        else:
            self._consumed_blocks += 1
            outdata[:] = next_audio

    def produce_blocks(self):
        """Producer for the audio queue and the amplitude queue.
        Pushes 'EOF' string into queues when all data is read from the file."""
        with self._file as file:
            audio_frames = np.zeros(self._step)

            while len(audio_frames) != 0:
                try:
                    audio_frames = file.read(frames=self._step)
                    self._audio_queue.put_nowait(audio_frames)
                    amplitude = self._process_audio(audio_frames, self._step)
                    self._amplitude_queue.put_nowait(amplitude)

                except Exception as e:
                    print("Producer error")
                    print(e)
                    self._error_event.set()
                    break

            self._audio_queue.put_nowait(None)
            self._amplitude_queue.put_nowait(None)
            print("producer finished")



    def draw_blocks(self, amp_display, stdscr) -> None:
        """Synchronises drawing, by waiting for the callback to consume blocks.
        Consumer for amplitude queue. Uses AmplitudeDisplay for drawing.
        Acts as the main loop, by raising errors from other threads"""
        while True:
            if self._error_event.is_set():
                raise self._error_queue.get()

            if self._last_drawn_block < self._consumed_blocks:
                self._last_drawn_block += 1
                try:
                    amplitude = self._amplitude_queue.get(timeout=0.5)
                    if amplitude is None:
                        print("Drawing finished")
                        break
                except q.Empty as e:
                    print('Drawing queue is empty')
                    self._error_queue.put(DisplayDesyncError())
                    self._error_event.set()
                    continue

                amp_display.display_amplitude(amplitude)
                stdscr.clear()

    def process_samples(self, stdscr):
        """
        Coordinates processing of the samples.
        Needs to be called wrapped with curses.wrapper to provide stdscr.
        """
        amp_display = AmplitudeDisplay(stdscr, LogScaling(), self._samplerate)
        producer_thread = Thread(target=self.produce_blocks)
        producer_thread.start()
        self._stream.start()
        try:
            self.draw_blocks(amp_display, stdscr)
        finally:
            self._file.close()
            producer_thread.join()
            self._stream.stop()
            self._stream.close()

