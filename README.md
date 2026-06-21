# OPERATOR — How to Command AI in 2026 (and Not Get Out-Computed)

A short, dense audiobook for an operator: the person whose job is no longer to *do* the
work faster than a machine (you can't), but to decide what the machine's compute gets
pointed at, set the constraints, and judge whether the result is actually good.

Every chapter is a ~15-minute spoken script, narrated with a **fully open-source, local,
no-GPU, no-API-key** text-to-speech engine. You can listen to the rendered MP3s in
[`audio/`](audio/), read or edit the scripts in [`scripts/`](scripts/), and re-render at
any time with one command.

## Chapters

| # | File | What it gives you |
|---|------|-------------------|
| 00 | Cold Open | The real stakes: out-*computed* vs out-*thought*, and the open seat. |
| 01 | The Map | The 2026 model landscape and how to choose without a leaderboard obsession. |
| 02 | The Instruction Stack | How to make any model actually perform: spec, not wish. |
| 03 | The Jaystay Loop | A repeatable cycle for deep work: Frame · Brief · Constrain · Unleash · Inspect · Bank. |
| 04 | Autonomy Inside Guardrails | Long autonomous runs with no babysitting — keys/permissions done right, safely. |
| 05 | Build With What's Free | Open repos, public endpoints, licenses → a shipped product. |
| 06 | The Human Moat | What stays scarce when intelligence gets cheap: taste, trust, distribution, ownership. |

Total runtime: roughly **100 minutes**.

## Listen

The rendered audio lives in [`audio/`](audio/) as `*.mp3` (128 kbps, tagged). Play them in
order. That's it.

## How the audio is made (the open-source TTS choice)

The brief was "open voice that doesn't sound terrible, using the open-source options that
are the best fit." Here's the honest 2026 landscape and why this repo defaults to **Piper**:

| Engine | Quality | Speed / HW | License | Best for |
|--------|---------|-----------|---------|----------|
| **Piper** *(used here)* | Good, natural | Very fast, **CPU-only** | MIT | Long-form narration, offline, zero setup, no GPU |
| **Kokoro-82M** | Excellent prosody | Fast, CPU-ok | Apache-2.0 | The upgrade pick when you want richer delivery |
| **OpenVoice v2** | Very good + **voice clone** | GPU preferred | MIT | Cloning a specific voice / tone control |
| **XTTS-v2 (Coqui)** | Excellent + clone | GPU for speed | Coqui CPML | Zero-shot cloning, many languages |
| **Chatterbox (Resemble)** | Excellent, expressive | GPU | MIT | Emotion/expressiveness control |

This repo uses **Piper with the `en-US-ryan-high` voice** because it runs fully locally on a
CPU with no GPU and no HuggingFace access (the voice model is pulled from a GitHub release),
which is exactly the constrained environment this was built in. It sounds clean and natural
for narration. If you have a GPU or want richer prosody, flip to **Kokoro** (see below) — the
pipeline auto-detects it.

## Re-render it yourself

```bash
pip install -r requirements.txt

# one-time: download the open-source voice (from GitHub, no HuggingFace needed)
mkdir -p voices && curl -L -o voices/ryan.tar.gz \
  https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-ryan-high.tar.gz \
  && tar xzf voices/ryan.tar.gz -C voices

# render everything in ./scripts -> ./audio
python src/generate_audiobook.py

# render one chapter
python src/generate_audiobook.py scripts/03_jaystay_loop.txt

# upgrade to Kokoro prosody (after: pip install kokoro soundfile)
python src/generate_audiobook.py --engine kokoro
```

The pipeline cleans each script for speech, synthesizes paragraph by paragraph with natural
pauses, concatenates losslessly, and encodes to MP3 using the static `ffmpeg` that ships
inside the `imageio-ffmpeg` wheel — so **no system `ffmpeg` install is required** either.

## Editing the content

The scripts in [`scripts/`](scripts/) are plain text written to be read aloud (no markdown,
no symbols that read badly). Edit any of them and re-render. [`BOOK_BIBLE.md`](BOOK_BIBLE.md)
is the internal style guide / brief used to keep the chapters consistent — useful if you want
to add or rewrite a chapter in the same voice.

## Why this exists

Because the audiobook *you'd actually want played to you* — the one that teaches the person
giving the instructions how to give the right instructions — didn't exist. So here it is.
No hype, no doom. Operator-grade. Go drive.
