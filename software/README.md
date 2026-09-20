# Splitter Studio

Splits songs into four stems — vocals, drums, bass and other — and writes
them to a USB stick in the layout the StemDeck hardware player expects.

Separation runs locally with [Demucs](https://github.com/facebookresearch/demucs).
Nothing is uploaded anywhere.

---

## Running it

**Double-click `run.command`.**

That is the whole setup. The first launch builds a local Python
environment and downloads the dependencies — about 2 GB, mostly PyTorch —
which takes several minutes. Every launch after that opens the app
straight away.

From a terminal instead:

```bash
./run.command
```

---

## Using it

1. **Drop audio files** onto the drop zone, or click it to browse.
   MP3, WAV and AIFF are supported.
2. Tracks queue up and process one at a time. Separation is the slow
   part — expect a few minutes per track, as it runs on the CPU.
3. **Choose an export folder** with the button in the "Export to" strip.
   Point it at your USB stick.
4. When a track shows **Complete**, hit **Transfer** to copy it across.

---

## What it produces

Each track becomes a folder containing the four stems, a waveform image
at three zoom levels, and a metadata file:

```
01 adore u (Original Mix)/
├── vocals.wav
├── drums.wav
├── bass.wav
├── other.wav
├── waveform_overview.png
├── waveform_medium.png
├── waveform_detail.png
└── metadata.json
```

```json
{
    "title": "01 adore u (Original Mix)",
    "source_file": "01 adore u (Original Mix).aiff",
    "bpm": 123,
    "duration": 220.65,
    "stems": ["vocals.wav", "drums.wav", "bass.wav", "other.wav"]
}
```

Processed tracks are kept in `output/` until you transfer them. That
folder is not tracked by git — the stems are large and can always be
regenerated.

---

## Requirements

- **macOS** — `run.command` is a macOS launcher
- **Python 3.10 or newer recommended** — 3.9 works but is past end of life
  and causes occasional packaging errors. `brew install python` gets you
  a current one
- **ffmpeg** *(optional)* — Demucs uses it to read MP3 and AIFF files.
  WAV works without it. Install with `brew install ffmpeg`

Everything else installs automatically.

---

## If something goes wrong

**"run.command cannot be opened because it is from an unidentified
developer"**
macOS quarantines scripts downloaded from the internet. Right-click the
file and choose **Open**, then confirm. You only need to do this once.

**"Permission denied"**

```bash
chmod +x run.command
```

**"Python 3.9 or newer was not found"**

```bash
brew install python
```

**pip crashes partway through installing, mentioning `__init__.tmpl.py`
or `encode() argument 'encoding' must be str`**
An old-Python packaging bug. `run.command` already works around it, so
make sure you are on the current version of the script, then:

```bash
./run.command --reset
```

**MP3 or AIFF files fail to process**
Install ffmpeg: `brew install ffmpeg`

**The environment is broken and you want to start over**

```bash
./run.command --reset
```

This deletes `venv/` and reinstalls from scratch. It does not touch
anything in `output/`.

---

## Project layout

```
software/
├── run.command          setup and launch
├── requirements.txt     Python dependencies
├── main.py              entry point
├── core/                separation, BPM, waveforms, queue, transfer
├── gui/                 window, queue rows, theme
└── output/              processed tracks (not tracked by git)
```

The hardware player that reads these USB sticks lives in `../hardware`.
