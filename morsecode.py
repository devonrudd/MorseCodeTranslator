import re
import sys
import time
import numpy as np
import socket
from pyaudio import PyAudio, paFloat32, paContinue
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

    def text_to_morse_audio(self, network_stream=False, **kwargs):
        sample, sample_rate = self.create_sample(self.text_to_morse(), **kwargs)
        if network_stream:
            stream = NetworkAudioServer()
            stream.start(sample.tobytes())
        else:
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

    def read_morse_audio(self, sample_rate=44100, network_stream=False):
        # ? Optional: ML to get better accuracy in determining gap lengths between characters and start of new word.
        if network_stream:
            self._get_network_stream(sample_rate)
        else:
            pass

    def _get_network_stream(self, sample_rate=44100):
        net_stream = NetworkAudioClient()
        conn = net_stream.connect()
        pa = PyAudio()
        stream = pa.open(rate=sample_rate, channels=2,
                         format=paFloat32, output=True,
                         frames_per_buffer=1024)
        self._read_audio_data(conn, stream)

    def _is_silent(self, data, threshold=500):
        return max(data) < threshold 

    def _read_audio_data(self, connect_obj, stream_obj):
        start = time.time()
        prev_audio = False
        while True:
            string = ''
            data = connect_obj.recv(1024)
            if not data:
                return
            stream_obj.write(data)
            arr = np.frombuffer(data, dtype=np.float32)
            
            if not self._is_silent(arr) and not prev_audio:
                stop = time.time()
                t = stop - start
                start = stop
                string += self._determine_symbol(t)
            elif self._is_silent(arr) and prev_audio:
                stop = time.time()
                t = stop - start
                start = stop
                space = self._determine_space(time)
                if space == ' ':
                    print(self._determine_character(string), end='')
                elif space == self.SPACE_SYMBOL:
                    print(self.SPACE_SYMBOL, ' ')

    def _determine_symbol(self, time):
        if time < 0.25:
            return '.'
        else:
            return '-'     

    def _determine_space(self, time):
        if time < 0.25:
            return ''
        elif time >= 0.25 and time < 0.7:
            return ' '
        else:
            return self.SPACE_SYMBOL

    def _determine_character(self, morse_code):
        keys = self.SYMBOLS.keys()
        vals = self.SYMBOLS.vals()
        idx = vals.index(morse_code)
        return keys[idx]
    
    # TODO: Determine wpm speed
    def _determine_speed(self):
        pass


class NetworkAudioServer:
    def __init__(self, ip='127.0.0.1', port=12345):
        self.server_addr = (ip, port)
        self.sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    def start(self, audio_data, buffer_size=1024, send_to_ip='127.0.0.1', send_to_port=12345):
        addr = (send_to_ip, send_to_port)
        self.sock.bind(self.server_addr)
        self.sock.listen(1)
        pa = PyAudio()
        stream = pa.open()
        self.sock.close()

    def send_chunk(self, in_data, frame_count, time_info, status_flags):
        self.sock.sendto()
        pass

class NetworkAudioClient:
    def __init__(self, server_ip='127.0.0.1', server_port=12345):
        self.address = (server_ip, server_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def connect(self, buffer_size=1024):
        return self.sock.connect(self.address)
          

if __name__ == "__main__":
    m = MorseCodeTranslator(text="CQ CQ CQ KN6FQY")
    code = m.text_to_morse()
    print(code)
    m.text_to_morse_audio(network_stream=False, tone_freq=440.0)
    m = MorseCodeTranslator(code=code)
    print(m.morse_to_text())
