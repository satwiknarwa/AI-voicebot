import json
import logging
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from groq import Groq

from .tts_service import TTSConfigurationError, synthesize_speech

load_dotenv()
logger = logging.getLogger(__name__)

MAX_MESSAGE_CHARS = 5000
MAX_TTS_CHARS = 3000
MAX_AUDIO_UPLOAD_BYTES = 15 * 1024 * 1024


class ServiceConfigurationError(RuntimeError):
    """A required service setting is missing."""


def index(request):
    return render(request, "index.html")


def _groq_client():
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ServiceConfigurationError(
            "GROQ_API_KEY is not configured. Add it to your local .env file."
        )
    return Groq(api_key=api_key)


@csrf_exempt
@require_POST
def chat_with_ai(request):
    """Generate a text reply from the configured Groq chat model."""
    try:
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return JsonResponse({"error": "Request body must be valid JSON."}, status=400)

        user_message = str(data.get("message", "")).strip()
        if not user_message:
            return JsonResponse({"error": "Please enter a message."}, status=400)
        if len(user_message) > MAX_MESSAGE_CHARS:
            return JsonResponse(
                {"error": f"Message must be {MAX_MESSAGE_CHARS} characters or fewer."},
                status=413,
            )

        try:
            client = _groq_client()
        except ServiceConfigurationError as exc:
            return JsonResponse({"error": str(exc)}, status=503)

        response = client.chat.completions.create(
            model=os.getenv("GROQ_CHAT_MODEL", "llama-3.1-8b-instant"),
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a friendly, clear, and helpful voice assistant. "
                        "Keep most answers concise and natural when spoken aloud."
                    ),
                },
                {"role": "user", "content": user_message},
            ],
        )
        reply = (response.choices[0].message.content or "").strip()
        if not reply:
            return JsonResponse({"error": "The AI returned an empty response."}, status=502)
        return JsonResponse({"reply": reply})

    except Exception:
        logger.exception("Chat generation failed.")
        return JsonResponse(
            {"error": "The AI service could not answer this request. Check the server logs."},
            status=502,
        )


@csrf_exempt
@require_POST
def process_audio(request):
    """Transcribe a browser-uploaded audio recording with Groq Whisper."""
    audio_file = request.FILES.get("audio")
    if audio_file is None:
        return JsonResponse({"error": "No audio file was uploaded."}, status=400)
    if audio_file.size > MAX_AUDIO_UPLOAD_BYTES:
        return JsonResponse(
            {"error": "Audio upload is too large. Keep it under 15 MB."},
            status=413,
        )

    try:
        client = _groq_client()
    except ServiceConfigurationError as exc:
        return JsonResponse({"error": str(exc)}, status=503)

    temp_path = None
    try:
        suffix = Path(audio_file.name or "recording.webm").suffix or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio:
            temp_path = temp_audio.name
            for chunk in audio_file.chunks():
                temp_audio.write(chunk)

        with open(temp_path, "rb") as audio_stream:
            transcript = client.audio.transcriptions.create(
                file=(
                    audio_file.name or "recording.webm",
                    audio_stream,
                    audio_file.content_type or "audio/webm",
                ),
                model=os.getenv("GROQ_STT_MODEL", "whisper-large-v3"),
                response_format="verbose_json",
            )

        transcript_text = (getattr(transcript, "text", "") or "").strip()
        return JsonResponse({"text": transcript_text})

    except Exception:
        logger.exception("Audio transcription failed.")
        return JsonResponse(
            {"error": "Audio transcription failed. Check the audio format and server logs."},
            status=502,
        )
    finally:
        if temp_path:
            try:
                os.unlink(temp_path)
            except OSError:
                logger.warning("Temporary audio file could not be removed.")


@csrf_exempt
@require_POST
def text_to_speech(request):
    """Convert a reply to audio using gTTS or optional local XTTS inference."""
    try:
        try:
            data = json.loads(request.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return JsonResponse({"error": "Request body must be valid JSON."}, status=400)

        text = str(data.get("text", "")).strip()
        if not text:
            return JsonResponse({"error": "Text is required."}, status=400)
        if len(text) > MAX_TTS_CHARS:
            return JsonResponse(
                {"error": f"Text-to-speech input must be {MAX_TTS_CHARS} characters or fewer."},
                status=413,
            )

        audio_bytes, content_type = synthesize_speech(text)
        response = HttpResponse(audio_bytes, content_type=content_type)
        response["Cache-Control"] = "no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response

    except TTSConfigurationError as exc:
        return JsonResponse({"error": str(exc)}, status=503)
    except ValueError as exc:
        return JsonResponse({"error": str(exc)}, status=400)
    except Exception:
        logger.exception("Text-to-speech generation failed.")
        return JsonResponse(
            {"error": "Could not synthesize speech. Check the selected TTS engine and server logs."},
            status=502,
        )
