"""Media player for the local Samsung soundbar."""

import logging

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import SoundbarAPI
from .const import SOURCES
from .coordinator import SoundbarConfigEntry

_LOGGER = logging.getLogger(__name__)

SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.SELECT_SOURCE
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SoundbarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Samsung Soundbar media player platform."""
    coordinator = config_entry.runtime_data
    async_add_entities(
        [
            SamsungSoundbarEntity(
                coordinator,
                coordinator.api,
                config_entry.unique_id,
                coordinator.device_info,
            )
        ]
    )


class SamsungSoundbarEntity(CoordinatorEntity, MediaPlayerEntity):
    """Representation of a Samsung Soundbar."""

    _attr_has_entity_name = True
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = SUPPORTED_FEATURES
    _attr_source_list = SOURCES

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api: SoundbarAPI,
        mac_addr: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the Samsung Soundbar entity."""
        super().__init__(coordinator)
        self.api = api
        self._attr_unique_id = mac_addr
        self._attr_device_info = device_info
        self._attr_name = None  # use device name

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the state of the device."""
        if not self.coordinator.data:
            return None
        if self.coordinator.data.get("power"):
            return MediaPlayerState.ON
        return MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        if not self.coordinator.data or not self.coordinator.data.get("power"):
            return None
        vol = self.coordinator.data.get("volume", 0)
        return vol / 100.0

    @property
    def is_volume_muted(self) -> bool | None:
        """Boolean if volume is currently muted."""
        if not self.coordinator.data or not self.coordinator.data.get("power"):
            return None
        return self.coordinator.data.get("mute", False)

    @property
    def source(self) -> str | None:
        """Name of the current input source."""
        if not self.coordinator.data or not self.coordinator.data.get("power"):
            return None
        return self.coordinator.data.get("source")

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        await self.api.set_power("1")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        await self.api.set_power("0")
        await self.coordinator.async_request_refresh()

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        await self.api.set_mute("on" if mute else "off")
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        vol_int = round(max(0, min(1, volume)) * 100)
        await self.api.set_volume(vol_int)
        await self.coordinator.async_request_refresh()

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        if source not in SOURCES:
            raise ServiceValidationError("Unsupported input source")
        await self.api.set_input(source)
        await self.coordinator.async_request_refresh()
