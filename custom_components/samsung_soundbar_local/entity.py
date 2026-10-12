"""Base entity for the Samsung Soundbar integration."""

from collections.abc import Awaitable

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import SoundbarAPIError
from .const import DOMAIN
from .coordinator import SoundbarCoordinator


class SoundbarEntity(CoordinatorEntity[SoundbarCoordinator]):
    """Common device info, unique ID and command handling."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SoundbarCoordinator, key: str | None) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        mac = coordinator.config_entry.unique_id
        self._attr_unique_id = mac if key is None else f"{mac}_{key}"
        self._attr_device_info = coordinator.device_info

    @property
    def _powered(self) -> bool:
        return bool(self.coordinator.data and self.coordinator.data.get("power"))

    async def _async_command(self, command: Awaitable[object]) -> None:
        """Send a command and refresh the shared state."""
        try:
            await command
        except SoundbarAPIError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="command_failed"
            ) from err
        await self.coordinator.async_request_refresh()
