import os
import asyncio
from contextlib import asynccontextmanager
from fastmcp import FastMCP
from agents.mcp import MCPServerStreamableHttp

mcp = FastMCP("") # noqa


@asynccontextmanager
async def _connect_mcp_servers(pairing_code: str = ""):
    asha_url = os.getenv("ASHA_MCP")
    asha_cm = None
    servers = []
    headers = {}
    if pairing_code:
        headers["X-Pairing-Code"] = pairing_code

    if asha_url:
        for attempt in range(2):
            try:
                asha_cm = MCPServerStreamableHttp(
                    params={"url": asha_url, "headers": headers},
                    name="ASHA",
                    client_session_timeout_seconds=25,
                    max_retry_attempts=3,
                )
                asha_server = await asyncio.wait_for(asha_cm.__aenter__(), timeout=25.0) # noqa
                servers.append(asha_server)
                break
            except Exception as e:
                print(f"ASHA_MCP connection attempt {attempt + 1} failed: {e}") # noqa
                asha_cm = None
                if attempt == 0:
                    await asyncio.sleep(2.0)

    try:
        yield servers
    finally:
        if asha_cm:
            try:
                await asha_cm.__aexit__(None, None, None)
            except Exception:
                pass
