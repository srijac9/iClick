import asyncio
import base64
import json
import os
import urllib.error
import urllib.request
import pyaudio
import time
import websockets
from websockets.exceptions import ConnectionClosed
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise RuntimeError("ELEVENLABS_API_KEY not set")

MODEL_ID = "scribe_v2_realtime"
BASE_WS_URL = "wss://api.elevenlabs.io/v1/speech-to-text/realtime"
TOKEN_URL = "https://api.elevenlabs.io/v1/single-use-token/realtime_scribe"


def _create_single_use_token():
    req = urllib.request.Request(
        TOKEN_URL,
        method="POST",
        headers={"xi-api-key": API_KEY},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(
            f"Token request failed: HTTP {exc.code}. "
            f"Response: {body}"
        ) from exc
    token = data.get("token")
    if not token:
        raise RuntimeError(f"Failed to create token: {data}")
    return token

RATE = 16000
CHUNK = 1024
SILENCE_LIMIT = 2.0  # seconds without transcript updates before auto-stop

async def main():
    while True:
        try:
            token = _create_single_use_token()
            ws_url = (
                f"{BASE_WS_URL}?model_id={MODEL_ID}"
                "&commit_strategy=vad"
                "&audio_format=pcm_16000"
                "&language_code=en"
                f"&token={token}"
            )
            async with websockets.connect(
                ws_url,
                extra_headers=[("xi-api-key", API_KEY)],
                ping_interval=10,
                ping_timeout=10,
            ) as ws:
                print("✅ Connected to ElevenLabs", flush=True)

                state = {
                    "last_text_time": time.time(),
                    "had_text": False,
                    "last_committed": None,
                }

                audio = pyaudio.PyAudio()
                stream = audio.open(
                    format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK,
                )

                print("🎙️ Listening...", flush=True)

                async def send_audio():
                    while True:
                        data = await asyncio.to_thread(
                            stream.read,
                            CHUNK,
                            exception_on_overflow=False,
                        )
                        audio_b64 = base64.b64encode(data).decode("ascii")
                        msg = {
                            "message_type": "input_audio_chunk",
                            "audio_base_64": audio_b64,
                            "sample_rate": RATE,
                        }
                        await ws.send(json.dumps(msg))

                async def receive_text():
                    while True:
                        raw = await ws.recv()
                        event = json.loads(raw)
                        msg_type = event.get("message_type")
                        if msg_type == "session_started":
                            print(f"ℹ️ session_started: {event.get('session_id')}", flush=True)
                            continue
                        if msg_type in ("partial_transcript", "committed_transcript"):
                            text = (event.get("text") or "").strip()
                            if text:
                                state["last_text_time"] = time.time()
                                state["had_text"] = True
                                if msg_type == "partial_transcript":
                                    print(f"📝 {text}", flush=True)
                                else:
                                    state["last_committed"] = text
                                    print(f"🗣️ {text}", flush=True)
                            continue
                        # Surface any errors or unexpected messages
                        if msg_type and "error" in msg_type:
                            print(f"❌ {msg_type}: {event}", flush=True)
                        else:
                            print(f"ℹ️ event: {event}", flush=True)

                async def silence_watchdog():
                    while True:
                        await asyncio.sleep(0.1)
                        if state["had_text"] and (time.time() - state["last_text_time"]) >= SILENCE_LIMIT:
                            print(f"⏹️ Auto-stop after {SILENCE_LIMIT:.1f}s silence", flush=True)
                            await ws.close()
                            return

                await asyncio.gather(send_audio(), receive_text(), silence_watchdog())
        except ConnectionClosed:
            print("⚠️ Connection closed, reconnecting...")
            await asyncio.sleep(1.0)

if __name__ == "__main__":
    asyncio.run(main())
