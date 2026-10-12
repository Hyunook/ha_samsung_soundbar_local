"""Media player for the local Samsung soundbar."""

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN, SOURCES
from .coordinator import SoundbarConfigEntry
from .entity import SoundbarEntity

PARALLEL_UPDATES = 1

SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.SELECT_SOURCE
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SoundbarConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Samsung Soundbar media player platform."""
    async_add_entities([SamsungSoundbarEntity(config_entry.runtime_data, None)])


class SamsungSoundbarEntity(SoundbarEntity, MediaPlayerEntity):
    """Representation of a Samsung Soundbar."""

    _attr_name = None
    _attr_device_class = MediaPlayerDeviceClass.RECEIVER
    _attr_supported_features = SUPPORTED_FEATURES
    _attr_source_list = SOURCES

    @property
    def state(self) -> MediaPlayerState | None:
        """Return the state of the device."""
        if not self.coordinator.data:
            return None
        return MediaPlayerState.ON if self._powered else MediaPlayerState.OFF

    @property
    def volume_level(self) -> float | None:
        """Volume level of the media player (0..1)."""
        if not self._powered:
            return None
        return self.coordinator.data["volume"] / 100

    @property
    def is_volume_muted(self) -> bool | None:
        """Boolean if volume is currently muted."""
        return self.coordinator.data["mute"] if self._powered else None

    @property
    def source(self) -> str | None:
        """Name of the current input source."""
        return self.coordinator.data["source"] if self._powered else None

    async def async_turn_on(self) -> None:
        """Turn the media player on."""
        await self._async_command(self.coordinator.api.set_power("1"))

    async def async_turn_off(self) -> None:
        """Turn the media player off."""
        await self._async_command(self.coordinator.api.set_power("0"))

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        await self._async_command(
            self.coordinator.api.set_mute("on" if mute else "off")
        )

    async def async_set_volume_level(self, volume: float) -> None:
        """Set volume level, range 0..1."""
        level = round(max(0, min(1, volume)) * 100)
        await self._async_command(self.coordinator.api.set_volume(level))

    async def async_select_source(self, source: str) -> None:
        """Select input source."""
        if source not in SOURCES:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_source",
                translation_placeholders={"source": source},
            )
        await self._async_command(self.coordinator.api.set_input(source))
