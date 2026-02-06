# STT-Mistral

STT-Mistral is a user-friendly desktop application that transforms audio files into text using Mistral AI's powerful voxtral-mini-2602 transcription model.

With its clean and intuitive interface, you can easily transcribe lectures, meetings, interviews, or any audio content in multiple languages without complex setup.

The app automatically detects the spoken language, supports popular audio formats like MP3, WAV, and M4A, and securely stores your API key locally for convenience.

Simply select your audio file, enter your Mistral API key, and click "Generate transcript" to get accurate text results in seconds - perfect for students, professionals, or anyone needing quick and reliable audio transcription.

## Features

- **Audio Transcription**: Transcribe audio files using Mistral's voxtral-mini-2602 model
- **Simple Interface**: Clean, intuitive GUI built with Tkinter
- **Auto Language Detection**: Automatically detects the language in audio files
- **Local API Key Storage**: Your Mistral API key is stored locally in config.json
- **Multiple Audio Formats**: Supports WAV, MP3, M4A, FLAC, and OGG files

## Requirements

- Python 3.7+
- Mistral API key

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

## Usage

1. **Get API Key**: Obtain a Mistral API key from [Mistral AI](https://mistral.ai/)
2. **Enter API Key**: Input your API key in the "Mistral API key" field
3. **Select Audio File**: Click "Browse" to choose an audio file
4. **Transcribe**: Click "Generate transcript" to start transcription
5. **View Results**: The transcribed text will appear in the output area

## Configuration

Your API key is automatically saved locally in `config.json` for convenience.

## API Details

- **Endpoint**: `https://api.mistral.ai/v1/audio/transcriptions`
- **Model**: `voxtral-mini-2602`
- **Diarization**: Disabled (to avoid timestamp requirements)
- **Language Detection**: Automatic

## File Structure

```
VoxtralPythonGUI/
├── app.py              # Main application
├── config.json         # API key storage
├── requirements.txt    # Dependencies
└── README.md          # This file
```

## Supported Audio Formats

- WAV (*.wav)
- MP3 (*.mp3)
- M4A (*.m4a)
- FLAC (*.flac)
- OGG (*.ogg)

## Notes

- The application requires an active internet connection to access the Mistral API
- Transcription time depends on audio file size and server load
- API key is stored locally and never transmitted to third parties
