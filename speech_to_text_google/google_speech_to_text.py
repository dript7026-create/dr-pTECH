#!/usr/bin/env python3
"""Google Cloud Speech-to-Text helper for audio files.

Usage:
  python google_speech_to_text.py input.mp3 --language en-US

Requirements:
  - Set the environment variable `GOOGLE_APPLICATION_CREDENTIALS` to your
    service account JSON path.
  - `ffmpeg` must be installed for `pydub` to read mp3 files.

This module converts input audio to 16kHz mono WAV and sends it to
Google Cloud Speech API. For files longer than 60s it uses the
long-running recognize API.
"""
from __future__ import annotations

import argparse
import io
import os


def convert_to_wav_mono16(path: str) -> bytes:
    from pydub import AudioSegment

    audio = AudioSegment.from_file(path)
    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    buf = io.BytesIO()
    audio.export(buf, format="wav")
    return buf.getvalue()


def transcribe_file(path: str, language: str = "en-US") -> str:
    from google.cloud import speech_v1 as speech

    audio_bytes = convert_to_wav_mono16(path)
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=language,
        enable_automatic_punctuation=True,
    )

    sample_width = 2
    estimated_seconds = len(audio_bytes) / (16000 * sample_width)

    if estimated_seconds > 60:
        operation = client.long_running_recognize(config=config, audio=audio)
        response = operation.result(timeout=600)
    else:
        response = client.recognize(config=config, audio=audio)

    transcripts = [result.alternatives[0].transcript for result in response.results]
    return "\n".join(transcripts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Transcribe an audio file using Google STT")
    parser.add_argument("input", help="Path to input audio file (wav/mp3/ogg/etc)")
    parser.add_argument("-l", "--language", default="en-US", help="Language code (default: en-US)")
    parser.add_argument("-o", "--output", help="Optional output text file")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise SystemExit(f"Input file not found: {args.input}")

    print(f"Converting and transcribing {args.input} (language={args.language})...")
    text = transcribe_file(args.input, language=args.language)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Transcription written to {args.output}")
    else:
        print("--- Transcription ---")
        print(text)


if __name__ == "__main__":
    main()
