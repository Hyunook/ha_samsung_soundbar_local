"""Optional equalizer preset selector."""

from homeassistant.components.select import SelectEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SoundbarConfigEntry, SoundbarCoordinator
from .entity import SoundbarEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SoundbarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the equalizer when the model reported its presets."""
    coordinator = config_entry.runtime_data
    if coordinator.eq_presets:
        async_add_entities([SoundbarEQSelect(coordinator, "eq")])


class SoundbarEQSelect(SoundbarEntity, SelectEntity):
    """Equalizer presets as reported by the soundbar."""

    _attr_translation_key = "equalizer"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: SoundbarCoordinator, key: str) -> None:
        """Initialize the select with the device's preset names."""
        super().__init__(coordinator, key)
        self._presets = coordinator.eq_presets
        self._attr_options = list(self._presets.values())

    @property
    def available(self) -> bool:
        """Return if the device reports an equalizer preset."""
        return super().available and self.coordinator.data.get("eq_mode") is not None

    @property
    def current_option(self) -> str | None:
        """Return the current option."""
        return self._presets.get(self.coordinator.data.get("eq_mode"))

    async def async_select_option(self, option: str) -> None:
        """Select an option."""
        index = next(i for i, name in self._presets.items() if name == option)
        await self._async_command(self.coordinator.api.set_eq_mode(index))
