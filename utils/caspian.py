import asyncio


async def _keep_typing(message, interval: int = 10):
    """Periodically triggers the typing indicator on the platform so it does not expire during long agent turns."""
    if not hasattr(message, "typing") or not callable(getattr(message, "typing", None)):
        return
    while True:
        try:
            message.typing()
        except Exception as e:
            print(f"typing() call failed: {e}")
        await asyncio.sleep(interval)
