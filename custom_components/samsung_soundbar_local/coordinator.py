"""Coordinate core state and optional model-specific features."""

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import SoundbarAPI, SoundbarAPIError, SoundbarUnsupportedError
from .const import DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)
type SoundbarConfigEntry = ConfigEntry[SoundbarCoordinator]


class SoundbarCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Maintain state without making optional commands a setup dependency."""

    def __init__(self, hass: HomeAssistant, entry: SoundbarConfigEntry) -> None:
        settings = {**entry.data, **entry.options}
        self.api = SoundbarAPI(
            settings[CONF_HOST],
            async_get_clientsession(hass),
            settings.get(CONF_PORT, DEFAULT_PORT),
        )
        self._unsupported: set[str] = set()
        self._optional_retry_at: dict[str, float] = {}
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            connections={(CONNECTION_NETWORK_MAC, entry.unique_id)},
            name=entry.title,
            manufacturer="Samsung",
            model=entry.data.get("model", entry.title),
            sw_version=entry.data.get("version"),
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="Samsung Soundbar",
            update_interval=timedelta(
                seconds=settings.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            ),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            power = await self.api.get_power() == "1"
            if not power:
                return {"power": False}
            data = {
                "power": True,
                "volume": await self.api.get_volume(),
                "mute": await self.api.get_mute() == "on",
                "source": await self.api.get_input(),
            }
        except SoundbarAPIError as err:
            raise UpdateFailed(str(err)) from err
        for key, getter in (
            ("sound_mode", self.api.get_sound_mode),
            ("woofer_level", self.api.get_woofer_level),
            ("eq_mode", self.api.get_eq_mode),
        ):
            data[key] = None
            if (
                key in self._unsupported
                or self.hass.loop.time() < self._optional_retry_at.get(key, 0)
            ):
                continue
            try:
                data[key] = await getter()
            except SoundbarUnsupportedError:
                self._unsupported.add(key)
            except SoundbarAPIError:
                self._optional_retry_at[key] = self.hass.loop.time() + 300
        return data
