# Jarvis: Raspberry Pi Voice Assistant

Say "Jarvis" and ask a question. Jarvis listens for the wake word, transcribes your question offline, searches the web when it needs current information, and answers out loud in an ElevenLabs voice.

Built with Python and tested on a Raspberry Pi 400.

## Features

- Offline wake word detection with Picovoice Porcupine
- Offline speech-to-text with Vosk
- Answers and web search with Claude (Anthropic API)
- Natural spoken replies with ElevenLabs text-to-speech
- Optional systemd service to start automatically on boot

## How it works

1. **Wake word:** Porcupine listens continuously for "Jarvis" and runs entirely on the Pi.
2. **Speech to text:** After the wake word, Vosk turns your question into text on the Pi.
3. **Answer:** The question goes to Claude. Claude can search the web for current information such as news, scores, and prices.
4. **Voice reply:** The answer is sent to the ElevenLabs API and played through the speaker.

## Hardware

- Raspberry Pi 400, or Raspberry Pi 4 or 5 with at least 4 GB of RAM
- microSD card, 16 GB or larger
- USB microphone (the Pi has no built-in microphone)
- Speaker, either USB or connected to the 3.5 mm audio jack
- Monitor and micro-HDMI cable for first-time setup
- Official Raspberry Pi power supply

## Accounts and API keys

You need three accounts:

