"""Test script for Gmail MCP server OAuth flow."""

import asyncio
import webbrowser
from collections.abc import Awaitable, Callable
from typing import TypeVar

from dedalus_labs import AsyncDedalus, AuthenticationError, DedalusRunner
from dotenv import load_dotenv

load_dotenv()

T = TypeVar("T")


async def with_oauth_retry(fn: Callable[[], Awaitable[T]]) -> T:
    """Run async function, handling OAuth browser flow if needed."""
    try:
        return await fn()
    except AuthenticationError as e:
        if not (isinstance(e.body, dict) and (url := e.body.get("connect_url"))):
            raise
        print("\nOAuth required. Opening browser...")
        webbrowser.open(url)
        input("Press Enter after completing OAuth...")
        return await fn()


async def main():
    client = AsyncDedalus()
    runner = DedalusRunner(client)

    result = await with_oauth_retry(
        lambda: runner.run(
            input="List my recent emails and summarize them",
            model="openai/gpt-4.1",
            mcp_servers=["windsor/gmail-mcp"],
        )
    )

    print("\nResponse:")
    print("-" * 40)
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())
