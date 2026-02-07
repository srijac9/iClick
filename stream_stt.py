import asyncio
import base64
import json
import os
import sys
import numpy as np
import sounddevice as sd
from dotenv import load_dotenv
from websockets.legacy.client import connect

# Optional: type transcribed text into the focused window (e.g. search bar, text field)
try:
    import pyautogui
    _CAN_TYPE = True
except ImportError:
    _CAN_TYPE = False

# =====================
# Config
# =====================
load_dotenv()

API_KEY = os.getenv("GRADIUM_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GRADIUM_API_KEY not found")

WS_URL = "wss://eu.api.gradium.ai/api/speech/asr"

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"
CHUNK_MS = 80
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_MS / 1000)
SILENCE_THRESHOLD = 0.01  # RMS threshold to detect silence
SILENCE_LIMIT = 2.0       # seconds of silence before auto-stop

# Type into focused window: set to False to only print in terminal
TYPE_INTO_FOCUSED = True

# Only start typing into focused field after this wake word is said (case-insensitive)
WAKE_WORD = "hey buddy"


def _normalize(text):
    """Lowercase and collapse spaces for wake-word matching."""
    return " ".join((text or "").lower().split())


def _strip_wake_word_from_start(phrase):
    """If phrase starts with the wake word, return the rest; else return phrase."""
    n = _normalize(phrase)
    if n.startswith(WAKE_WORD):
        return n[len(WAKE_WORD):].strip()
    return phrase


def _type_into_focused(text):
    """Type text into whatever window/field currently has focus (e.g. search bar)."""
    if not text or not _CAN_TYPE or not TYPE_INTO_FOCUSED:
        return
    try:
        # interval=0.02 so the target app keeps up; use interval=0 for speed if needed
        pyautogui.write(text, interval=0.02)
    except Exception:
        pass

print("🔑 API key loaded")
if not _CAN_TYPE and TYPE_INTO_FOCUSED:
    print("   (Install pyautogui to type into focused field: pip install pyautogui)")
print("🌐 Connecting to Gradium…")

# =====================
# Audio sender
# =====================
def _consume_future_exception(future):
    """Consume exception from Future to avoid 'Task exception never retrieved'."""
    try:
        future.result()
    except (asyncio.CancelledError, Exception):
        pass


async def send_audio(ws, closing_flag, wake_word_said):
    loop = asyncio.get_running_loop()
    silence_time = 0.0

    def callback(indata, frames, time, status):
        nonlocal silence_time
        if status:
            print("⚠️", status)

        if closing_flag.is_set():
            return

        rms = np.sqrt(np.mean(indata**2))
        if rms < SILENCE_THRESHOLD:
            silence_time += CHUNK_MS / 1000
        else:
            silence_time = 0.0

        # Auto-stop on silence only after the wake word has been said
        if silence_time >= SILENCE_LIMIT and wake_word_said.is_set():
            closing_flag.set()
            close_future = asyncio.run_coroutine_threadsafe(ws.close(), loop)
            close_future.add_done_callback(_consume_future_exception)
            return

        # Gradium expects JSON with base64-encoded PCM
        pcm16 = (indata * 32767).astype(np.int16).tobytes()
        audio_b64 = base64.b64encode(pcm16).decode("ascii")
        msg = json.dumps({"type": "audio", "audio": audio_b64})

        future = asyncio.run_coroutine_threadsafe(ws.send(msg), loop)
        future.add_done_callback(_consume_future_exception)

    while not closing_flag.is_set():
        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=CHUNK_SAMPLES,
                callback=callback,
            ):
                mode = "terminal + type into focused field" if (_CAN_TYPE and TYPE_INTO_FOCUSED) else "terminal only"
                print(f"🎙️ Listening… ({mode}, auto-stop on {SILENCE_LIMIT}s silence after \"{WAKE_WORD.title()}\")")
                if _CAN_TYPE and TYPE_INTO_FOCUSED:
                    print(f"   Say \"{WAKE_WORD.title()}\" then speak — text will be typed where your cursor is.")
                    print("   👆 Click into a text field (e.g. search bar) first.")
                    print("   (On macOS: grant Accessibility access to Terminal/Python if typing doesn't work.)")
                    print("   Starting in 2s…")
                    await asyncio.sleep(2)  # give time to focus the target field
                while not closing_flag.is_set():
                    await asyncio.sleep(0.1)
        except Exception as e:
            print(f"❌ Audio input error: {e}")
            await asyncio.sleep(1.0)

# =====================
# Receiver — live transcript display
# Gradium uses "text" (recognized words) and "end_text" (end of phrase)
# =====================
async def receive_text(ws, wake_word_said):
    transcript = []
    current_phrase = []  # Words in current phrase
    last_line_len = 0
    wake_word_detected = False  # Only type into focused field after "Hey, buddy"

    async for message in ws:
        raw = message if isinstance(message, str) else message.decode("utf-8", errors="ignore")
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue

        msg_type = data.get("type")
        text = data.get("text", "").strip()

        if msg_type == "text" and text:
            # Live transcript: each word/phrase as it's recognized
            current_phrase.append(text)
            full_line = " ".join(transcript) + (" " if transcript else "") + " ".join(current_phrase)
            if not wake_word_detected and WAKE_WORD in _normalize(full_line):
                wake_word_detected = True
                wake_word_said.set()  # Allow auto-stop on silence from now on
            pad = " " * max(0, last_line_len - len(full_line))
            last_line_len = len(full_line)
            print(f"\r🗣️ {full_line}{pad}", end="", flush=True)

        elif msg_type == "end_text":
            # End of phrase: commit to transcript, print, and maybe type into focused field
            if current_phrase:
                new_phrase = " ".join(current_phrase)
                if not wake_word_detected and WAKE_WORD in _normalize(new_phrase):
                    wake_word_detected = True
                    wake_word_said.set()  # Allow auto-stop on silence from now on
                transcript.append(new_phrase)
                print(f"\r📝 {new_phrase}")  # overwrite partial line with final phrase
                print()  # newline so next partial has its own line
                # Type into focused field only after wake word; don't type the wake word itself
                if wake_word_detected:
                    to_type = _strip_wake_word_from_start(new_phrase)
                    if to_type:
                        _type_into_focused(to_type + " ")
                current_phrase = []
            last_line_len = 0

# =====================
# Main
# =====================
async def main():
    closing_flag = asyncio.Event()
    wake_word_said = asyncio.Event()  # Set when "Hey, buddy" is heard; enables auto-stop on silence

    async with connect(
        WS_URL,
        extra_headers=[("x-api-key", API_KEY)],
        ping_interval=None,
        open_timeout=20,
    ) as ws:

        print("✅ Connected to Gradium")

        # Send setup (Gradium expects model_name, input_format, json_config)
        await ws.send(json.dumps({
            "type": "setup",
            "model_name": "default",
            "input_format": "pcm",
            "json_config": {"language": "en"}
        }))

        # Run sender and receiver concurrently
        try:
            await asyncio.gather(
                send_audio(ws, closing_flag, wake_word_said),
                receive_text(ws, wake_word_said)
            )
        except Exception:
            pass  # Connection closed (e.g. after silence) — exit cleanly

# =====================
# Entry
# =====================
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Stopped cleanly")
    except Exception as e:
        print("\n❌ Error:", e)
        sys.exit(1)
