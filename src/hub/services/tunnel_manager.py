"""ngrok runtime management for GPTTalker's public edge."""

import asyncio
import os
import signal
from typing import Any

from src.hub.config import HubConfig
from src.shared.logging import get_logger

logger = get_logger(__name__)


class TunnelManager:
    """Manage the ngrok subprocess used for GPTTalker's public HTTPS edge."""

    NGROK_COMMAND = "ngrok"

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
        """Start the ngrok subprocess if enabled or detect external management."""
        if not self.config.ngrok_enabled:
            logger.info("ngrok_tunnel_disabled")
            return False

        if await self._check_external_management():
            if self._is_external:
                logger.info(
                    "ngrok_tunnel_external_detected",
                    message="ngrok appears to be managed externally (systemd or running process)",
                )
                self._running = True
                return True

            logger.warning(
                "ngrok_tunnel_check_failed",
                message="Could not determine external ngrok status, proceeding with hub management",
            )

        if not self.config.ngrok_authtoken:
            logger.warning(
                "ngrok_tunnel_enabled_but_no_authtoken",
                message="ngrok enabled but GPTTALKER_NGROK_AUTHTOKEN not set for hub-managed mode",
            )
            return False

        try:
            return await self._start_subprocess()
        except Exception as e:
            logger.error(
                "ngrok_tunnel_start_failed",
                error=str(e),
            )
            return False

    async def _check_external_management(self) -> bool:
        """Check whether ngrok is already managed externally."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "pgrep",
                "-x",
                self.NGROK_COMMAND,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0 and stdout.strip():
                logger.info(
                    "ngrok_tunnel_process_found",
                    message="ngrok process already running",
                )
                self._is_external = True
                return True
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.debug(
                "ngrok_tunnel_pgrep_check_error",
                error=str(e),
            )

        try:
            proc = await asyncio.create_subprocess_exec(
                "systemctl",
                "is-active",
                self.NGROK_COMMAND,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0 and stdout.strip() == b"active":
                logger.info(
                    "ngrok_tunnel_systemd_active",
                    message="ngrok systemd service is active",
                )
                self._is_external = True
                return True
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.debug(
                "ngrok_tunnel_systemd_check_error",
                error=str(e),
            )

        return False

    def _build_command(self) -> list[str]:
        """Build the ngrok CLI command for hub-managed mode."""
        command = [
            self.NGROK_COMMAND,
            "http",
            self.config.ngrok_forward_url,
            "--authtoken",
            self.config.ngrok_authtoken,
        ]
        if self.config.ngrok_public_url:
            command.extend(["--url", self.config.ngrok_public_url])
        return command

    async def _start_subprocess(self) -> bool:
        """Start the ngrok subprocess."""
        logger.info(
            "ngrok_tunnel_starting",
            authtoken_present=bool(self.config.ngrok_authtoken),
            public_url=self.config.ngrok_public_url,
            forward_url=self.config.ngrok_forward_url,
        )

        command = self._build_command()

        self._process = await asyncio.create_subprocess_exec(
            *command,
            env=os.environ.copy(),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._running = True
        self._restart_count = 0

        logger.info(
            "ngrok_tunnel_started",
            pid=self._process.pid,
        )

        self._monitor_task = asyncio.create_task(self._monitor_loop())
        return True

    async def _monitor_loop(self) -> None:
        """Monitor the ngrok subprocess and restart it on failure."""
        while self._running:
            try:
                await asyncio.sleep(self.config.ngrok_health_check_interval)

                if not self._running:
                    break

                if self._process and self._process.returncode is not None:
                    logger.warning(
                        "ngrok_tunnel_process_died",
                        exit_code=self._process.returncode,
                        restart_count=self._restart_count,
                    )
                    await self._restart()
                elif self._process is None and not self._is_external:
                    logger.warning(
                        "ngrok_tunnel_process_missing",
                    )
                    await self._restart()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "ngrok_tunnel_monitor_error",
                    error=str(e),
                )

    async def _restart(self) -> None:
        """Attempt to restart the ngrok process."""
        if self._is_external:
            return

        if self._restart_count >= self.config.ngrok_max_restarts:
            logger.error(
                "ngrok_tunnel_max_restarts_exceeded",
                max_restarts=self.config.ngrok_max_restarts,
                message="Giving up on ngrok restart, hub will continue without the public edge",
            )
            self._running = False
            return

        self._restart_count += 1

        logger.info(
            "ngrok_tunnel_restarting",
            attempt=self._restart_count,
            max_attempts=self.config.ngrok_max_restarts,
        )

        await asyncio.sleep(self.config.ngrok_restart_delay)

        try:
            await self._start_subprocess()
        except Exception as e:
            logger.error(
                "ngrok_tunnel_restart_failed",
                error=str(e),
                attempt=self._restart_count,
            )

    async def health_check(self) -> dict[str, Any]:
        """Check the health of the configured public-edge process."""
        if not self.config.ngrok_enabled:
            return {
                "enabled": False,
                "running": False,
                "status": "disabled",
                "provider": "ngrok",
            }

        if self._is_external:
            return {
                "enabled": True,
                "running": self._running,
                "status": "external" if self._running else "external_not_running",
                "managed_by": "external",
                "provider": "ngrok",
            }

        if not self._running or self._process is None:
            return {
                "enabled": True,
                "running": False,
                "status": "not_running",
                "provider": "ngrok",
            }

        if self._process.returncode is not None:
            return {
                "enabled": True,
                "running": False,
                "status": "crashed",
                "exit_code": self._process.returncode,
                "provider": "ngrok",
            }

        return {
            "enabled": True,
            "running": True,
            "status": "healthy",
            "pid": self._process.pid,
            "restart_count": self._restart_count,
            "provider": "ngrok",
        }

    async def stop(self) -> None:
        """Stop the ngrok subprocess gracefully."""
        self._running = False

        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        if self._is_external:
            logger.info(
                "ngrok_tunnel_external_skip_stop",
                message="Skipping stop for externally managed ngrok",
            )
            return

        if self._process and self._process.returncode is None:
            logger.info(
                "ngrok_tunnel_stopping",
                pid=self._process.pid,
            )

            try:
                self._process.send_signal(signal.SIGTERM)
                try:
                    await asyncio.wait_for(
                        self._process.wait(),
                        timeout=10.0,
                    )
                    logger.info(
                        "ngrok_tunnel_stopped_gracefully",
                        pid=self._process.pid,
                    )
                except TimeoutError:
                    logger.warning(
                        "ngrok_tunnel_force_kill",
                        pid=self._process.pid,
                    )
                    self._process.send_signal(signal.SIGKILL)
                    await self._process.wait()

            except Exception as e:
                logger.error(
                    "ngrok_tunnel_stop_error",
                    error=str(e),
                )

        self._process = None
        logger.info("ngrok_tunnel_stop_complete")
