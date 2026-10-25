# Custom Voice Dataset Pipeline — In Progress

This folder contains dataset-preparation utilities for the custom voice workflow in the main Django voice chatbot.

## Implemented

- WAV duration, sample rate, channels, RMS, and peak inspection.
- Validation of transcript/audio pairs, missing files, duplicate filenames, and empty text.
- CSV metadata manifest generation.
- Privacy defaults that exclude private recordings and generated dataset files from Git.

## Current status

The dataset-preparation scripts are implemented. The web application has an optional XTTS inference mode that uses a local reference WAV with a pretrained model. That inference mode is not fine-tuning a new model. Training/adaptation on the prepared personal dataset and end-to-end validation with a locally trained model remain in progress.

## Dataset layout

Place recordings you own or have permission to use in the ignored local folder:

~~~text
voice_training/
  data/
    raw/
      001.wav
      002.wav
  transcripts.csv
~~~

Use uncompressed PCM WAV recordings. Ensure each transcript matches the exact words spoken in its corresponding audio file.

## 1. Inspect audio

~~~bash
python voice_training/inspect_audio.py
~~~

You can also pass a file or directory explicitly:

~~~bash
python voice_training/inspect_audio.py voice_training/data/raw/001.wav
~~~

## 2. Prepare transcript mappings

Copy voice_training/transcripts.example.csv to voice_training/transcripts.csv and replace the example sentences with the exact spoken words for every recording. Keep the column names filename,text.

## 3. Validate and create metadata

~~~bash
python voice_training/prepare_dataset.py
~~~

The script writes voice_training/data/metadata.csv only if the audio/transcript pairs validate. The manifest is model-agnostic and may need conversion to the format required by your chosen trainer.

## Next steps

1. Gather additional clean recordings and accurate transcripts.
2. Choose an open-source TTS training framework and adapt the manifest to its required format.
3. Train/adapt a model and evaluate the generated speech.
4. Connect and validate model inference in the Django application.

A few very short recordings can help you learn the pipeline but are generally not enough for robust, natural-sounding voice cloning.
