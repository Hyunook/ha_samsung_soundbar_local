"""Optional equalizer preset selector."""

import logging
from typing import ClassVar

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SoundbarAPI
from .const import DOMAIN
from .coordinator import SoundbarConfigEntry

_LOGGER = logging.getLogger(__name__)

EQ_MODES = {0: "NONE", 1: "POP", 2: "JAZZ", 3: "CLASSIC"}
REVERSE_EQ_MODES = {v: k for k, v in EQ_MODES.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SoundbarConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Samsung Soundbar select platform."""
    coordinator = config_entry.runtime_data
    api: SoundbarAPI = coordinator.api
    mac_addr = config_entry.unique_id

    async_add_entities([SoundbarEQSelect(coordinator, api, mac_addr)])


class SoundbarEQSelect(CoordinatorEntity, SelectEntity):
    """Representation of the Soundbar EQ Mode."""

    _attr_has_entity_name = True
    _attr_name = "Equalizer"
    _attr_options: ClassVar[list[str]] = list(EQ_MODES.values())
    _attr_icon = "mdi:equalizer"

    def __init__(self, coordinator, api, mac_addr):
        """Initialize."""
        super().__init__(coordinator)
        self.api = api
        self._attr_unique_id = f"{mac_addr}_eq"
        self._attr_device_info = {"identifiers": {(DOMAIN, mac_addr)}}

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.get("eq_mode") in EQ_MODES

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        if not self.coordinator.data or not self.coordinator.data.get("power"):
            return None
        return EQ_MODES.get(self.coordinator.data.get("eq_mode"))

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        if option not in REVERSE_EQ_MODES:
            raise ServiceValidationError("Unsupported equalizer preset")
        idx = REVERSE_EQ_MODES[option]
        await self.api.set_eq_mode(idx)
        await self.coordinator.async_request_refresh()
