# StemDeck

A four-stem USB player for the Raspberry Pi. Loads tracks prepared by
[Splitter Studio](../software) from a USB stick and plays them through
real buttons, rotary encoders and a touchscreen — vocals, drums and
bass/other each on their own volume knob.

---

## What you need

- **Raspberry Pi 4 or 5** running Raspberry Pi OS (64-bit)
- **480 × 320 touchscreen** — the window is a fixed 480 × 320
- **USB audio adapter** — the Pi's headphone jack is noisy; the engine
  looks for an output device with "USB" in its name and falls back to the
  system default if there isn't one
- **5 buttons** and **4 rotary encoders** (see wiring below)
- **A USB stick** with tracks on it

---

## Wiring

All pin numbers are **BCM (GPIO) numbering**, which is what `gpiozero`
uses.

### Buttons

Every button is configured with an internal pull-up, so wire each one
between its GPIO pin and any **GND** pin. No resistors needed.

| GPIO | Physical pin | Function              |
|------|--------------|-----------------------|
| 17   | 11           | Play / pause          |
| 0    | 27           | Search back  *(hold)* |
| 11   | 23           | Search forward *(hold)* |
| 27   | 13           | Jog left *(hold)*     |
| 22   | 15           | Jog right *(hold)*    |

### Rotary encoders

Each encoder uses two GPIO pins for its A and B channels, with its common
pin to **GND**.

| Encoder           | A (GPIO) | B (GPIO) | Physical pins |
|-------------------|----------|----------|---------------|
| Tempo             | 1        | 7        | 28, 26        |
| Vocals volume     | 5        | 6        | 29, 31        |
| Drums volume      | 13       | 19       | 33, 35        |
| Bass + Other      | 20       | 21       | 38, 40        |

Bass and Other share one encoder — turning it moves both together.

> **Note on pin choices.** GPIO 0 and 1 are the reserved ID_SD / ID_SC
> pins used for HAT identification, and GPIO 7 and 11 belong to SPI0.
> They work fine on a breadboard, but if you ever add a HAT — including
> an I²S audio board, which needs GPIO 18–21 — these will need moving.

---

## USB stick layout

The player scans mounted volumes for a folder called **`music`** at the
root of the stick. Each track is a folder inside it:

```
USB_STICK/
└── music/
    ├── 01 adore u (Original Mix)/
    │   ├── vocals.wav
    │   ├── drums.wav
    │   ├── bass.wav
    │   ├── other.wav
    │   ├── waveform_overview.png
    │   ├── waveform_medium.png
    │   ├── waveform_detail.png
    │   └── metadata.json
    └── Another Track/
        └── ...
```

Stems can be `.wav`, `.mp3`, `.aif` or `.aiff`. A missing stem is skipped
rather than treated as an error, so a track will still play without one.

`metadata.json` supplies the track title and BPM:

```json
{
    "title": "01 adore u (Original Mix)",
    "bpm": 123,
    "duration": 220.65
}
```

> **Important.** Splitter Studio writes track folders straight into
> whatever export folder you choose, so point it at
> `<USB>/music` — not the root of the stick. If you export to the root,
> the player will not find anything.

---

## Install

On the Pi, from the `hardware` folder:

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev ffmpeg \
    libportaudio2 portaudio19-dev libsndfile1 alsa-utils \
    swig liblgpio-dev

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`ffmpeg` is not optional here — the audio engine shells out to it to
decode every stem.

Check the Pi can see your USB audio adapter:

```bash
aplay -l
```

---

## Run

```bash
source venv/bin/activate
cd core
python3 main.py
```

The `cd core` matters: `main.py` imports its siblings directly
(`from app_window import MainWindow`), so it only runs from inside that
folder.

---

## Controls

| Control            | Action                                        |
|--------------------|-----------------------------------------------|
| Play button        | Play / pause                                  |
| Search back / fwd  | Scrub while held; speed follows the zoom level |
| Jog left / right   | Nudge tempo, accelerating the longer you hold |
| Stem encoders      | Volume for vocals, drums, and bass+other      |
| Tempo encoder      | ±8 % playback speed, pitch included           |

On screen:

- **REWIND / FAST FORWARD** — same as the search buttons
- **ZOOM** — cycles the waveform through overview, medium and detail,
  which also changes how fast the search buttons scrub
- **SONGS** — opens the track browser
- **Tempo slider** — mirrors the tempo encoder

Pulling the USB stick out mid-track stops playback and clears the
browser.

---

## If something goes wrong

**No tracks listed / "NO USB"**
The stick needs a `music` folder at its root, and it has to be mounted.
Confirm with `lsblk` and `ls /media/*/*`. A headless Pi may not
auto-mount — `usbmount` or a udev rule handles that.

**No sound**
Run `aplay -l` to confirm the adapter is detected. The engine prints the
device it chose at startup. Without a USB device it falls back to the
system default, which may be HDMI.

**"ERROR: ffmpeg is not installed"**

```bash
sudo apt install ffmpeg
```

**Buttons or encoders do nothing**
`gpiozero` needs a pin factory. `lgpio` is in `requirements.txt`; if it
failed to build, install the system library and reinstall:

```bash
sudo apt install liblgpio-dev
pip install --force-reinstall lgpio
```

**Playback stutters**
Every stem is decoded into RAM in full, so a five-minute track holds
roughly 400 MB across four stems. On a 2 GB Pi that is tight. Watch it
with `free -h` while a track loads.

---

## Known issues

- `scripts/run.sh` points at `../main.py`, which does not exist —
  `main.py` is in `core/`. Use the commands under **Run** above.
- `scripts/setup.sh` creates its virtual environment in whatever
  directory you run it from, while `scripts/run.sh` expects it one level
  up. The manual install above avoids the mismatch.
- Tempo changes pitch along with speed, like a turntable. There is no
  key lock.

---

## Layout

```
hardware/
├── requirements.txt
├── core/
│   ├── main.py            entry point — run from this folder
│   ├── app_window.py      wiring between GPIO, audio and the pages
│   ├── audio_engine.py    stem mixing, search, tempo, jog
│   ├── gpio.py            buttons and encoders
│   ├── usb_manager.py     detects the stick and its music folder
│   ├── player_ui.py       playback page
│   ├── selection_ui.py    track browser page
│   ├── track_browser.py   the track list itself
│   ├── waveform_widget.py scrolling waveform
│   └── styles.py          stylesheet
└── scripts/               see Known issues
```

Tracks are prepared on a Mac with [Splitter Studio](../software).
