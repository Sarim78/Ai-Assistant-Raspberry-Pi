#!/usr/bin/env python3
"""Jarvis: a wake-word voice assistant for Raspberry Pi."""

import json
import logging
import os
import signal
import subprocess
import sys
from array import array

import anthropic
import pvporcupine
import requests
from dotenv import load_dotenv
from pvrecorder import PvRecorder
from vosk import KaldiRecognizer, Model

load_dotenv()

logging.basicConfig(
    level=os.getenv("JARVIS_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("jarvis")

PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")

CLAUDE_MODEL = os.getenv("JARVIS_MODEL", "claude-haiku-5-5")
ELEVENLABS_MODEL = os.getenv("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")
VOSK_MODEL_DIR = os.getenv("VOSK_MODEL_DIR", "vosk-model-small-en-us-0.15")
MIC_INDEX = int(os.getenv("JARVIS_MIC_INDEX", "-1"))

SAMPLE_RATE = 16000
COMMAND_TIMEOUT_S = 10      # max seconds to wait for a spoken question
MAX_TOKENS = 500
MAX_WEB_SEARCHES = 3        # caps search cost per question
MAX_PAUSE_TURNS = 3         # rounds allowed if a long search pauses
HISTORY_LIMIT = 20          # messages kept in memory

SYSTEM_PROMPT = (
    "You are Jarvis, a helpful voice assistant. Use web search when a question "
    "needs current information such as news, scores, prices, or weather. "
    "Keep answers short and conversational, since they will be read aloud. "
    "Do not use markdown, bullet points, or links."
)


def check_config():
    required = {
        "PICOVOICE_ACCESS_KEY": PICOVOICE_ACCESS_KEY,
        "ANTHROPIC_API_KEY": ANTHROPIC_API_KEY,
        "ELEVENLABS_API_KEY": ELEVENLABS_API_KEY,
        "ELEVENLABS_VOICE_ID": ELEVENLABS_VOICE_ID,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        log.error("Missing settings in .env: %s", ", ".join(missing))
        sys.exit(1)
    if not os.path.isdir(VOSK_MODEL_DIR):
        log.error("Speech model folder not found: %s. See the setup steps in the README.", VOSK_MODEL_DIR)
        sys.exit(1)


def speak(text):
    try:
        resp = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
            headers={"xi-api-key": ELEVENLABS_API_KEY, "Accept": "audio/mpeg"},
            json={"text": text, "model_id": ELEVENLABS_MODEL},
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException:
        log.exception("Text-to-speech request failed")
        return
    try:
        subprocess.run(["mpg123", "-q", "-"], input=resp.content, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired):
        log.exception("Audio playback failed")


def listen_for_command(recorder, stt, frame_length):
    rec = KaldiRecognizer(stt, SAMPLE_RATE)
    max_frames = int(COMMAND_TIMEOUT_S * SAMPLE_RATE / frame_length)
    for _ in range(max_frames):
        pcm = recorder.read()
        if rec.AcceptWaveform(array("h", pcm).tobytes()):
            return json.loads(rec.Result()).get("text", "").strip()
    return json.loads(rec.FinalResult()).get("text", "").strip()


def ask_claude(client, history, question):
    history.append({"role": "user", "content": question})
    messages = list(history)
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": MAX_WEB_SEARCHES}]

    try:
        for _ in range(MAX_PAUSE_TURNS):
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
                timeout=30,
            )
            if response.stop_reason != "pause_turn":
                break
            messages.append({"role": "assistant", "content": response.content})
    except anthropic.APIError:
        log.exception("Claude request failed")
        history.pop()
        return "Sorry, I'm having trouble reaching my brain right now."

    answer = " ".join(b.text for b in response.content if b.type == "text").strip()
    if not answer:
        history.pop()
        return "Sorry, I couldn't find an answer to that."

    history.append({"role": "assistant", "content": answer})
    while len(history) > HISTORY_LIMIT:
        del history[:2]
    return answer


def handle_sigterm(signum, frame):
    raise KeyboardInterrupt


def main():
    check_config()
    signal.signal(signal.SIGTERM, handle_sigterm)

    try:
        porcupine = pvporcupine.create(access_key=PICOVOICE_ACCESS_KEY, keywords=["jarvis"])
    except Exception:
        log.exception("Could not start the wake word engine. Check PICOVOICE_ACCESS_KEY.")
        sys.exit(1)

    recorder = None
    try:
        stt = Model(VOSK_MODEL_DIR)
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, max_retries=2)
        history = []

        recorder = PvRecorder(frame_length=porcupine.frame_length, device_index=MIC_INDEX)
        recorder.start()
        log.info("Jarvis is ready. Say 'Jarvis' to ask a question.")
        speak("Jarvis is ready.")

        while True:
            pcm = recorder.read()
            if porcupine.process(pcm) < 0:
                continue

            log.info("Wake word detected")
            speak("Yes?")
            question = listen_for_command(recorder, stt, porcupine.frame_length)
            if not question:
                speak("Sorry, I didn't catch that.")
                continue

            log.info("Question: %s", question)
            answer = ask_claude(client, history, question)
            log.info("Answer: %s", answer)
            speak(answer)
    except KeyboardInterrupt:
        log.info("Shutting down.")
    finally:
        if recorder is not None:
            recorder.stop()
            recorder.delete()
        porcupine.delete()


if __name__ == "__main__":
    main()