import asyncio
import base64
import json
import os
import threading
import time
import pyaudio
import websockets
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not API_KEY:
    raise RuntimeError("ELEVENLABS_API_KEY is not set")

MODEL_ID = "scribe_v2_realtime"
WS_URL = (
    "wss://api.elevenlabs.io/v1/speech-to-text/realtime"
    f"?model_id={MODEL_ID}&commit_strategy=vad"
)

RATE = 16000
CHUNK = 1024

async def listen_for_keyword_async(stop_event: threading.Event, trigger_event: threading.Event, keyword: str = "hey buddy"):
    async with websockets.connect(
        WS_URL,
        extra_headers={"xi-api-key": API_KEY}
    ) as ws:
        print("✅ Voice listener connected")

        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )

        print(f"🎤 Listening... say '{keyword}'")

        async def send_audio():
            while not stop_event.is_set():
                data = stream.read(CHUNK, exception_on_overflow=False)
                audio_b64 = base64.b64encode(data).decode("ascii")
                msg = {
                    "message_type": "input_audio_chunk",
                    "audio_base_64": audio_b64,
                    "sample_rate": RATE,
                }
                await ws.send(json.dumps(msg))

        async def receive_text():
            while not stop_event.is_set():
                raw = await ws.recv()
                event = json.loads(raw)
                msg_type = event.get("message_type")
                if msg_type in ("partial_transcript", "committed_transcript"):
                    text = (event.get("text") or "").lower()
                    if text:
                        if keyword in text:
                            trigger_event.set()

        await asyncio.gather(send_audio(), receive_text())


def listen_for_keyword(stop_event: threading.Event, trigger_event: threading.Event, keyword: str = "hey buddy"):
    while not stop_event.is_set():
        try:
            asyncio.run(listen_for_keyword_async(stop_event, trigger_event, keyword))
        except Exception:
            time.sleep(1.0)
