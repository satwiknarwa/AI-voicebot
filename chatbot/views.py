import os
import json
import tempfile
import speech_recognition as sr
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
print("DEBUG — GROQ_API_KEY:", os.getenv("GROQ_API_KEY"))

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def index(request):
    return render(request, 'index.html')

@csrf_exempt
def chat_with_ai(request):
    """Text-based AI conversation"""
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            user_message = data.get("message", "").strip()

            if not user_message:
                return JsonResponse({"error": "No message provided"}, status=400)

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a friendly and helpful assistant."},
                    {"role": "user", "content": user_message},
                ],
            )

            bot_reply = response.choices[0].message.content.strip()
            return JsonResponse({"reply": bot_reply})

        except Exception as e:
            print("DEBUG — ERROR:", e)
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def process_audio(request):
    """Handle voice recording -> transcription"""
    if request.method == "POST":
        try:
            if 'audio' not in request.FILES:
                return JsonResponse({"error": "No audio file uploaded"}, status=400)

            audio_file = request.FILES['audio']

            # Save the uploaded audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
                for chunk in audio_file.chunks():
                    temp_audio.write(chunk)
                temp_audio_path = temp_audio.name

            # Use Groq Whisper for transcription
            with open(temp_audio_path, "rb") as af:
                transcript = client.audio.transcriptions.create(
                    file=(audio_file.name, af, "audio/webm"),
                    model="whisper-large-v3",
                    response_format="verbose_json"
                )

            os.remove(temp_audio_path)

            print("DEBUG — Transcribed Text:", transcript.text)
            return JsonResponse({"text": transcript.text})

        except Exception as e:
            print("DEBUG — AUDIO ERROR:", str(e))
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)
