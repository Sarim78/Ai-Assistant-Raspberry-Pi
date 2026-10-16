# Jarvis AI Assistant

A voice assistant for Raspberry Pi. Say "Jarvis" and ask any question. It listens, searches the web when needed, and answers out loud in an ElevenLabs voice.

Built on a Raspberry Pi 400 with Python.

## How it works

1. **Wake word:** Picovoice Porcupine listens continuously for the word "Jarvis" and runs entirely on the Pi.
2. **Speech to text:** After the wake word, Vosk converts the spoken question into text on the Pi, offline.
3. **Answer:** The question goes to Claude (Anthropic API). Claude can use web search for current information like news, scores, and prices.
4. **Voice reply:** The answer is sent to the ElevenLabs text-to-speech API and played through the speaker.

## Hardware

- Raspberry Pi 400 (or Pi 4 / Pi 5 with 4 GB RAM or more)
- microSD card, 16 GB or larger
- USB microphone
- Speaker (USB speaker, or a speaker on the 3.5mm jack)
- Monitor with a micro-HDMI cable for first setup
- Power supply for the Pi

## Accounts and API keys

You need three accounts:

- **Picovoice Console** (console.picovoice.ai): provides the AccessKey for the wake word.
- **Anthropic Console** (console.anthropic.com): provides the API key for Claude. Anthropic charges per use.
- **ElevenLabs** (elevenlabs.io): provides the API key and a Voice ID for the spoken replies.

## Setup

### 1. Install Raspberry Pi OS

Use Raspberry Pi Imager or Rufus to write the current 64-bit Raspberry Pi OS to the SD card. Boot the Pi and finish the setup screens. Then update the system:

```
sudo apt update
sudo apt full-upgrade -y
```

### 2. Install VS Code (optional)

```
sudo apt install code
```

### 3. Install system packages

```
sudo apt install mpg123
```

### 4. Create the project and virtual environment

```
mkdir ~/jarvis
cd ~/jarvis
python3 -m venv venv
source venv/bin/activate
pip install pvporcupine pvrecorder vosk anthropic requests python-dotenv
```

Always run `source venv/bin/activate` before running the project. You'll see `(venv)` in the prompt when it's active.

### 5. Download the speech model

```
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
```

### 6. Check your microphone

```
arecord -l
```

Your USB microphone should appear in the list. Test the speaker with:

```
speaker-test -t wav -c 2
```

Press Ctrl+C to stop.

### 7. Add your keys

Create a file named `.env` in the `jarvis` folder:

```
PICOVOICE_ACCESS_KEY=your_picovoice_key
ANTHROPIC_API_KEY=your_anthropic_key
ELEVENLABS_API_KEY=your_elevenlabs_key
ELEVENLABS_VOICE_ID=your_voice_id
```

The `.env` file holds private keys. Never commit it to GitHub.

## Running Jarvis

```
cd ~/jarvis
source venv/bin/activate
python jarvis.py
```

Wait for "Jarvis is ready," then say "Jarvis" followed by your question. Press Ctrl+C to stop.

## Project structure

```
jarvis/
├── jarvis.py                          # Main program
├── .env                               # Your API keys (private, not committed)
├── .gitignore                         # Keeps .env and the model folder out of Git
├── requirements.txt                   # Python packages
└── vosk-model-small-en-us-0.15/       # Speech recognition model (downloaded)
```

## Configuration

Settings are at the top of `jarvis.py`:

- `MODEL`: the Claude model used for answers.
- `SYSTEM`: the instructions that shape how Jarvis talks. Edit this to change its personality.
- `max_uses` in the web search tool: how many searches Claude can run per question. Lowering it keeps costs down.
- `model_id` in the ElevenLabs request: set to a Flash model to cut voice costs roughly in half.

## Costs

Costs depend on use. For light to moderate use, expect roughly $10 to $25 a month, mostly from the Claude API (including web search) and ElevenLabs. Check each provider's pricing page for current rates.

## Troubleshooting

- **Wake word doesn't respond:** Check that your microphone shows up with `arecord -l` and that your Picovoice AccessKey is valid.
- **No sound from the speaker:** Run `speaker-test -t wav -c 2` to test the audio output, and make sure `mpg123` is installed.
- **"Invalid AccessKey" error:** Log into the Picovoice Console and confirm your key is active.
- **Speech is misheard:** Try a larger Vosk model. It's more accurate but uses more memory.
- **Slow replies:** ElevenLabs and Claude both need internet. Check your Wi-Fi connection.
- **Web search error:** Check docs.claude.com for the current name of the web search tool and update it in `jarvis.py`.

## Known limitations

- Jarvis has no memory between runs. Conversation history resets when the program restarts.
- The Pi has no built-in microphone, so a USB mic is required.
- Recognition works best when the speaker is close to the microphone.

## License

Add your license here, for example MIT.

## Acknowledgments

- [Picovoice Porcupine](https://picovoice.ai) for wake word detection
- [Vosk](https://alphacephei.com/vosk/) for offline speech recognition
- [Anthropic Claude](https://www.anthropic.com) for answers and web search
- [ElevenLabs](https://elevenlabs.io) for text-to-speech
