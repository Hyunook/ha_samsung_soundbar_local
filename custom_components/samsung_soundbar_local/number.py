"""Optional subwoofer, bass, treble and rear level control."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .api import SoundbarAPI
from .const import LEVEL_MAX, LEVEL_MIN
from .coordinator import SoundbarConfigEntry, SoundbarCoordinator
from .entity import SoundbarEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SoundbarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Samsung Soundbar number platform."""
    async_add_entities([SoundbarWooferNumber(config_entry.runtime_data, "woofer")])
    async_add_entities(
        SoundbarLevelNumber(config_entry.runtime_data, description)
        for description in LEVELS
    )


class SoundbarWooferNumber(SoundbarEntity, NumberEntity):
    """Representation of the Soundbar Woofer Level."""

    _attr_translation_key = "woofer_level"
    _attr_entity_category = EntityCategory.CONFIG
    # The SmartThings app offers -12 to +6; the HW-Q950T stored -7 and -12 (2026-10-16)
    _attr_native_min_value = -12
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


@dataclass(frozen=True, kw_only=True)
class SoundbarLevelDescription(NumberEntityDescription):
    """A level the coordinator stores under the description key."""

    set_fn: Callable[[SoundbarAPI, int], Awaitable[str]]


LEVELS = (
    SoundbarLevelDescription(
        key="bass",
        translation_key="bass",
        set_fn=lambda api, level: api.set_bass(level),
    ),
    SoundbarLevelDescription(
        key="treble",
        translation_key="treble",
        set_fn=lambda api, level: api.set_treble(level),
    ),
    SoundbarLevelDescription(
        key="rear_level",
        translation_key="rear_level",
        set_fn=lambda api, level: api.set_rear_level(level),
    ),
)


class SoundbarLevelNumber(SoundbarEntity, NumberEntity):
    """Bass, treble or rear level, configured like the subwoofer."""

    entity_description: SoundbarLevelDescription
    _attr_entity_category = EntityCategory.CONFIG
    _attr_native_min_value = LEVEL_MIN
    _attr_native_max_value = LEVEL_MAX
    _attr_native_step = 1

    def __init__(
        self, coordinator: SoundbarCoordinator, description: SoundbarLevelDescription
    ) -> None:
        """Initialize the level from its description."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def available(self) -> bool:
        """Return if the device reports this level."""
        return (
            super().available
            and self.coordinator.data.get(self.entity_description.key) is not None
        )

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return self.coordinator.data.get(self.entity_description.key)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self._async_command(
            self.entity_description.set_fn(self.coordinator.api, int(value))
        )
