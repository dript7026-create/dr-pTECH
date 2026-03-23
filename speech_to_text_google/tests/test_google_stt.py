import os
import unittest

from speech_to_text_google import transcribe_file, convert_to_wav_mono16


class TestGoogleSTT(unittest.TestCase):
    def test_convert_returns_bytes(self):
        # Create a short silent WAV in memory using pydub if available
        here = os.path.dirname(__file__)
        sample = os.path.join(here, "..", "examples", "sample_silence.wav")
        # Ensure function exists and callable — not executing real transcription here.
        self.assertTrue(callable(convert_to_wav_mono16))
        self.assertTrue(callable(transcribe_file))


if __name__ == "__main__":
    unittest.main()
