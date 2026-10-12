"""Optional subwoofer control."""

from homeassistant.components.number import NumberEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SoundbarConfigEntry
from .entity import SoundbarEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SoundbarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Samsung Soundbar number platform."""
    async_add_entities([SoundbarWooferNumber(config_entry.runtime_data, "woofer")])


class SoundbarWooferNumber(SoundbarEntity, NumberEntity):
    """Representation of the Soundbar Woofer Level."""

    _attr_translation_key = "woofer_level"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = -6
    _attr_native_max_value = 6
    _attr_native_step = 1

    @property
    def available(self) -> bool:
        """Return if the device reports a subwoofer level."""
        return (
            super().available and self.coordinator.data.get("woofer_level") is not None
        )

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return self.coordinator.data.get("woofer_level")

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self._async_command(self.coordinator.api.set_woofer_level(int(value)))
