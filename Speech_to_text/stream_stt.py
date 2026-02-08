import asyncio
import base64
import json
import os
import subprocess
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
SILENCE_THRESHOLD = 0.02  # RMS threshold to detect silence (higher = more sensitive)
SILENCE_LIMIT = 2.0       # seconds of silence before auto-stop

# Type into focused window: set to False to only print in terminal
TYPE_INTO_FOCUSED = True


def _type_into_focused(text):
    """Type text into whatever window/field currently has focus (e.g. search bar)."""
    if not text or not _CAN_TYPE or not TYPE_INTO_FOCUSED:
        return
    try:
        # interval=0.02 so the target app keeps up; use interval=0 for speed if needed
        pyautogui.write(text, interval=0.02)
        return
    except Exception:
        pass
    # Fallback: use AppleScript to type (requires Accessibility permissions)
    try:
        escaped = text.replace('"', '\\"')
        subprocess.run(
            ["osascript", "-e", f'tell application "System Events" to keystroke "{escaped}"'],
            check=False,
        )
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


async def send_audio(ws, closing_flag):
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

        # Auto-stop on silence
        if silence_time >= SILENCE_LIMIT:
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

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype=DTYPE,
        blocksize=CHUNK_SAMPLES,
        callback=callback,
    ):
        mode = "terminal + type into focused field" if (_CAN_TYPE and TYPE_INTO_FOCUSED) else "terminal only"
        print(f"🎙️ Listening… ({mode}, auto-stop on {SILENCE_LIMIT}s silence)")
        if _CAN_TYPE and TYPE_INTO_FOCUSED:
            print("   Speak — text will be typed where your cursor is.")
            print("   👆 Click into a text field (e.g. search bar) first.")
            print("   (On macOS: grant Accessibility access to Terminal/Python if typing doesn't work.)")
            print("   Starting in 2s…")
            await asyncio.sleep(2)  # give time to focus the target field
        while not closing_flag.is_set():
            await asyncio.sleep(0.1)

# =====================
# Receiver — live transcript display
# Gradium uses "text" (recognized words) and "end_text" (end of phrase)
# =====================
async def receive_text(ws):
    transcript = []
    current_phrase = []  # Words in current phrase
    last_line_len = 0
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
            pad = " " * max(0, last_line_len - len(full_line))
            last_line_len = len(full_line)
            print(f"\r🗣️ {full_line}{pad}", end="", flush=True)

        elif msg_type == "end_text":
            # End of phrase: commit to transcript, print, and maybe type into focused field
            if current_phrase:
                new_phrase = " ".join(current_phrase)
                transcript.append(new_phrase)
                print(f"\r📝 {new_phrase}")  # overwrite partial line with final phrase
                print()  # newline so next partial has its own line
                # Type into focused field immediately
                if new_phrase:
                    _type_into_focused(new_phrase + " ")
                current_phrase = []
            last_line_len = 0

# =====================
# Main
# =====================
async def main():
    closing_flag = asyncio.Event()
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
                send_audio(ws, closing_flag),
                receive_text(ws)
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
