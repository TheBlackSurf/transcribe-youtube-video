import speech_recognition as sr
import os
import subprocess
from pytube import YouTube
from pydub import AudioSegment
import srt
from pydub.silence import split_on_silence

SEGMENT_LENGTH = 10
ENERGY_THRESHOLD = 12000
MIN_TEXT_LENGTH = 3


def download_youtube_video(youtube_url):
    youtube = YouTube(youtube_url)
    video = youtube.streams.get_highest_resolution()
    video.download()
    mp4_filename = video.default_filename
    wav_filename = os.path.splitext(mp4_filename)[0] + '.wav'
    subprocess.run(['ffmpeg', '-i', mp4_filename, wav_filename])
    transcribe_audio(wav_filename)
    os.remove(wav_filename)


def transcribe_audio(wav_filename):
    audio_path = wav_filename
    transcribe_path = os.path.splitext(wav_filename)[0] + '.srt'
    MAX_SEGMENT_DURATION = 8
    sound = AudioSegment.from_wav(audio_path)
    sound = sound.set_channels(1)
    sound = sound.set_frame_rate(16000)
    sound.export(audio_path, format='wav')
    r = sr.Recognizer()
    subtitles = []
    audio_segments = split_on_silence(
        sound, min_silence_len=500, silence_thresh=-50, keep_silence=True)
    total_duration = len(sound) / 1000
    for i, segment in enumerate(audio_segments):
        if len(segment) > MAX_SEGMENT_DURATION * 1000:
            subsegments = [segment[x:x + (MAX_SEGMENT_DURATION * 1000)] for x in
                           range(0, len(segment), MAX_SEGMENT_DURATION * 1000)]
        else:
            subsegments = [segment]
        for subsegment in subsegments:
            subsegment.export('segment.wav', format='wav')
            with sr.AudioFile('segment.wav') as source:
                audio = r.record(source)
            try:
                text = r.recognize_google(
                    audio, language='pl-PL', show_all=False)
                text = text.strip().capitalize()
                if len(text) >= MIN_TEXT_LENGTH:
                    print(text)
                else:
                    text = ''
            except sr.UnknownValueError:
                text = ''
            os.remove('segment.wav')
            subsegment_duration = len(subsegment) / 1000
            if len(subtitles) == 0:
                start = 0
            else:
                start = subtitles[-1].end.total_seconds()
            end = start + subsegment_duration
            subtitle = srt.Subtitle(index=len(subtitles) + 1,
                                    start=srt.timedelta(seconds=start),
                                    end=srt.timedelta(seconds=end),
                                    content=text)
            subtitles.append(subtitle)

    with open(transcribe_path, 'w', encoding='utf-8') as file:
        file.write(srt.compose(subtitles))


def main():
    youtube_url = input("Podaj link do filmu na YouTube: ")
    download_youtube_video(youtube_url)
    print("Transkrypcja została zapisana w pliku transcription.srt")


if __name__ == "__main__":
    main()
