import asyncio


async def _keep_typing(message, interval: float = 4.0):
    try:
        while True:
            if hasattr(message, "send_typing"):
                await message.send_typing()
            await asyncio.sleep(interval)
    except asyncio.CancelledError:
        pass
