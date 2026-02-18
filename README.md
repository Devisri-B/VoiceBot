# Voice Bot - AI Agent Tester

A voice bot that calls a medical office AI agent, simulates realistic patient scenarios, records conversations, and identifies bugs.

## Quick Start

```bash
# 1. Setup (one-time)
./setup.sh

# 2. Edit .env with your Twilio credentials
#    Get free trial at https://www.twilio.com/try-twilio

# 3. Start the server (starts ngrok + FastAPI)
./run.sh

# 4. In a new terminal, run test calls
source venv/bin/activate
python -m app.pipeline.run_test_suite --scenario schedule_new   # Single scenario
python -m app.pipeline.run_test_suite                           # All 12 scenarios
```

## Prerequisites

- **Python 3.11+**
- **macOS** (tested on Apple Silicon)
- **Homebrew** (`brew`)
- **Ollama** with `llama3` model ([ollama.com](https://ollama.com))
- **Twilio account** (free trial gives $15.50 credit)

## Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description |
|----------|-------------|
| `TWILIO_ACCOUNT_SID` | From Twilio Console |
| `TWILIO_AUTH_TOKEN` | From Twilio Console |
| `TWILIO_FROM_NUMBER` | Your Twilio phone number (e.g., +1234567890) |
| `TARGET_PHONE_NUMBER` | Number to call (default: +18054398008) |
| `NGROK_URL` | Auto-set by `run.sh` |
| `OLLAMA_MODEL` | LLM model (default: llama3) |
| `WHISPER_MODEL_SIZE` | STT model size: tiny, base, small (default: base) |

## Project Structure

```
BOT/
├── app/
│   ├── main.py              # FastAPI server
│   ├── config.py            # Settings
│   ├── telephony/           # Twilio call + WebSocket handling
│   ├── audio/               # mu-law conversion, TTS, audio buffering
│   ├── speech/              # Whisper STT, VAD, turn detection
│   ├── brain/               # Ollama LLM, patient persona, response gen
│   ├── scenarios/           # 12 patient scenario YAML definitions
│   ├── analysis/            # Bug detection, transcript logging, reports
│   └── pipeline/            # Call orchestrator, test suite runner
├── output/
│   ├── transcripts/         # JSON transcripts per call
│   └── reports/             # Bug analysis reports
├── setup.sh                 # One-time setup
└── run.sh                   # Launch server + ngrok
```

## 12 Test Scenarios

| # | Scenario | Patient | Tests |
|---|----------|---------|-------|
| 1 | Schedule new appointment | Sarah Johnson, 34 | Basic scheduling flow |
| 2 | Reschedule appointment | Michael Torres, 52 | Lookup + rescheduling |
| 3 | Cancel appointment | Linda Chen, 67 | Cancellation + fee question |
| 4 | Prescription refill | Robert Williams, 45 | Medication details + pharmacy |
| 5 | Medication question | Angela Martinez, 38 | Side effects, medical scope |
| 6 | Billing inquiry | James O'Brien, 58 | Billing dispute handling |
| 7 | Lab results | Priya Sharma, 41 | HIPAA, identity verification |
| 8 | Urgent symptoms | David Kim, 72 | Emergency triage (CRITICAL) |
| 9 | Insurance verification | Maria Rodriguez, 29 | Jargon handling |
| 10 | Confused elderly | Dorothy Wilson, 84 | Patience, conversation flow |
| 11 | Angry patient | Frank Davis, 47 | De-escalation |
| 12 | Limited English | Carlos Mendez, 55 | Language accommodation |

## Bug Detection

The system detects:
- **Hallucinations**: Agent makes up patient records, appointments, or medical data
- **Non-sequiturs**: Agent response has no connection to what was said
- **Missing verification**: Agent acts without confirming identity
- **Slow responses**: Gaps >8 seconds between turns
- **Medical safety**: Dosage advice, missed urgency for chest pain
- **LLM review**: Post-call qualitative analysis via Ollama

## Cost

All tools are free:
- Twilio free trial: $15.50 credit (~370 calls)
- faster-whisper: Local, open source
- edge-tts: Free (Microsoft Edge TTS)
- Ollama + llama3: Local, open source
- ngrok: Free tier
