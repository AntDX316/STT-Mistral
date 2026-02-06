# STT-Mistral

STT-Mistral is a user-friendly desktop application that transforms audio into text using Mistral AI’s Voxtral models. It supports both **file-based transcription** and **real-time microphone streaming**.

With its clean and intuitive interface, you can transcribe lectures, meetings, interviews, or any audio content without complex setup.

The app automatically detects the spoken language for file transcription, supports popular audio formats like MP3, WAV, and M4A, and securely stores your API key locally for convenience.

Simply select your audio file and click **Generate transcript**, or use **Start realtime** to stream from your microphone.

## Features

- **Audio Transcription**: Transcribe audio files using Mistral's `voxtral-mini-2602` model
- **Realtime Mic Streaming**: Live transcription from your microphone using `voxtral-mini-transcribe-realtime-2602`
- **Simple Interface**: Clean, intuitive GUI built with Tkinter
- **Auto Language Detection**: Automatically detects the language in audio files
- **Local API Key Storage**: Your Mistral API key is stored locally in config.json
- **Multiple Audio Formats**: Supports WAV, MP3, M4A, FLAC, and OGG files

## Requirements

- Python 3.7+
- Mistral API key
- Microphone access (for realtime mode)

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
3. **File mode**: Click "Browse" to choose an audio file, then "Generate transcript"
4. **Realtime mode**: Click "Start realtime" and speak into your microphone; click "Stop realtime" to end
5. **View Results**: The transcribed text will appear in the output area

## Configuration

Your API key is automatically saved locally in `config.json` for convenience.

## API Details

- **Endpoint (file)**: `https://api.mistral.ai/v1/audio/transcriptions`
- **Model (file)**: `voxtral-mini-2602`
- **Model (realtime)**: `voxtral-mini-transcribe-realtime-2602`
- **Diarization**: Disabled (to avoid timestamp requirements)
- **Language Detection**: Automatic (file mode)

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
