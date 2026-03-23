# Google Speech-to-Text helper

This small helper converts common audio files to 16 kHz mono WAV and transcribes
them using Google Cloud Speech-to-Text.

Prerequisites
- Create a Google service account with Speech-to-Text enabled and download the
  JSON key.
- Set the environment variable:

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS = 'C:\path\to\service-account.json'
```

- Install dependencies in your virtualenv:

```bash
pip install -r requirements.txt
```

Usage

```bash
python google_speech_to_text.py examples/input.mp3 --language en-US -o out.txt
```

Notes
- `ffmpeg` is required for `pydub` to read MP3/other formats. On Windows you can
  install via `choco install ffmpeg` or download from ffmpeg.org.
