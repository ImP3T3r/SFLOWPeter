# CLAUDE.md — SFlow Development Instructions

## What is SFlow?

SFlow is a macOS voice-to-text desktop tool that replaces Wispr Flow ($15/month). It captures audio via global hotkeys, transcribes using Groq Whisper API (~$0.02/hour), and auto-pastes text wherever the cursor is. It includes a floating pill UI overlay, real-time audio visualization, SQLite history, and a web dashboard.

## Quick Start

```bash
# 1. Install system dependency
brew install portaudio

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Set up environment
cp .env.example .env
# Edit .env and add your GROQ_API_KEY (get one at https://console.groq.com/keys)

# 5. Add your logo
# Place logo.png (full size) and logo_small.png (96x96 or similar) in the project root
# These are used in the pill UI overlay

# 6. Run
python3 main.py
```

## macOS Permissions Required

- **Accessibility**: System Settings → Privacy & Security → Accessibility → add your Terminal/IDE
- **Microphone**: Automatically requested on first use
- **Input Monitoring**: May be required for pynput — add your Terminal/IDE

## Project Structure

```
sflow/
├── main.py                 # Entry point — orchestrates all modules
├── config.py               # All configuration constants (UI, audio, paths)
├── ui/
│   ├── pill_widget.py      # Floating pill overlay (native macOS via PyObjC)
│   └── audio_visualizer.py # Real-time audio bars
├── core/
│   ├── recorder.py         # sounddevice audio capture
│   ├── transcriber.py      # Groq Whisper API client
│   ├── hotkey.py           # Global hotkeys (Ctrl+Shift hold + double-tap Ctrl)
│   └── clipboard.py        # Focus save/restore + native paste via AppleScript
├── db/
│   └── database.py         # SQLite CRUD
├── web/
│   └── server.py           # Flask dashboard at localhost:5000
├── logo.png                # Brand logo (full size)
├── logo_small.png          # Brand logo (for pill, ~96x96)
├── requirements.txt
├── .env                    # GROQ_API_KEY (never committed)
└── .env.example
```

## Architecture & Data Flow

```
Hotkey Press (pynput thread)
  → [QueuedConnection] → save_frontmost_app() + recorder.start()
  → pill.set_state(RECORDING)
  → sounddevice callback → queue.Queue → QTimer → audio_visualizer paints bars

Hotkey Release (pynput thread)
  → [QueuedConnection] → recorder.stop()
  → pill.set_state(PROCESSING)
  → background Thread: transcriber.transcribe(wav_buffer)
    → Groq Whisper API returns text
    → [QueuedConnection] → paste_text() + db.insert() + pill.set_state(DONE)
```

## Critical Implementation Details

### 1. Qt Signal Threading (MUST use QueuedConnection)
pynput emits signals from its own thread. Both QObjects live in the main thread, so Qt's `AutoConnection` incorrectly chooses `DirectConnection`. But since `emit()` comes from pynput's thread, UI modifications happen on the wrong thread — undefined behavior on macOS. **Always use explicit `Qt.ConnectionType.QueuedConnection`.**

### 2. macOS Floating Window (MUST use PyObjC)
Qt's `WindowDoesNotAcceptFocus` flag doesn't work properly on macOS. The pill must use native Cocoa APIs via PyObjC to float without stealing focus:
```python
import AppKit, objc
from ctypes import c_void_p

ns_view = objc.objc_object(c_void_p=c_void_p(widget.winId().__int__()))
ns_window = ns_view.window()
ns_window.setLevel_(AppKit.NSFloatingWindowLevel)
ns_window.setStyleMask_(ns_window.styleMask() | AppKit.NSWindowStyleMaskNonactivatingPanel)
ns_window.setHidesOnDeactivate_(False)
ns_window.setCollectionBehavior_(
    AppKit.NSWindowCollectionBehaviorCanJoinAllSpaces
    | AppKit.NSWindowCollectionBehaviorStationary
    | AppKit.NSWindowCollectionBehaviorFullScreenAuxiliary
)
```
This is the same approach used by Spotlight and Wispr Flow itself.

### 3. Auto-Paste (MUST use native AppleScript, not pyautogui)
pyautogui is unreliable on macOS when modifier keys were recently released. Use:
- `save_frontmost_app()` before recording (via AppleScript)
- `pbcopy` to copy text to clipboard
- AppleScript to restore focus to saved app
- AppleScript `keystroke "v" using command down` to paste

### 4. Audio Pipeline (thread-safe)
sounddevice callback runs in audio thread — NEVER touch Qt widgets from it. Use `queue.Queue` as bridge:
- Callback → puts audio chunks in queue
- QTimer on main thread → polls queue → updates visualizer

### 5. Short Recording Filter
Recordings under 0.3 seconds are accidental taps — skip transcription and return to idle.

## Customization

### Hotkeys
Edit `core/hotkey.py`:
- **Hold mode**: Currently Ctrl+Shift. Change `is_ctrl`/`is_shift` checks.
- **Hands-free mode**: Currently double-tap Ctrl within 400ms. Change `DOUBLE_TAP_INTERVAL` in config.py.

### UI Dimensions
Edit `config.py`:
- `PILL_WIDTH_IDLE` (34) — width when just showing logo
- `PILL_WIDTH_RECORDING` (120) — width during recording with bars
- `PILL_WIDTH_STATUS` (52) — width for checkmark/spinner/error
- `PILL_HEIGHT` (34) — height of pill
- `PILL_MARGIN_BOTTOM` (14) — distance from bottom of screen

### Audio
Edit `config.py`:
- `SAMPLE_RATE` (16000) — 16kHz is optimal for speech
- `NUM_BARS` (8) — number of visualizer bars
- `BAR_GAIN` (6.0) — sensitivity of bars
- `BAR_DECAY` (0.80) — how quickly bars fall

## Building from Scratch

If you want to rebuild this project from scratch using Claude, copy the `PRP.md` file and give it to Claude with the instruction: "Build this project following the PRP phases. Execute all phases sequentially, validating each one before moving to the next."

The PRP contains all the architectural decisions, gotchas, and anti-patterns discovered during development. It serves as a complete blueprint.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Pill doesn't appear | Check Accessibility permissions for your terminal |
| Pill appears but steals focus | Verify PyObjC is installed: `python3 -c "import AppKit"` |
| Audio not captured | Check Microphone permissions + verify portaudio: `brew list portaudio` |
| Paste doesn't work | Grant Accessibility permission to terminal; check `save_frontmost_app` |
| Ctrl+C doesn't kill the process | This is handled by `signal.signal(signal.SIGINT, signal.SIG_DFL)` in main.py |
| Short taps trigger transcription | Adjust the 0.3s threshold in `main.py` `_on_hotkey_released` |
| Web dashboard not loading | Check if port 5000 is free: `lsof -i :5000` |
