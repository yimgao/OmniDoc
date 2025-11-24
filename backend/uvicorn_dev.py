"""Development entrypoint for running the FastAPI application with Uvicorn.

This helper keeps all FastAPI-related commands under the `backend/` directory
while continuing to load the application from the existing `src/` package.
"""
from __future__ import annotations

import asyncio
import os
from contextlib import suppress

import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def main() -> None:
    """Run the FastAPI app with autoreload for local development."""
    app_path = os.getenv("BACKEND_APP_PATH", "src.web.app:app")
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))

    config = uvicorn.Config(
        app_path,
        host=host,
        port=port,
        reload=True,
        reload_dirs=["backend/src"],
        log_level="info",
    )
    server = uvicorn.Server(config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(server.serve())
    finally:
        with suppress(Exception):
            loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == "__main__":
    main()

