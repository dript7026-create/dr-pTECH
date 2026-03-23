"""speech_to_text_google package

Expose the main helper for easy imports.
"""
from .google_speech_to_text import transcribe_file, convert_to_wav_mono16

__all__ = ["transcribe_file", "convert_to_wav_mono16"]
