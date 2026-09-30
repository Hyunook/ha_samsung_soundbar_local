"""Optional subwoofer control."""

import logging

from homeassistant.components.number import NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SoundbarAPI
from .const import DOMAIN
from .coordinator import SoundbarConfigEntry

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SoundbarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Samsung Soundbar number platform."""
    coordinator = config_entry.runtime_data
    api: SoundbarAPI = coordinator.api
    mac_addr = config_entry.unique_id

    async_add_entities([SoundbarWooferNumber(coordinator, api, mac_addr)])


class SoundbarWooferNumber(CoordinatorEntity, NumberEntity):
    """Representation of the Soundbar Woofer Level."""

    _attr_has_entity_name = True
    _attr_name = "Subwoofer"
    _attr_native_min_value = -6
    _attr_native_max_value = 6
    _attr_native_step = 1
    _attr_icon = "mdi:speaker-wireless"

    def __init__(self, coordinator, api, mac_addr):
        """Initialize."""
        super().__init__(coordinator)
        self.api = api
        self._attr_unique_id = f"{mac_addr}_woofer"
        self._attr_device_info = {"identifiers": {(DOMAIN, mac_addr)}}

    @property
    def available(self) -> bool:
        return (
            super().available and self.coordinator.data.get("woofer_level") is not None
        )

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if not self.coordinator.data or not self.coordinator.data.get("power"):
            return None
        return self.coordinator.data.get("woofer_level")

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        if not -6 <= value <= 6 or value != int(value):
            raise ServiceValidationError(
                "Subwoofer level must be an integer from -6 to 6"
            )
        await self.api.set_woofer_level(int(value))
        await self.coordinator.async_request_refresh()
