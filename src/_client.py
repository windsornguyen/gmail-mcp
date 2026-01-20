# Copyright (c) 2026 Dedalus Labs, Inc. and its contributors
# SPDX-License-Identifier: MIT

"""Sample MCP client demonstrating OAuth browser flow for Gmail.

Environment variables:
    DEDALUS_API_KEY: Your Dedalus API key (dsk_*)
    DEDALUS_API_URL: Product API base URL
    DEDALUS_AS_URL: Authorization server URL
"""

import asyncio
import os
import webbrowser
from collections.abc import Awaitable, Callable
from typing import TypeVar

from dotenv import load_dotenv

load_dotenv()

from dedalus_labs import AsyncDedalus, AuthenticationError, DedalusRunner  # noqa: E402


class MissingEnvError(ValueError):
    """Required environment variable not set."""


def get_env(key: str) -> str:
    """Get required env var or raise."""
    val = os.getenv(key)
    if not val:
        raise MissingEnvError(key)
    return val


API_URL = get_env("DEDALUS_API_URL")
AS_URL = get_env("DEDALUS_AS_URL")
DEDALUS_API_KEY = os.getenv("DEDALUS_API_KEY")

# Debug: print env vars
print("=== Environment ===")
print(f"  DEDALUS_API_URL: {API_URL}")
print(f"  DEDALUS_AS_URL: {AS_URL}")
print(f"  DEDALUS_API_KEY: {DEDALUS_API_KEY[:20]}..." if DEDALUS_API_KEY else "  DEDALUS_API_KEY: None")

T = TypeVar("T")


async def with_oauth_retry(fn: Callable[[], Awaitable[T]]) -> T:
    """Run async function, handling OAuth browser flow if needed."""
    try:
        return await fn()
    except AuthenticationError as e:
        # connect_url may be at top level or nested under 'detail'
        body = e.body if isinstance(e.body, dict) else {}
        url = body.get("connect_url") or body.get("detail", {}).get("connect_url")
        if not url:
            raise
        print("\n" + "=" * 60)
        print("OAuth required. Opening browser...")
        print(f"\nConnect URL: {url}")
        print("\nRedirect URI (add to Google Cloud Console):")
        print("  https://admin.api.dedaluslabs.ai/v1/oauth/callback\n")
        print("=" * 60)
        webbrowser.open(url)
        input("Press Enter after completing OAuth...")
        return await fn()


async def run_with_runner() -> None:
    """Demo using DedalusRunner (handles multi-turn, aggregates results)."""
    client = AsyncDedalus(api_key=DEDALUS_API_KEY, base_url=API_URL, as_base_url=AS_URL)
    runner = DedalusRunner(client)

    result = await with_oauth_retry(
        lambda: runner.run(
            input="List my recent emails and summarize them",
            model="openai/gpt-4.1",
            mcp_servers=["windsor/gmail-mcp"],
        )
    )

    print("=== Model Output ===")
    print(result.output)

    if result.mcp_results:
        print("\n=== MCP Tool Results ===")
        for r in result.mcp_results:
            print(f"  {r.tool_name} ({r.duration_ms}ms): {str(r.result)[:200]}")


async def run_raw() -> None:
    """Demo using raw client (single request, full control)."""
    client = AsyncDedalus(api_key=DEDALUS_API_KEY, base_url=API_URL, as_base_url=AS_URL)

    async def do_request():
        return await client.chat.completions.create(
            model="openai/gpt-4.1",
            messages=[
                {
                    "role": "user",
                    "content": "List my recent emails and summarize them",
                }
            ],
            mcp_servers=["windsor/gmail-mcp"],
        )

    resp = await with_oauth_retry(do_request)

    print("=== Model Output ===")
    print(resp.choices[0].message.content)

    if resp.mcp_tool_results:
        print("\n=== MCP Tool Results ===")
        for r in resp.mcp_tool_results:
            print(f"  {r.tool_name} ({r.duration_ms}ms): {str(r.result)[:200]}")


async def main() -> None:
    """Run both demo modes."""
    print("=" * 60)
    print("DedalusRunner")
    print("=" * 60)
    await run_with_runner()

    print("\n" + "=" * 60)
    print("Raw Client")
    print("=" * 60)
    await run_raw()


if __name__ == "__main__":
    asyncio.run(main())
