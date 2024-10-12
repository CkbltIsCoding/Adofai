# from pydub import AudioSegment
#
#
# def change_speed(in_file, out_file, speed):
#     audio = AudioSegment.from_file(in_file)
#     new_audio = audio._spawn(
#         audio.raw_data, {"frame_rate": int(audio.frame_rate * speed)}
#     ).set_frame_rate(audio.frame_rate)
#     new_audio.export(out_file, format="ogg")
#
# def add_sound(in_file, out_file, offset, ms_list: list[int], callback):
#     if in_file:
#         audio = AudioSegment.from_file(in_file)
#         frame_rate = audio.frame_rate
#     else:
#         frame_rate = 44100
#         audio = AudioSegment.silent(offset + ms_list[-1] + 1000, frame_rate)
#     beat = AudioSegment.from_file("beat.ogg", frame_rate=frame_rate) - 3
#     beats = AudioSegment.silent(ms_list[-1] + 1000, frame_rate)
#     for index in range(len(ms_list)):
#         beats = beats.overlay(beat, ms_list[index])
#         if index % 20 == 0:
#             # print(f"Loading... ({index / len(ms_list) * 100:.2f}%)")
#             if not callback((index + 1) / len(ms_list)):
#                 return False
#         # if index == 10000:
#         #     (audio - 2).overlay(beats + 3, offset).export(out_file, format="ogg")
#         #     return True
#     callback(1)
#     (audio - 2).overlay(beats + 3, offset).export(out_file, format="ogg")
#     return True
#
#
# # change_speed("beat.ogg", "beat2.ogg", 10)

import librosa
import soundfile as sf
import numpy as np
import math


def change_speed(in_file, out_file, speed):
    audio, audio_sr = librosa.load(in_file)
    sf.write(out_file, audio, int(audio_sr * speed), format="wav")


def add_sound(in_file, out_file, offset, ms_list: list[int], callback):
    global audio, beat
    if in_file:
        audio, audio_sr = librosa.load(in_file)
    else:
        audio_sr = 44100
        audio = np.zeros(int(audio_sr * (offset + ms_list[-1] + 1000) / 1000))
    beat, beat_sr = librosa.load("beat.ogg")
    if beat_sr != audio_sr:
        beat = librosa.resample(beat, orig_sr=beat_sr, target_sr=audio_sr)
    beats = np.zeros(int(audio_sr * (offset + ms_list[-1] + 1000) / 1000))
    for index in range(len(ms_list)):
        ms = ms_list[index]
        pos = int(audio_sr * (ms + offset) / 1000)
        for i in range(len(beat)):
            beats[pos + i] += beat[i]

        if index % 20 == 0:
            if not callback((index + 1) / len(ms_list)):
                return False
    for i in range(len(audio)):
        if i < len(beats):
            audio[i] += beats[i] * 0.8
    callback(1)
    sf.write(out_file, audio, audio_sr, format="wav")

    return True
