#!/usr/bin/env python3
"""Inspect PCM WAV files for duration and basic signal levels.

This utility uses only the Python standard library and never modifies audio.
"""
from __future__ import annotations

import argparse
import math
import struct
import wave
from pathlib import Path
from typing import Iterator


def normalized_samples(raw: bytes, sample_width: int) -> Iterator[float]:
    """Yield PCM samples normalized approximately to [-1.0, 1.0]."""
    if sample_width == 1:
        # 8-bit PCM WAV samples are unsigned.
        for value in raw:
            yield (value - 128) / 128.0
    elif sample_width == 2:
        usable = len(raw) - len(raw) % 2
        for (value,) in struct.iter_unpack("<h", raw[:usable]):
            yield value / 32768.0
    elif sample_width == 3:
        usable = len(raw) - len(raw) % 3
        for offset in range(0, usable, 3):
            value = int.from_bytes(raw[offset:offset + 3], "little", signed=True)
            yield value / 8388608.0
    elif sample_width == 4:
        usable = len(raw) - len(raw) % 4
        for (value,) in struct.iter_unpack("<i", raw[:usable]):
            yield value / 2147483648.0
    else:
        raise ValueError(f"Unsupported PCM sample width: {sample_width} bytes.")


def inspect_wav(path: Path) -> dict[str, float | int | str]:
    with wave.open(str(path), "rb") as audio:
        if audio.getcomptype() != "NONE":
            raise ValueError("Compressed WAV is unsupported; convert to PCM WAV.")
        sample_rate = audio.getframerate()
        if sample_rate <= 0:
            raise ValueError("Invalid sample rate.")

        frames = audio.getnframes()
        sample_width = audio.getsampwidth()
        channels = audio.getnchannels()
        duration = frames / sample_rate
        sum_squares = 0.0
        count = 0
        peak = 0.0

        while True:
            raw = audio.readframes(8192)
            if not raw:
                break
            for sample in normalized_samples(raw, sample_width):
                peak = max(peak, abs(sample))
                sum_squares += sample * sample
                count += 1

    rms = math.sqrt(sum_squares / count) if count else 0.0
    return {
        "file": path.name,
        "duration_seconds": duration,
        "sample_rate_hz": sample_rate,
        "channels": channels,
        "sample_width_bytes": sample_width,
        "rms": rms,
        "peak": peak,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect one PCM WAV file or every WAV file in a folder."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="voice_training/data/raw",
        help="WAV file or directory (default: voice_training/data/raw)",
    )
    args = parser.parse_args()
    target = Path(args.path)

    if not target.exists():
        parser.error(f"Path does not exist: {target}")

    wav_files = [target] if target.is_file() else sorted(
        p for p in target.iterdir() if p.is_file() and p.suffix.lower() == ".wav"
    )
    if not wav_files:
        parser.error(f"No WAV files found at: {target}")

    print("File | Duration(s) | Sample rate(Hz) | Channels | RMS | Peak")
    print("-" * 72)
    failures = 0
    for path in wav_files:
        try:
            info = inspect_wav(path)
            print(
                f"{info['file']} | {info['duration_seconds']:.2f} | "
                f"{info['sample_rate_hz']} | {info['channels']} | "
                f"{info['rms']:.4f} | {info['peak']:.4f}"
            )
        except (OSError, wave.Error, ValueError) as exc:
            failures += 1
            print(f"{path.name} | ERROR: {exc}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
