import os
from dotenv import load_dotenv

load_dotenv()

# SignalWire
SIGNALWIRE_PROJECT_ID = os.getenv("SIGNALWIRE_PROJECT_ID", "")
SIGNALWIRE_API_TOKEN = os.getenv("SIGNALWIRE_API_TOKEN", "")
SIGNALWIRE_SPACE_URL = os.getenv("SIGNALWIRE_SPACE_URL", "")
SIGNALWIRE_FROM_NUMBER = os.getenv("SIGNALWIRE_FROM_NUMBER", "")

# Target
TARGET_PHONE_NUMBER = os.getenv("TARGET_PHONE_NUMBER", "+18054398008")

# Ngrok
NGROK_URL = os.getenv("NGROK_URL", "")

# Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# Whisper
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

# Call settings
SILENCE_THRESHOLD_MS = int(os.getenv("SILENCE_THRESHOLD_MS", "700"))
TRIAL_MESSAGE_DURATION_S = int(os.getenv("TRIAL_MESSAGE_DURATION_S", "0"))
MAX_CALL_DURATION_S = int(os.getenv("MAX_CALL_DURATION_S", "180"))

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
TRANSCRIPTS_DIR = os.path.join(OUTPUT_DIR, "transcripts")
REPORTS_DIR = os.path.join(OUTPUT_DIR, "reports")
SCENARIOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scenarios", "definitions")
