"""Node agent service entrypoint."""

import asyncio


async def main() -> None:
    """
    Main entrypoint for the node agent service.

    This async function starts the node agent, registers handlers,
    and begins listening for commands from the hub.
    """
    print("GPTTalker Node Agent starting...")

    # TODO(CORE-003): Initialize config, logging, and health endpoint
    # TODO(CORE-003): Set up Tailscale connectivity to hub
    # TODO(CORE-003): Register bounded executor for local operations

    # Placeholder for running service
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("Node Agent shutting down...")


def run() -> None:
    """Run the node agent service."""
    asyncio.run(main())


# TODO(CORE-003): Add health endpoint at /health
# TODO(CORE-003): Add operation handlers: list_dir, read_file, search, git_status
