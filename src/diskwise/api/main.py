"""Command line entry point for the local DiskWise API."""

from __future__ import annotations

from diskwise.api.app import create_app

app = create_app()


def main() -> None:
    """Run the local API on the loopback interface only."""
    import uvicorn

    uvicorn.run(
        "diskwise.api.main:app",
        host="127.0.0.1",
        port=8765,
        reload=False,
    )


if __name__ == "__main__":
    main()
