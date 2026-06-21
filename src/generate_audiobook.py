#!/usr/bin/env python3
"""
OPERATOR audiobook — open-source TTS render pipeline.

Turns the plain-text chapter scripts in ./scripts into listenable MP3s in ./audio
using a fully open-source, local, no-GPU-required voice (Piper). Optionally upgrades
to Kokoro-82M if it's installed (better prosody) — see requirements.txt.

Usage:
    python src/generate_audiobook.py                 # render every scripts/*.txt
    python src/generate_audiobook.py scripts/03_*.txt
    python src/generate_audiobook.py --engine kokoro
    python src/generate_audiobook.py --voice voices/en-us-ryan-high.onnx

Design notes:
- Text is "spoken-cleaned" first (strip any stray markdown, normalize symbols).
- Piper splits on sentences and inserts natural pauses; we add a touch of extra
  silence between paragraphs so chapters breathe like an audiobook.
- WAV is concatenated losslessly, then encoded to MP3 via the ffmpeg binary that
  ships inside the `imageio-ffmpeg` wheel (no system ffmpeg needed).
"""
from __future__ import annotations
import argparse
import glob
import os
import re
import subprocess
import sys
import tempfile
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_VOICE = os.path.join(ROOT, "voices", "en-us-ryan-high.onnx")
OUT_DIR = os.path.join(ROOT, "audio")
SAMPLE_RATE = 22050  # ryan-high is 22.05kHz
LENGTH_SCALE = 1.45  # >1 slows narration; tuned for a calm ~150 wpm audiobook pace


def ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"  # fall back to a system install if present


def clean_for_speech(text: str) -> str:
    """Make raw script text friendly for a TTS engine."""
    # Drop common markdown noise in case a script slipped some in.
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)  # headers
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)                 # bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)                     # italics
    text = re.sub(r"`{1,3}([^`]*)`{1,3}", r"\1", text)           # code spans
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", text)            # links -> label
    # Symbols that read badly.
    text = text.replace("%", " percent").replace("&", " and ")
    text = text.replace("→", ", then ").replace("/", " or ")
    text = text.replace("\r", " ")
    return text


def paragraphs(text: str) -> list[str]:
    blocks = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return [re.sub(r"[ \t]*\n[ \t]*", " ", p) for p in blocks]


def silence_bytes(rate: int, seconds: float) -> bytes:
    return b"\x00\x00" * int(rate * seconds)


def piper_synth(voice, text: str) -> tuple[bytes, int]:
    """Synthesize one block of text in-process; return (int16 PCM bytes, sample rate)."""
    from piper.config import SynthesisConfig
    cfg = SynthesisConfig(length_scale=LENGTH_SCALE)
    pcm = bytearray()
    rate = SAMPLE_RATE
    for chunk in voice.synthesize(text, syn_config=cfg):
        pcm += chunk.audio_int16_bytes
        rate = chunk.sample_rate
    return bytes(pcm), rate


def kokoro_synth(kpipe, text: str) -> tuple[bytes, int]:
    import numpy as np
    chunks = [a for _, _, a in kpipe(text, voice="am_michael")]
    audio = np.concatenate(chunks) if chunks else np.zeros(1, dtype=np.float32)
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()
    return pcm, 24000


def write_wav(path: str, pcm: bytes, rate: int) -> float:
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return len(pcm) / 2 / rate


def encode_mp3(wav_path: str, mp3_path: str, title: str) -> None:
    cmd = [ffmpeg_exe(), "-y", "-i", wav_path,
           "-codec:a", "libmp3lame", "-b:a", "128k", "-ar", "44100",
           "-metadata", f"title={title}",
           "-metadata", "album=OPERATOR — Command AI in 2026",
           "-metadata", "artist=Open-source narration (Piper)",
           "-metadata", "genre=Audiobook",
           mp3_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def render_chapter(script_path: str, engine: str, voice, kpipe=None) -> str:
    base = os.path.splitext(os.path.basename(script_path))[0]
    with open(script_path, encoding="utf-8") as f:
        raw = f.read()
    title_line = next((l.strip() for l in raw.splitlines() if l.strip()), base)
    text = clean_for_speech(raw)

    os.makedirs(OUT_DIR, exist_ok=True)
    pcm = bytearray()
    rate = SAMPLE_RATE
    gap = None  # paragraph pause, sized once we know the rate
    for para in paragraphs(text):
        if engine == "kokoro":
            seg, rate = kokoro_synth(kpipe, para)
        else:
            seg, rate = piper_synth(voice, para)
        if gap is None:
            gap = silence_bytes(rate, 0.45)
        pcm += seg + gap

    with tempfile.TemporaryDirectory() as tmp:
        merged = os.path.join(tmp, "merged.wav")
        secs = write_wav(merged, bytes(pcm), rate)
        mp3 = os.path.join(OUT_DIR, base + ".mp3")
        encode_mp3(merged, mp3, title_line)
    print(f"  -> {os.path.relpath(mp3, ROOT)}  ({secs/60:.1f} min)")
    return mp3


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("scripts", nargs="*", help="script .txt files (default: scripts/*.txt)")
    ap.add_argument("--engine", choices=["piper", "kokoro"], default="piper")
    ap.add_argument("--voice", default=DEFAULT_VOICE)
    args = ap.parse_args()

    files = args.scripts or sorted(glob.glob(os.path.join(ROOT, "scripts", "*.txt")))
    if not files:
        sys.exit("No scripts found in ./scripts")

    kpipe = None
    voice = None
    if args.engine == "kokoro":
        from kokoro import KPipeline  # type: ignore
        kpipe = KPipeline(lang_code="a")
    else:
        from piper import PiperVoice
        if not os.path.exists(args.voice):
            sys.exit(f"Voice model not found: {args.voice}\nSee README for the one-line download.")
        print(f"Loading voice {os.path.basename(args.voice)} ...")
        voice = PiperVoice.load(args.voice)

    print(f"Rendering {len(files)} chapter(s) with engine={args.engine}")
    for f in files:
        print(f"[{os.path.basename(f)}]")
        render_chapter(f, args.engine, voice, kpipe)
    print("Done. Audio in ./audio")


if __name__ == "__main__":
    main()
