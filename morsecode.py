import re
import sys
import time
import numpy as np
from pyaudio import PyAudio, paFloat32
from collections import deque


class MorseCodeTranslator:
    SPACE_SYMBOL = ' '
    SYMBOLS = {
        'A': '.-',
        'B': '-...',
        'C': '-.-.',
        'D': '-..',
        'E': '.',
        'F': '..-.',
        'G': '--.',
        'H': '....',
        'I': '..',
        'J': '.---',
        'K': '-.-',
        'L': '.-..',
        'M': '--',
        'N': '-.',
        'O': '---',
        'P': '.--.',
        'Q': '--.-',
        'R': '.-.',
        'S': '...',
        'T': '-',
        'U': '..-',
        'V': '...-',
        'W': '.--',
        'X': '-..-',
        'Y': '-.--',
        'Z': '--..',
        '1': '.----',
        '2': '..---',
        '3': '...--',
        '4': '....-',
        '5': '.....',
        '6': '-....',
        '7': '--...',
        '8': '---..',
        '9': '----.',
        '0': '-----',
        '.': '.-.-.-',
        ',': '--..--',
        '?': '..--..',
        # ' ': '/'
        ' ': SPACE_SYMBOL
    }

    def __init__(self, code=None, text=None):
        self.code = code
        self.text = text

    def morse_to_char(self, symbol):
        if symbol in self.SYMBOLS.values():
            symbol_vals = list(self.SYMBOLS.values())
            symbol_keys = list(self.SYMBOLS.keys())
            return symbol_keys[symbol_vals.index(symbol)]
        return

    def clean_morse(self):
        spaces = re.findall(r'\s{2,}', self.code)
        arr = re.split(r'(\s+)', self.code)
        for i in range(len(arr)):
            if arr[i] == ' ':
                arr[i] = ''
            elif arr[i] in spaces:
                arr[i] = self.SPACE_SYMBOL
        return arr

    def morse_to_text(self):
        if not self.code:
            return
        arr = self.clean_morse()
        # arr = self.code.split(' ')  # for use if '/' is used as symbol for ' '.
        msg = ''
        for s in arr:
            char = self.morse_to_char(s)
            if not char:
                continue
            msg += char
        return msg

    def char_to_morse(self, char):
        return self.SYMBOLS[char.upper()]

    def text_to_morse(self):
        if not self.text:
            return
        coded_msg = []
        for char in self.text:
            coded_msg.append(self.char_to_morse(char))
        return ' '.join(coded_msg)

    def text_to_morse_audio(self, **kwargs):
        sample, sample_rate = self.create_sample(self.text_to_morse(), **kwargs)   
        self._play_morse_code_audio(sample, sample_rate)

    @staticmethod
    def _create_tone(duration, tone_freq, sample_rate):
        sample = (np.sin(2*np.pi*np.arange(sample_rate*duration)
                          * tone_freq/sample_rate)).astype(np.float32)
        return sample

    @staticmethod
    def _create_silence(duration, sample_rate):
        sample = (np.zeros(int(sample_rate*duration))).astype(np.float32)
        return sample

    def create_sample(self, morse_code, speed=20, farnsworth_speed=20, tone_freq=440.0, sample_rate=44100):
        time_unit = 60/(speed*25)
        f_time_unit = 60/(farnsworth_speed*25)
        char_time_units = {
            '.': (time_unit, 1), '-': (time_unit*3, 1), ' ': (f_time_unit, 0), self.SPACE_SYMBOL: (f_time_unit*5, 0)}
        sample = np.array([]).astype(np.float32)
        for char in code:
            duration, sound = char_time_units[char]
            if sound:
                sample = np.append(sample, self._create_tone(
                    duration, tone_freq, sample_rate))
            else:
                sample = np.append(
                    sample, self._create_silence(duration, sample_rate))
            sample = np.append(sample, self._create_silence(f_time_unit, sample_rate))
        return sample, sample_rate

    @staticmethod
    def _play_morse_code_audio(samples, sample_rate):
        pa = PyAudio()
        stream = pa.open(rate=sample_rate, channels=2,
                         format=paFloat32, output=True)
        start = time.time()
        stream.write(samples.tobytes())
        stream.stop_stream()
        stop = time.time()
        stream.close()
        pa.terminate()
        print("Played in {} seconds.".format(round(stop - start, 2)))

    def read_morse_audio(self, sample_rate=44100):
        # TODO:
        # Wait for first tone
        # Read characters
        # Determine length tones (short => '.', long => '-')
        # Determine length of silence for space
        # Determine wpm speed
        # ? Optional: ML to get better accuracy in determining gap lengths between characters and start of new word.
        chunk = 1024
        pa = PyAudio()
        stream = pa.open(rate=sample_rate, channels=2, 
                         format=paFloat32, input=True)
        stream.read(num_frames=chunk)
        pass

    def _get_first_tone(self, stream):
        threshold = 2500
        deque()
        pass

    def _read_audio_stream(self, stream):
        pass

    def _determine_character(self):
        pass

    def _determine_space(self):
        pass

    def _determine_speed(self):
        pass

    def _print_single_char(self, char):
        sys.stdout.write(char)
        sys.stdout.flush()


if __name__ == "__main__":
    m = MorseCodeTranslator(text="Hello there")
    code = m.text_to_morse()
    print(code)
    m.text_to_morse_audio(tone_freq=440.0)
    m = MorseCodeTranslator(code=code)
    print(m.morse_to_text())
