# Custom Voice Cloning & AI Voice Chatbot — Dataset Pipeline

This code lives inside the existing [AI-voicebot Django project](https://github.com/satwiknarwa/AI-voicebot). It adds reproducible dataset inspection and audio/transcript validation for the custom single-speaker voice project.

## Implemented in this folder

- **Audio inspection:** reports WAV duration, sample rate, channels, RMS level, and peak level.
- **Transcript alignment validation:** checks WAV/transcript pairs and flags missing files, duplicate filenames, and empty transcript text.
- **Metadata manifest:** writes a CSV that can be adapted for a selected open-source TTS training framework.
- **Privacy defaults:** raw recordings and generated metadata are ignored by Git.

## Current status

The dataset-preparation code is implemented. Custom TTS model fine-tuning/training and end-to-end inference with the trained voice are still in progress; these scripts do not claim to train a model.

## Prepare your data

From the repository root, create the local data folder and place your own recordings (or recordings you have permission to use) in it:

~~~text
voice_training/
  data/
    raw/
      001.wav
      002.wav
  transcripts.csv
~~~

Use uncompressed PCM WAV files. Keep transcripts exact: punctuation and wording should match the spoken recording as closely as practical.

### 1. Inspect recordings

~~~bash
python voice_training/inspect_audio.py
~~~

Or inspect a specific file/folder:

~~~bash
python voice_training/inspect_audio.py voice_training/data/raw/001.wav
~~~

### 2. Create the transcript CSV

Copy `voice_training/transcripts.example.csv` to `voice_training/transcripts.csv`. Replace the example transcript text with the exact spoken words for each recording. Keep the columns named `filename,text`.

### 3. Validate audio/text alignment

~~~bash
python voice_training/prepare_dataset.py
~~~

Optional paths:

~~~bash
python voice_training/prepare_dataset.py --audio-dir voice_training/data/raw --transcripts voice_training/transcripts.csv --output voice_training/data/metadata.csv
~~~

The script exits with errors rather than producing a manifest when an audio file is missing, a transcript is blank, or the pair mapping is inconsistent.

## Next steps

1. Collect more clean, accurately transcribed recordings.
2. Select an open-source TTS framework and adapt the validated metadata to its required dataset format.
3. Train/adapt the model and test speech synthesis locally.
4. Connect a real custom TTS inference endpoint to the Django chatbot using `CUSTOM_TTS_API_URL` (see the main repository README).

A few very short samples are useful for learning the pipeline, but are generally not enough to expect robust, natural-sounding voice cloning.
