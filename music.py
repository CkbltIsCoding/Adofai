from pydub import AudioSegment


def change_speed(in_file, out_file, speed):
    audio = AudioSegment.from_file(in_file)
    new_audio = audio._spawn(audio.raw_data, {"frame_rate": int(audio.frame_rate * speed)}).set_frame_rate(audio.frame_rate)
    new_audio.export(out_file, format="wav")
