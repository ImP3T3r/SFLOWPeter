import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Groq API
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "whisper-large-v3-turbo"

# Audio
SAMPLE_RATE = 16000
CHANNELS = 1
AUDIO_DTYPE = "int16"
BLOCK_SIZE = 1024

# UI
PILL_WIDTH_IDLE = 34
PILL_WIDTH_RECORDING = 120
PILL_WIDTH_STATUS = 52
PILL_HEIGHT = 34
PILL_OPACITY = 0.90
PILL_CORNER_RADIUS = 17
PILL_MARGIN_BOTTOM = 14
LOGO_SIZE = 22

# Logo path
LOGO_PATH = os.path.join(os.path.dirname(__file__), "logo_small.png")

# Audio Visualizer
NUM_BARS = 8
VIZ_FPS = 30
BAR_DECAY = 0.80
BAR_GAIN = 6.0

# Hotkey
DOUBLE_TAP_INTERVAL = 0.4  # seconds for double-tap detection

# Database
DB_PATH = os.path.join(os.path.dirname(__file__), "transcriptions.db")
