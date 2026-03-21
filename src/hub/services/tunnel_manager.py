"""Cloudflare Tunnel runtime management.

This module provides the TunnelManager class for managing the cloudflared subprocess
from within the GPTTalker hub's lifespan.
"""

import asyncio
import os
import signal
from typing import Any

from src.hub.config import HubConfig
from src.shared.logging import get_logger

logger = get_logger(__name__)


class TunnelManager:
    """Manages the Cloudflare Tunnel (cloudflared) subprocess.

    This class handles:
    - Starting cloudflared subprocess when tunnel is enabled
    - Health monitoring with automatic restart on failure
    - Systemd/service detection to avoid conflicting with external management
    - Graceful shutdown of the subprocess

    Attributes:
        config: Hub configuration with tunnel settings.
        _process: The asyncio subprocess instance (if managed by hub).
        _monitor_task: Background task for health monitoring.
        _is_external: Whether tunnel is managed externally (e.g., by systemd).
        _restart_count: Number of restart attempts made.
    """

    CLOUDFLARED_COMMAND = "cloudflared"

    def __init__(self, config: HubConfig) -> None:
        """Initialize the tunnel manager.

        Args:
            config: Hub configuration containing tunnel settings.
        """
        self.config = config
        self._process: asyncio.subprocess.Process | None = None
        self._monitor_task: asyncio.Task | None = None
        self._is_external = False
        self._restart_count = 0
        self._running = False

    @property
    def is_running(self) -> bool:
        """Check if the tunnel is currently running.

        Returns:
            True if the tunnel process is running, False otherwise.
        """
        return self._running

    async def start(self) -> bool:
        """Start the Cloudflare Tunnel subprocess if enabled.

        This method:
        1. Checks if tunnel is enabled in config
        2. Detects if cloudflared is already managed externally (systemd/process)
        3. Starts subprocess if not externally managed

        Returns:
            True if tunnel was started successfully or is externally managed,
            False if tunnel is disabled or failed to start.
        """
        # Check if tunnel is enabled
        if not self.config.cloudflare_tunnel_enabled:
            logger.info("cloudflare_tunnel_disabled")
            return False

        # Check for token
        token = self.config.cloudflare_tunnel_token
        if not token:
            logger.warning(
                "cloudflare_tunnel_enabled_but_no_token",
                message="Tunnel enabled but CLOUDFLARE_TUNNEL_TOKEN not set",
            )
            return False

        # Check if tunnel is externally managed (systemd or already running)
        if await self._check_external_management():
            if self._is_external:
                logger.info(
                    "cloudflare_tunnel_external_detected",
                    message="Tunnel appears to be managed externally (systemd or running process)",
                )
                self._running = True
                return True
            else:
                logger.warning(
                    "cloudflare_tunnel_check_failed",
                    message="Could not determine external tunnel status, proceeding with hub management",
                )

        # Start the tunnel subprocess
        try:
            return await self._start_subprocess()
        except Exception as e:
            logger.error(
                "cloudflare_tunnel_start_failed",
                error=str(e),
            )
            return False

    async def _check_external_management(self) -> bool:
        """Check if cloudflared is managed externally (systemd or running process).

        Returns:
            True if external management detected, False otherwise.
        """
        # Check if cloudflared process is already running
        try:
            proc = await asyncio.create_subprocess_exec(
                "pgrep",
                "-x",
                "cloudflared",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0 and stdout.strip():
                logger.info(
                    "cloudflare_tunnel_process_found",
                    message="cloudflared process already running",
                )
                self._is_external = True
                return True
        except FileNotFoundError:
            # pgrep not available, continue with other checks
            pass
        except Exception as e:
            logger.debug(
                "cloudflare_tunnel_pgrep_check_error",
                error=str(e),
            )

        # Check if systemd service is active
        try:
            proc = await asyncio.create_subprocess_exec(
                "systemctl",
                "is-active",
                "cloudflared",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0 and stdout.strip() == b"active":
                logger.info(
                    "cloudflare_tunnel_systemd_active",
                    message="cloudflared systemd service is active",
                )
                self._is_external = True
                return True
        except FileNotFoundError:
            # systemctl not available (not systemd), continue
            pass
        except Exception as e:
            logger.debug(
                "cloudflare_tunnel_systemd_check_error",
                error=str(e),
            )

        return False

    async def _start_subprocess(self) -> bool:
        """Start the cloudflared subprocess.

        Returns:
            True if subprocess started successfully, False otherwise.
        """
        logger.info(
            "cloudflare_tunnel_starting",
            token_present=bool(self.config.cloudflare_tunnel_token),
        )

        # Build environment with token
        env = os.environ.copy()
        env["CLOUDFLARE_TUNNEL_TOKEN"] = self.config.cloudflare_tunnel_token

        # Start cloudflared tunnel
        self._process = await asyncio.create_subprocess_exec(
            self.CLOUDFLARED_COMMAND,
            "tunnel",
            "--url",
            self.config.cloudflare_tunnel_url,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._running = True
        self._restart_count = 0

        logger.info(
            "cloudflare_tunnel_started",
            pid=self._process.pid,
        )

        # Start health monitoring
        self._monitor_task = asyncio.create_task(self._monitor_loop())

        return True

    async def _monitor_loop(self) -> None:
        """Background task for health monitoring and auto-restart.

        This task:
        1. Periodically checks if the tunnel process is alive
        2. Attempts restart on failure up to max_restarts times
        3. Logs failures but continues hub operation (fail-open)
        """
        while self._running:
            try:
                await asyncio.sleep(self.config.cloudflare_tunnel_health_check_interval)

                if not self._running:
                    break

                # Check if process is still running
                if self._process and self._process.returncode is not None:
                    logger.warning(
                        "cloudflare_tunnel_process_died",
                        exit_code=self._process.returncode,
                        restart_count=self._restart_count,
                    )
                    await self._restart()
                elif self._process is None and not self._is_external:
                    logger.warning(
                        "cloudflare_tunnel_process_missing",
                    )
                    await self._restart()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "cloudflare_tunnel_monitor_error",
                    error=str(e),
                )
                # Continue monitoring despite errors (fail-open)

    async def _restart(self) -> None:
        """Attempt to restart the tunnel process.

        If max_restarts is exceeded, logs an error but continues hub operation.
        """
        if self._is_external:
            return

        if self._restart_count >= self.config.cloudflare_tunnel_max_restarts:
            logger.error(
                "cloudflare_tunnel_max_restarts_exceeded",
                max_restarts=self.config.cloudflare_tunnel_max_restarts,
                message="Giving up on tunnel restart, hub will continue without tunnel",
            )
            self._running = False
            return

        self._restart_count += 1

        logger.info(
            "cloudflare_tunnel_restarting",
            attempt=self._restart_count,
            max_attempts=self.config.cloudflare_tunnel_max_restarts,
        )

        # Wait before restarting
        await asyncio.sleep(self.config.cloudflare_tunnel_restart_delay)

        try:
            await self._start_subprocess()
        except Exception as e:
            logger.error(
                "cloudflare_tunnel_restart_failed",
                error=str(e),
                attempt=self._restart_count,
            )

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the tunnel.

        Returns:
            Dictionary with health status information.
        """
        if not self.config.cloudflare_tunnel_enabled:
            return {
                "enabled": False,
                "running": False,
                "status": "disabled",
            }

        if self._is_external:
            return {
                "enabled": True,
                "running": self._running,
                "status": "external" if self._running else "external_not_running",
                "managed_by": "external",
            }

        if not self._running or self._process is None:
            return {
                "enabled": True,
                "running": False,
                "status": "not_running",
            }

        # Check process status
        if self._process.returncode is not None:
            return {
                "enabled": True,
                "running": False,
                "status": "crashed",
                "exit_code": self._process.returncode,
            }

        return {
            "enabled": True,
            "running": True,
            "status": "healthy",
            "pid": self._process.pid,
            "restart_count": self._restart_count,
        }

    async def stop(self) -> None:
        """Stop the tunnel subprocess gracefully.

        This method:
        1. Signals the process to stop (SIGTERM first, then SIGKILL)
        2. Waits for graceful shutdown
        3. Cancels the health monitoring task
        """
        self._running = False

        # Cancel monitoring task
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        # Don't stop externally managed tunnels
        if self._is_external:
            logger.info(
                "cloudflare_tunnel_external_skip_stop",
                message="Skipping stop for externally managed tunnel",
            )
            return

        # Stop the subprocess
        if self._process and self._process.returncode is None:
            logger.info(
                "cloudflare_tunnel_stopping",
                pid=self._process.pid,
            )

            try:
                # Send SIGTERM for graceful shutdown
                self._process.send_signal(signal.SIGTERM)

                # Wait for graceful shutdown with timeout
                try:
                    await asyncio.wait_for(
                        self._process.wait(),
                        timeout=10.0,
                    )
                    logger.info(
                        "cloudflare_tunnel_stopped_gracefully",
                        pid=self._process.pid,
                    )
                except asyncio.TimeoutError:
                    # Force kill if graceful shutdown fails
                    logger.warning(
                        "cloudflare_tunnel_force_kill",
                        pid=self._process.pid,
                    )
                    self._process.send_signal(signal.SIGKILL)
                    await self._process.wait()

            except Exception as e:
                logger.error(
                    "cloudflare_tunnel_stop_error",
                    error=str(e),
                )

        self._process = None
        logger.info("cloudflare_tunnel_stop_complete")
