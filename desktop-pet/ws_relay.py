import asyncio
import websockets

HOST = "127.0.0.1"
PORT = 8765

pet_clients = set()

async def pet_handler(ws):
    print("[relay] pet connected")
    pet_clients.add(ws)
    try:
        async for msg in ws:
            print("[relay] got from pet:", msg)
    except Exception as e:
        print("[relay] pet error:", repr(e))
    finally:
        pet_clients.discard(ws)
        print("[relay] pet disconnected")

async def ctrl_handler(ws):
    print("[relay] ctrl connected")
    try:
        async for msg in ws:
            print("[relay] got from ctrl:", msg)
            if pet_clients:
                await asyncio.gather(*(c.send(msg) for c in list(pet_clients)), return_exceptions=True)
                print("[relay] forwarded to", len(pet_clients), "pet client(s)")
            else:
                print("[relay] no pet clients connected yet")
    except Exception as e:
        print("[relay] ctrl error:", repr(e))
    finally:
        print("[relay] ctrl disconnected")

async def router(ws):
    path = ws.request.path
    if path == "/pet":
        await pet_handler(ws)
    else:
        await ctrl_handler(ws)

async def main():
    async with websockets.serve(router, HOST, PORT):
        print(f"WS relay running at ws://{HOST}:{PORT}")
        print(" Godot connects to ws://127.0.0.1:8765/pet")
        print(" app_controller connects to ws://127.0.0.1:8765/ctrl")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
