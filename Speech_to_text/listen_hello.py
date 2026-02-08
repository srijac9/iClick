import asyncio
import json
import os
import pyaudio
import websockets

API_KEY = os.getenv("ELEVENLABS_API_KEY")
WS_URL = "wss://api.elevenlabs.io/v1/realtime?model=scribe_v2_realtime"

RATE = 16000
CHUNK = 1024

async def listen():
    async with websockets.connect(
        WS_URL,
        extra_headers={"xi-api-key": API_KEY}
    ) as ws:

        print("🎤 Connected. Speak now...")

        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=CHUNK)

        async def send_audio():
            while True:
                data = stream.read(CHUNK, exception_on_overflow=False)
                await ws.send(data)

        async def receive_text():
            while True:
                msg = await ws.recv()
                event = json.loads(msg)

                if "text" in event:
                    text = event["text"].lower()
                    print("Heard:", text)

                    if "hello" in text:
                        print("hi")

        await asyncio.gather(send_audio(), receive_text())

asyncio.run(listen())
