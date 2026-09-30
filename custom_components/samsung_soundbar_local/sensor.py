"""Optional sound mode sensor."""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import SoundbarAPI
from .coordinator import SoundbarConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SoundbarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Samsung Soundbar sensor platform."""
    coordinator = config_entry.runtime_data
    async_add_entities(
        [
            SamsungSoundbarSoundModeSensor(
                coordinator,
                coordinator.api,
                config_entry.unique_id,
                coordinator.device_info,
            )
        ]
    )


class SamsungSoundbarSoundModeSensor(CoordinatorEntity, SensorEntity):
    """Representation of the Soundbar Sound Mode."""

    _attr_has_entity_name = True
    _attr_translation_key = "sound_mode"
    _attr_icon = "mdi:audio-video"

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        api: SoundbarAPI,
        mac_addr: str,
        device_info: DeviceInfo,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.api = api
        self._attr_unique_id = f"{mac_addr}_sound_mode"
        self._attr_device_info = device_info

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("sound_mode") is not None

    @property
    def native_value(self) -> str | None:
        """Return the current sound mode."""
        if not self.coordinator.data or not self.coordinator.data.get("power"):
            return None
        return self.coordinator.data.get("sound_mode")
