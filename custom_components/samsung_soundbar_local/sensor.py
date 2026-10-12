"""Optional sound mode sensor."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SoundbarConfigEntry
from .entity import SoundbarEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SoundbarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Samsung Soundbar sensor platform."""
    async_add_entities(
        [SamsungSoundbarSoundModeSensor(config_entry.runtime_data, "sound_mode")]
    )


class SamsungSoundbarSoundModeSensor(SoundbarEntity, SensorEntity):
    """Representation of the Soundbar Sound Mode."""

    _attr_translation_key = "sound_mode"

    @property
    def available(self) -> bool:
        """Return if the device reports a sound mode."""
        return super().available and self.coordinator.data.get("sound_mode") is not None

    @property
    def native_value(self) -> str | None:
        """Return the current sound mode."""
        return self.coordinator.data.get("sound_mode")
