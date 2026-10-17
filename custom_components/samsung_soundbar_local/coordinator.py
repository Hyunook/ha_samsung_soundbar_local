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
from .const import CONF_EQ_PRESETS, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN

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
        # JSON storage needs string keys; restore the last known preset list.
        self.eq_presets: dict[int, str] = {
            int(index): name
            for index, name in entry.data.get(CONF_EQ_PRESETS, {}).items()
        }
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

    async def _async_setup(self) -> None:
        """Read the model's equalizer presets and keep them in the entry."""
        try:
            presets = await self.api.get_eq_presets()
        except SoundbarAPIError as err:
            _LOGGER.debug("Using stored equalizer presets: %s", err)
            return
        if presets != self.eq_presets:
            self.eq_presets = presets
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={
                    **self.config_entry.data,
                    CONF_EQ_PRESETS: {str(i): name for i, name in presets.items()},
                },
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
            }
        except SoundbarAPIError as err:
            raise UpdateFailed(str(err)) from err
        for key, getter in (
            # The HW-Q950T does not answer GetFunc while it is playing (timeout or no
            # <function>), so a missing source must not take the whole device down
            ("source", self.api.get_input),
            ("sound_mode", self.api.get_sound_mode),
            ("woofer_level", self.api.get_woofer_level),
            ("eq_mode", self.api.get_eq_mode),
            ("bass", self.api.get_bass),
            ("treble", self.api.get_treble),
            ("rear_level", self.api.get_rear_level),
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
