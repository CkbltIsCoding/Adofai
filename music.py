from pydub import AudioSegment


def change_speed(in_file, out_file, speed):
    audio = AudioSegment.from_file(in_file)
    new_audio = audio._spawn(
        audio.raw_data, {"frame_rate": int(audio.frame_rate * speed)}
    ).set_frame_rate(audio.frame_rate)
    new_audio.export(out_file, format="ogg")

def add_sound(in_file, out_file, offset, ms_list: list[int], callback):
    if in_file:
        audio = AudioSegment.from_file(in_file)
        frame_rate = audio.frame_rate
    else:
        frame_rate = 44100
        audio = AudioSegment.silent(offset + ms_list[-1] + 1000, frame_rate)
    beat = AudioSegment.from_file("beat.ogg", frame_rate=frame_rate) - 3
    beats = AudioSegment.silent(ms_list[-1] + 1000, frame_rate)
    for index in range(len(ms_list)):
        beats = beats.overlay(beat, ms_list[index])
        if index % 100 == 0:
            # print(f"Loading... ({index / len(ms_list) * 100:.2f}%)")
            if not callback((index + 1) / len(ms_list)):
                return False
        # if index == 10000:
        #     (audio - 2).overlay(beats + 3, offset).export(out_file, format="ogg")
        #     return True
    (audio - 2).overlay(beats + 3, offset).export(out_file, format="ogg")
    return True


change_speed("beat.ogg", "beat2.ogg", 10)
