#!/usr/bin/env python3
"""Validate voice recording/transcript pairs and generate a CSV manifest.

Expected transcript CSV columns: filename,text. This prepares data only; it
does not train a text-to-speech model.
"""
from __future__ import annotations

import argparse
import csv
import wave
from pathlib import Path


def wav_metadata(path: Path) -> tuple[float, int, int, int]:
    with wave.open(str(path), "rb") as wav:
        if wav.getcomptype() != "NONE":
            raise ValueError("WAV must use uncompressed PCM audio.")
        rate = wav.getframerate()
        if rate <= 0:
            raise ValueError("Invalid sample rate.")
        duration = wav.getnframes() / rate
        return duration, rate, wav.getnchannels(), wav.getsampwidth()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate matching WAV recordings and transcripts."
    )
    parser.add_argument("--audio-dir", default="voice_training/data/raw")
    parser.add_argument("--transcripts", default="voice_training/transcripts.csv")
    parser.add_argument("--output", default="voice_training/data/metadata.csv")
    args = parser.parse_args()

    audio_dir = Path(args.audio_dir)
    transcript_path = Path(args.transcripts)
    output_path = Path(args.output)

    if not audio_dir.is_dir():
        parser.error(f"Audio directory does not exist: {audio_dir}")
    if not transcript_path.is_file():
        parser.error(
            f"Transcript CSV not found: {transcript_path}. "
            "Copy transcripts.example.csv to transcripts.csv and fill it in."
        )

    errors: list[str] = []
    rows: list[tuple[str, str]] = []
    seen: set[str] = set()

    with transcript_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or not {"filename", "text"}.issubset(reader.fieldnames):
            parser.error("CSV must contain the columns: filename,text")

        for line_number, row in enumerate(reader, start=2):
            filename = (row.get("filename") or "").strip()
            text = (row.get("text") or "").strip()

            if not filename or not text:
                errors.append(f"Line {line_number}: filename and text are required.")
                continue
            if Path(filename).name != filename or filename in {".", ".."}:
                errors.append(f"Line {line_number}: use a filename only: {filename}")
                continue
            if filename in seen:
                errors.append(f"Line {line_number}: duplicate filename: {filename}")
                continue
            seen.add(filename)

            if Path(filename).suffix.lower() != ".wav":
                errors.append(f"Line {line_number}: expected a .wav file: {filename}")
                continue

            audio_path = audio_dir / filename
            if not audio_path.is_file():
                errors.append(f"Line {line_number}: audio file not found: {filename}")
                continue
            try:
                wav_metadata(audio_path)
            except (OSError, wave.Error, ValueError) as exc:
                errors.append(f"Line {line_number}: invalid WAV {filename}: {exc}")
                continue
            rows.append((filename, text))

    wav_files = {
        p.name for p in audio_dir.iterdir()
        if p.is_file() and p.suffix.lower() == ".wav"
    }
    for missing in sorted(wav_files - seen):
        errors.append(f"No transcript row found for audio file: {missing}")

    if errors:
        print("Dataset validation failed; no manifest was written:")
        for error in errors:
            print(f"- {error}")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as target:
        writer = csv.writer(target)
        writer.writerow([
            "filename", "text", "duration_seconds",
            "sample_rate_hz", "channels", "sample_width_bytes",
        ])
        for filename, transcript in rows:
            duration, rate, channels, width = wav_metadata(audio_dir / filename)
            writer.writerow([
                filename, transcript, f"{duration:.3f}", rate, channels, width
            ])

    print(f"Validated {len(rows)} recording/transcript pairs.")
    print(f"Manifest written to: {output_path}")
    print("This is a generic manifest; adapt it to the selected TTS trainer.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
