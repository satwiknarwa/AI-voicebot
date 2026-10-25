# AI Voice Chatbot — Django, Groq, and Optional Custom-Voice TTS

A browser-based voice chatbot combining speech recognition, LLM responses, and speech synthesis in one Django application. It also includes dataset-preparation utilities for learning a custom single-speaker voice workflow.

## Features

- Record speech in the browser and transcribe it using Groq Whisper.
- Send typed or transcribed messages to a Groq-hosted LLM.
- Listen to answers through the text-to-speech endpoint.
- Choose default gTTS audio generation or optional local XTTS reference-audio inference.
- Inspect WAV recordings and validate transcript/audio pairs for a future voice-model training workflow.
- Keep credentials, personal recordings, and generated audio out of version control.

## Architecture

~~~text
Browser (typed text or microphone)
        |
        +--> /process_audio/ --> Groq Whisper STT
        |                            |
        +----------------------------+
                                     v
                            /chat_with_ai/
                               Groq LLM
                                     |
                                 Text reply
                                     |
                            /text_to_speech/
                             /             \
                       gTTS (default)    XTTS (optional,
                                         local reference WAV)
                                     |
                               Browser audio
~~~

## Tech stack

- Python and Django
- Groq API for LLM responses and Whisper transcription
- gTTS for default TTS output
- Optional Coqui XTTS for local reference-audio voice synthesis
- HTML, CSS, JavaScript, and Python standard-library dataset utilities

## Setup

Python 3.10 or 3.11 is recommended if you plan to try the optional XTTS dependencies.

### 1. Create a virtual environment

Windows PowerShell:

~~~powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
~~~

Linux/macOS:

~~~bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
~~~

Edit the local .env file and add your own GROQ_API_KEY and DJANGO_SECRET_KEY. Never commit real credentials.

### 2. Run Django

~~~bash
python manage.py check
python manage.py migrate
python manage.py runserver
~~~

Open http://127.0.0.1:8000/.

## Text-to-speech modes

### Default: gTTS

Set VOICE_TTS_ENGINE=gtts. This is the easiest way to test speech playback, but it uses an online TTS service and does not clone your voice.

### Optional local XTTS reference-audio inference

1. Install the optional dependencies in a compatible environment:

   ~~~bash
   pip install -r requirements-xtts.txt
   ~~~

2. Place a clean WAV recording of your own voice at voice_training/data/reference.wav, or set VOICE_REFERENCE_WAV to another local path.
3. In your local .env, set:

   ~~~env
   VOICE_TTS_ENGINE=xtts
   VOICE_LANGUAGE=en
   VOICE_REFERENCE_WAV=voice_training/data/reference.wav
   VOICE_TTS_MODEL=tts_models/multilingual/multi-dataset/xtts_v2
   VOICE_TTS_GPU=false
   ~~~

4. Restart Django and send a message.

XTTS conditions synthesis on reference audio using a pretrained model. It is not the same as fine-tuning or training a new model from your dataset. Keep recordings private and only use voices you have permission to use.

## Voice dataset preparation

The voice_training folder contains scripts to inspect WAV audio and validate transcript/audio pairs.

~~~bash
python voice_training/inspect_audio.py
~~~

Copy voice_training/transcripts.example.csv to voice_training/transcripts.csv, replace the example sentences with the exact words spoken in each recording, then run:

~~~bash
python voice_training/prepare_dataset.py
~~~

The resulting manifest is generic metadata, not a complete trainer-specific dataset. Fine-tuning a model on the prepared data remains a separate next step. See [voice_training/README.md](voice_training/README.md) for details.

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | / | Chat UI |
| POST | /chat_with_ai/ | Accepts JSON with a message; returns a text reply |
| POST | /process_audio/ | Accepts an audio upload named audio; returns a transcript |
| POST | /text_to_speech/ | Accepts JSON with text; returns audio/mpeg or audio/wav |

## Repository structure

~~~text
chatbot/                 Django views, URL routes, and browser UI
voicebot_core/           Django project configuration
voice_training/          WAV inspection and transcript manifest utilities
requirements.txt         Main chatbot dependencies
requirements-xtts.txt    Optional local XTTS dependencies
.env.example             Sample configuration; contains no secrets
~~~

## Security notes

- Keep real .env files and API keys private.
- Do not commit personal WAV recordings or generated audio.
- For public deployment, set DEBUG=false, configure ALLOWED_HOSTS explicitly, use HTTPS, and add authentication/rate limiting appropriate to your deployment.
- gTTS can send text to an external provider. Use local XTTS mode when local synthesis is required, and review the model's license and terms before redistribution.

## Project status

The Django text/audio chatbot and dataset-preparation utilities are implemented. Optional XTTS reference-audio inference is integrated. Fine-tuning a model on the personal dataset and testing a complete locally trained-voice pipeline remain in progress.
