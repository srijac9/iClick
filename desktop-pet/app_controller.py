import asyncio
import json
import websockets
import ctypes

WS_URL = "ws://127.0.0.1:8765/ctrl"

async def send(cmd: dict):
    async with websockets.connect(WS_URL) as ws:
        await ws.send(json.dumps(cmd))

def compute_bottom_right(win_w=520, win_h=520, margin=24):
    user32 = ctypes.windll.user32
    screen_w = user32.GetSystemMetrics(0)
    screen_h = user32.GetSystemMetrics(1)
    x = screen_w - win_w - margin
    y = screen_h - win_h - margin
    return x, y

async def demo():
    await send({"type": "bottom_right", "margin": 24})
    await send({"type": "set_speed", "vx": 1.2})
    await asyncio.sleep(2)
    await send({"type": "set_speed", "vx": -1.2})
    await asyncio.sleep(2)
    await send({"type": "set_speed", "vx": 0.0})
    await send({"type": "do", "action": "idle"})

if __name__ == "__main__":
    asyncio.run(demo())