| Service | Used for | Sign up |
|---|---|---|
| Picovoice Console | Wake word AccessKey | [console.picovoice.ai](https://console.picovoice.ai) |
| Anthropic Console | Claude API key (billed per use) | [console.anthropic.com](https://console.anthropic.com) |
| ElevenLabs | API key and Voice ID for speech | [elevenlabs.io](https://elevenlabs.io) |

Keep all keys private. Never paste them into code, screenshots, or commit messages.

## Setup

### 1. Install Raspberry Pi OS

Use Raspberry Pi Imager to write the current **64-bit Raspberry Pi OS** to your SD card. Enable SSH and set your username and password in the Imager settings if you want remote access. Boot the Pi, complete the setup screens, and update the system:

```bash
sudo apt update
sudo apt full-upgrade -y
```

### 2. Install system packages

```bash
sudo apt install -y git mpg123 python3-venv python3-pip
```

Optional, for editing files in a graphical editor:

```bash
sudo apt install -y code
```

### 3. Clone the repository

```bash
cd ~
git clone https://github.com/Sarim78/Ai-Assistant-Raspberry-Pi.git
cd Ai-Assistant-Raspberry-Pi
```

### 4. Create a virtual environment and install Python packages

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Always run `source venv/bin/activate` before you run Jarvis. When the environment is active, `(venv)` appears at the start of your prompt.

### 5. Download the speech model

The Vosk model is about 40 MB and isn't stored in this repository.

```bash
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
rm vosk-model-small-en-us-0.15.zip
```

### 6. Check your audio devices

```bash
arecord -l
speaker-test -t wav -c 2
```

`arecord -l` should list your USB microphone. Press Ctrl+C to stop the speaker test.

### 7. Add your API keys

```bash
cp .env.example .env
nano .env
```

Fill in the values:

```
PICOVOICE_ACCESS_KEY=your_picovoice_access_key
ANTHROPIC_API_KEY=your_anthropic_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
ELEVENLABS_VOICE_ID=your_voice_id
```

Save with Ctrl+O and Enter, then exit with Ctrl+X. The `.env` file is ignored by Git, so your keys stay on the Pi.

## Running Jarvis

```bash
cd ~/Ai-Assistant-Raspberry-Pi
source venv/bin/activate
python jarvis.py
```

Wait until you hear "Jarvis is ready." Then say "Jarvis" and ask your question. Press Ctrl+C to stop.

## Run on boot (optional)

After Jarvis works from the terminal, you can run it as a background service. Edit `jarvis.service` first if your username isn't `pi`, and update `User=` and the paths to match.

```bash
sudo cp jarvis.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now jarvis
```

Check the status with `systemctl status jarvis`, or follow the live log with:

```bash
journalctl -u jarvis -f
```

## Configuration

Set these in `.env`. Defaults are used for any optional value you leave out.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `PICOVOICE_ACCESS_KEY` | Yes | none | Wake word engine |
| `ANTHROPIC_API_KEY` | Yes | none | Claude API |
| `ELEVENLABS_API_KEY` | Yes | none | Text to speech |
| `ELEVENLABS_VOICE_ID` | Yes | none | Voice used for replies |
| `JARVIS_MODEL` | No | `claude-haiku-5-5` | Claude model for answers |
| `ELEVENLABS_MODEL_ID` | No | `eleven_flash_v2_5` | Voice model. Flash costs about half as much as Multilingual v2 |
| `VOSK_MODEL_DIR` | No | `vosk-model-small-en-us-0.15` | Speech model folder |
| `JARVIS_MIC_INDEX` | No | `-1` (default device) | Microphone index from `arecord -l` if the default is wrong |
| `JARVIS_LOG_LEVEL` | No | `INFO` | Set to `DEBUG` for more detail |

Other settings are at the top of `jarvis.py`:

- `SYSTEM_PROMPT` controls how Jarvis speaks. Edit it to change its personality.
- `MAX_WEB_SEARCHES` limits how many searches Claude can run per question. Lower it to control costs.
- `HISTORY_LIMIT` sets how many messages are kept in conversation memory.

## Costs

Costs depend on how often you use Jarvis. For light to moderate use, expect roughly $10 to $25 per month, mostly from the Claude API (including web search) and ElevenLabs. Web search is billed per search, on top of token costs. Check each provider's pricing page for current rates.

## Project structure

```
Ai-Assistant-Raspberry-Pi/
├── jarvis.py               # Main program
├── jarvis.service          # systemd service file (optional)
├── requirements.txt        # Python dependencies
├── .env.example            # Template for your API keys
├── .gitignore              # Keeps secrets and large files out of Git
├── README.md
├── .env                    # Your keys (created on the Pi, never committed)
└── vosk-model-small-en-us-0.15/   # Speech model (downloaded, never committed)
```

## Troubleshooting

**Missing setting error on startup**
Check that `.env` exists and every required variable has a value.

**"Speech model folder not found"**
Make sure you ran the download step in the project folder and the `vosk-model-small-en-us-0.15` folder exists.

**Wake word doesn't respond**
Run `arecord -l` to confirm the microphone is detected. Then check that your Picovoice AccessKey is active in the Picovoice Console. Picovoice has changed its free tier, so your key may need a paid plan.

**"Invalid AccessKey" or wake word engine error**
Log in to the Picovoice Console and confirm the key is active and allowed for your device.

**No sound from the speaker**
Run `speaker-test -t wav -c 2` to test output. Make sure `mpg123` is installed.

**Microphone not picked up**
Try a different USB port, or set `JARVIS_MIC_INDEX` in `.env` to the number shown by `arecord -l`.

**Speech is misheard**
Recognition is best when the speaker is close to the microphone. A larger Vosk model is more accurate but needs more memory.

**Slow replies**
Claude and ElevenLabs both need an internet connection. Check your Wi-Fi.

**Web search error**
The web search tool version may have changed. Check [docs.claude.com](https://docs.claude.com) for the current tool name and update it in `jarvis.py`.

**Jarvis hears itself and wakes up**
Use headphones, or place the speaker away from the microphone.

## Known limitations

- Jarvis doesn't remember conversations after it restarts.
- Wake word and speech recognition work best in quiet rooms.
- The Pi needs internet access for Claude and ElevenLabs.

## Security

- Never commit `.env` or share your API keys.
- If a key is ever exposed, revoke it in the provider's console and create a new one.
- The `.gitignore` excludes `.env` and the speech model folder.

## Contributing

Issues and pull requests are welcome. Please keep API keys and personal data out of any commits.

## License

This project does not yet include a license. Add one before publishing, for example the MIT License.

## Acknowledgments

- [Picovoice Porcupine](https://picovoice.ai) for wake word detection
- [Vosk](https://alphacephei.com/vosk/) for offline speech recognition
- [Anthropic Claude](https://www.anthropic.com) for answers and web search
- [ElevenLabs](https://elevenlabs.io) for text to speech
