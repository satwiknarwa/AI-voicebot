# Voice Chatbot (Django)

A simple Django-based voice chatbot that records voice in browser, sends to backend, uses STT -> LLM -> TTS and returns audio + text.

## Features
- Browser-based voice recording
- Backend Speech-to-Text (Whisper or SpeechRecognition)
- LLM integration (OpenAI API)
- Text-to-Speech (gTTS)

## Setup
1. Create and activate virtualenv
   ```bash
   python -m venv venv
   source venv/bin/activate  # on Windows use venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Set environment variables (example using Linux/macOS):
   ```bash
   export OPENAI_API_KEY="your_openai_api_key"
   export DJANGO_SECRET_KEY="replace_this_with_a_secret"
   ```

3. Run migrations and start server
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

4. Open http://127.0.0.1:8000/

## Notes
- For production TTS or higher-quality voices, replace gTTS with ElevenLabs or other provider.
- For better STT use OpenAI Whisper API or a local whisper model.
