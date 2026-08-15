import os
import asyncio
from contextlib import asynccontextmanager
from fastmcp import FastMCP
from agents.mcp import MCPServerStreamableHttp

mcp = FastMCP("caspier as an mcp. This mcp is used to send messages via telegram and Discord to users") # noqa


@asynccontextmanager
async def _connect_mcp_servers():
    asha_url = os.getenv("ASHA_MCP")
    asha_cm = None
    servers = []
    if asha_url:
        try:
            asha_cm = MCPServerStreamableHttp(
                params={"url": asha_url},
                name="ASHA",
                client_session_timeout_seconds=5,
                max_retry_attempts=1,
            )
            asha_server = await asyncio.wait_for(asha_cm.__aenter__(), timeout=5.0) # noqa
            servers.append(asha_server)
        except Exception as e:
            print(f"ASHA_MCP connection failed, continuing without ASHA tools: {e}") # noqa
            asha_cm = None
    try:
        yield servers
    finally:
        if asha_cm:
            try:
                await asha_cm.__aexit__(None, None, None)
            except Exception:
                pass
