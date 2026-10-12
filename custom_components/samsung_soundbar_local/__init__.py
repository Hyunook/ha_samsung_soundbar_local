"""Samsung Soundbar local integration."""

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .coordinator import SoundbarConfigEntry, SoundbarCoordinator

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.NUMBER, Platform.SELECT, Platform.SENSOR]


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


async def async_migrate_entry(hass: HomeAssistant, entry: SoundbarConfigEntry) -> bool:
    """Move connection settings from options into data (1.1)."""
    if entry.version > 1:
        return False
    if entry.minor_version < 2:
        options = dict(entry.options)
        connection = {
            key: options.pop(key) for key in (CONF_HOST, CONF_PORT) if key in options
        }
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, **connection}, options=options, minor_version=2
        )
    return True
