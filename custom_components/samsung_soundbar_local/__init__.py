"""Samsung Soundbar local integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import SoundbarConfigEntry, SoundbarCoordinator

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.SENSOR, Platform.NUMBER, Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: SoundbarConfigEntry) -> bool:
    """Set up the integration and fetch initial state."""
    coordinator = SoundbarCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SoundbarConfigEntry) -> bool:
    """Unload platforms."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
