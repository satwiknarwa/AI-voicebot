"""Speech synthesis adapters for the Django voice chatbot.

Default mode uses gTTS. Optional XTTS mode runs locally and conditions synthesis
on a speaker reference WAV. XTTS uses a pretrained model; it does not fine-tune
a new model on the supplied recording.
"""
from __future__ import annotations

import os
import tempfile
from io import BytesIO
from pathlib import Path
from threading import Lock

_model = None
_model_name: str | None = None
_model_lock = Lock()
_synthesis_lock = Lock()


class TTSConfigurationError(RuntimeError):
    """Raised when a selected TTS engine is not configured correctly."""


def _load_xtts():
    global _model, _model_name

    model_name = os.getenv(
        "VOICE_TTS_MODEL",
        "tts_models/multilingual/multi-dataset/xtts_v2",
    )
    with _model_lock:
        if _model is not None and _model_name == model_name:
            return _model
        try:
            from TTS.api import TTS
        except ImportError as exc:
            raise TTSConfigurationError(
                "XTTS is optional. Install requirements-xtts.txt in a compatible "
                "Python environment, or set VOICE_TTS_ENGINE=gtts."
            ) from exc

        use_gpu = os.getenv("VOICE_TTS_GPU", "false").strip().lower() in {
            "1", "true", "yes", "on"
        }
        try:
            _model = TTS(model_name=model_name, progress_bar=False, gpu=use_gpu)
        except Exception as exc:
            _model = None
            _model_name = None
            raise TTSConfigurationError(
                "Could not load the configured XTTS model. Check the model name, "
                "Python environment, and model download."
            ) from exc
        _model_name = model_name
        return _model


def synthesize_speech(text: str) -> tuple[bytes, str]:
    """Return synthesized audio bytes and their MIME type."""
    text = text.strip()
    if not text:
        raise ValueError("Text to synthesize cannot be empty.")

    engine = os.getenv("VOICE_TTS_ENGINE", "gtts").strip().lower()
    language = os.getenv("VOICE_LANGUAGE", "en").strip() or "en"

    if engine == "gtts":
        try:
            from gtts import gTTS
            output = BytesIO()
            gTTS(text=text, lang=language, slow=False).write_to_fp(output)
            return output.getvalue(), "audio/mpeg"
        except Exception as exc:
            raise RuntimeError(
                "gTTS could not generate audio. Check network access and VOICE_LANGUAGE."
            ) from exc

    if engine == "xtts":
        reference = Path(
            os.getenv("VOICE_REFERENCE_WAV", "voice_training/data/reference.wav")
        ).expanduser()
        if not reference.is_file():
            raise TTSConfigurationError(
                "XTTS mode needs a local reference WAV. Set VOICE_REFERENCE_WAV "
                "to a clean recording you have permission to use."
            )

        model = _load_xtts()
        try:
            with tempfile.TemporaryDirectory(prefix="voicebot-tts-") as temp_dir:
                output_path = Path(temp_dir) / "reply.wav"
                # This is reference-audio inference, not model fine-tuning.
                with _synthesis_lock:
                    model.tts_to_file(
                        text=text,
                        speaker_wav=str(reference),
                        language=language,
                        file_path=str(output_path),
                    )
                if not output_path.is_file() or output_path.stat().st_size == 0:
                    raise RuntimeError("XTTS did not generate an audio file.")
                return output_path.read_bytes(), "audio/wav"
        except TTSConfigurationError:
            raise
        except Exception as exc:
            raise RuntimeError(
                "XTTS synthesis failed. Check the reference WAV, supported language, "
                "and local model installation."
            ) from exc

    raise TTSConfigurationError(
        "Unsupported VOICE_TTS_ENGINE. Use 'gtts' or 'xtts'."
    )
