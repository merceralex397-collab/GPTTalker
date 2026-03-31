from types import SimpleNamespace

import pytest

from src.hub.services.tunnel_manager import TunnelManager


def make_config(**overrides: object) -> SimpleNamespace:
    config = {
        "ngrok_enabled": False,
        "ngrok_authtoken": None,
        "ngrok_public_url": None,
        "ngrok_forward_url": "http://localhost:8000",
        "ngrok_health_check_interval": 30,
        "ngrok_restart_delay": 5,
        "ngrok_max_restarts": 5,
    }
    config.update(overrides)
    return SimpleNamespace(**config)


def test_build_command_uses_public_url_when_present() -> None:
    manager = TunnelManager(
        make_config(
            ngrok_enabled=True,
            ngrok_authtoken="token-123",
            ngrok_public_url="https://gpttalker.ngrok.app",
        )
    )

    assert manager._build_command() == [
        "ngrok",
        "http",
        "http://localhost:8000",
        "--authtoken",
        "token-123",
        "--url",
        "https://gpttalker.ngrok.app",
    ]


def test_build_command_omits_public_url_when_not_configured() -> None:
    manager = TunnelManager(
        make_config(
            ngrok_enabled=True,
            ngrok_authtoken="token-123",
        )
    )

    assert manager._build_command() == [
        "ngrok",
        "http",
        "http://localhost:8000",
        "--authtoken",
        "token-123",
    ]


@pytest.mark.asyncio
async def test_health_check_reports_disabled_state() -> None:
    manager = TunnelManager(make_config())

    health = await manager.health_check()

    assert health == {
        "enabled": False,
        "running": False,
        "status": "disabled",
        "provider": "ngrok",
    }


@pytest.mark.asyncio
async def test_health_check_reports_external_management() -> None:
    manager = TunnelManager(make_config(ngrok_enabled=True))
    manager._is_external = True
    manager._running = True

    health = await manager.health_check()

    assert health == {
        "enabled": True,
        "running": True,
        "status": "external",
        "managed_by": "external",
        "provider": "ngrok",
    }
