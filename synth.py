import numpy as np
from scipy.io.wavfile import write
import os

SR = 44100

def _default_amp_envelope(seg_len):
    if seg_len < int(SR * 0.05):
        evs = int(seg_len * 0.3)
        return np.concatenate([
            np.linspace(0., 1., evs),
            np.ones(seg_len - 2 * evs),
            np.linspace(1., 0., evs)
        ])
    else:
        evs = int(SR * 0.015)
        return np.concatenate([
            np.linspace(0., 1., evs),
            np.ones(seg_len - 2 * evs),
            np.linspace(1., 0., evs)
        ])

def generate_raw_sine_wave(freq_array, amp_array):
    dt = 1 / SR
    phase_changes = 2 * np.pi * freq_array * dt
    phases = np.cumsum(phase_changes) % (2 * np.pi)
    return np.sin(phases) * amp_array * _default_amp_envelope(len(amp_array))

def save_wav(x_wav: np.ndarray, file_name: str, in_dir='out'):
    """
    保存波形數據為 WAV 檔案。
    :param x_wav: 波形數據的 NumPy 數組。
    :param file_name: 保存的檔案名稱。
    :param in_dir: 保存檔案的目錄。
    """
    if np.max(np.abs(x_wav)) > 0:
        wav = np.int16(x_wav / np.max(np.abs(x_wav)) * 10000)
        existing_name = os.listdir(in_dir)
        saving_file_name = f'{file_name}.wav'
        r = 1
        while saving_file_name in existing_name:
            saving_file_name = f'{file_name}{r}.wav'
            r += 1
        write(f'{in_dir}/{saving_file_name}', SR, wav)

        return saving_file_name

def freq_amp_point_synth(freq, amp, time_len):
    return amp * np.sin(np.linspace(0., freq * 2 * np.pi, int(time_len * SR)))

if __name__ == '__main__':
    k = 10
    start = 220
    end = 440
    arr_s = []
    for i in range(k):
        print(start + (end - start) * (i/k))
        arr_s.append(freq_amp_point_synth(start + (end - start) * (i/k), 1, 1/k))
    save_wav(np.concatenate(arr_s), 'synth_abc')
