"""Local Samsung HTTP/XML client."""

import logging
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any

import aiohttp
from homeassistant.exceptions import HomeAssistantError

from .const import LEVEL_MAX, LEVEL_MIN

_LOGGER = logging.getLogger(__name__)

# The soundbar sometimes hands a request the response meant for another one
# (another client, or a request that timed out). Each response names its
# command in <method>, so reads are checked against it and asked again.
METHODS = {
    "GetPowerStatus": "PowerStatus",
    "GetVolume": "VolumeLevel",
    "GetMute": "MuteStatus",
    "GetFunc": "CurrentFunc",
    "GetPlayStatus": "PlayStatus",
    "GetSoundMode": "SoundMode",
    "GetWooferLevel": "WooferLevel",
    "GetCurrentEQMode": "CurrentEQMode",
    "Get7BandEQList": "7BandEQList",
    "GetEQBass": "EQBass",
    "GetEQTreble": "EQTreble",
    "GetRearLevel": "RearLevel",
    "GetMainInfo": "MainInfo",
    "GetSoftwareVersion": "SoftwareVersion",
}
ATTEMPTS = 3


class SoundbarAPIError(HomeAssistantError):
    """Exception to indicate a general API error."""


class SoundbarUnsupportedError(SoundbarAPIError):
    """The device explicitly rejected a command."""


class SoundbarAPI:
    """Async API for Samsung Soundbar local control."""

    def __init__(self, ip: str, session: aiohttp.ClientSession, port: int = 56001):
        self.ip = ip
        self.port = port
        self.session = session
        self.base_url = f"http://{self.ip}:{self.port}"

    async def _request(
        self,
        cmd_name: str,
        params: str = "",
        endpoint: str = "UIC",
        timeout: float = 5,
    ) -> ET.Element:
        encoded_params = urllib.parse.quote(params)
        url = (
            f"{self.base_url}/{endpoint}?cmd="
            f"%3Cname%3E{cmd_name}%3C/name%3E{encoded_params}"
        )

        expected = METHODS.get(cmd_name)
        for _ in range(ATTEMPTS):
            try:
                async with self.session.get(url, timeout=timeout) as response:
                    response.raise_for_status()
                    res_text = await response.text()
            except (aiohttp.ClientError, TimeoutError) as err:
                raise SoundbarAPIError("Cannot communicate with soundbar") from err
            root = self._parse_root(res_text)
            if expected is None or self._belongs_to(root, expected):
                return self._parse_response(root)
            _LOGGER.debug(
                "Asking %s again, got a response for %s",
                cmd_name,
                root.findtext("method"),
            )
        raise SoundbarAPIError(f"No {expected} response to {cmd_name}")

    async def _send_cmd(self, cmd_name: str, params: str = "") -> dict[str, Any]:
        response = await self._request(cmd_name, params)
        return {"result": "ok", **{child.tag: child.text for child in response}}

    @staticmethod
    def _belongs_to(root: ET.Element, expected: str) -> bool:
        method = root.findtext("method")
        if method is not None and method.strip() != expected:
            return False
        # An accepted read without any value has been seen as well.
        response = root if root.tag == "response" else root.find(".//response")
        return not (
            response is not None
            and response.get("result", "").lower() == "ok"
            and len(response) == 0
        )

    @staticmethod
    def _parse_root(xml_str: str) -> ET.Element:
        try:
            return ET.fromstring(xml_str)
        except ET.ParseError as err:
            raise SoundbarAPIError("Invalid XML response") from err

    def _parse_xml(self, xml_str: str) -> ET.Element:
        return self._parse_response(self._parse_root(xml_str))

    @staticmethod
    def _parse_response(root: ET.Element) -> ET.Element:
        response = root if root.tag == "response" else root.find(".//response")
        if response is None:
            raise SoundbarAPIError("Missing response element")
        if response.get("result", "").lower() != "ok":
            raise SoundbarUnsupportedError("Device rejected command")
        return response

    async def _value(self, command: str, field: str) -> str:
        result = await self._send_cmd(command)
        value = result.get(field)
        if not isinstance(value, str) or not value.strip():
            raise SoundbarAPIError(f"Missing {field} in {command} response")
        return value.strip()

    async def _number(self, command: str, field: str) -> int:
        try:
            return int(await self._value(command, field))
        except ValueError as err:
            raise SoundbarAPIError(f"Invalid number in {command} response") from err

    # --- INPUT ---
    async def get_input(self) -> str:
        # GetFunc never answers while Spotify Connect plays. The CPM play
        # status keeps reporting the last network function even after a
        # switch to another input, so it is only asked when GetFunc hangs.
        try:
            response = await self._request("GetFunc", timeout=2)
        except SoundbarAPIError:
            response = await self._request("GetPlayStatus", endpoint="CPM")
        value = (response.findtext("function") or "").strip()
        if not value:
            raise SoundbarAPIError("Missing function in input response")
        return value

    async def set_input(self, input_name: str) -> str:
        res = await self._send_cmd(
            "SetFunc", f'<p type="str" name="function" val="{input_name}"/>'
        )
        return res.get("result", "")

    # --- VOLUME ---
    async def get_volume(self) -> int:
        value = await self._number("GetVolume", "volume")
        if not 0 <= value <= 100:
            raise SoundbarAPIError("Volume outside device range")
        return value

    async def set_volume(self, level: int) -> str:
        res = await self._send_cmd(
            "SetVolume", f'<p type="dec" name="volume" val="{level}"/>'
        )
        return res.get("result", "")

    # --- MUTE ---
    async def get_mute(self) -> str:
        value = await self._value("GetMute", "mute")
        if value not in ("on", "off"):
            raise SoundbarAPIError("Invalid mute state")
        return value

    async def set_mute(self, state: str) -> str:
        # state: "on" or "off"
        res = await self._send_cmd(
            "SetMute", f'<p type="str" name="mute" val="{state}"/>'
        )
        return res.get("result", "")

    # --- SOUND MODE ---
    async def get_sound_mode(self) -> str:
        return await self._value("GetSoundMode", "soundMode")

    async def set_sound_mode(self, mode: str) -> str:
        res = await self._send_cmd(
            "SetSoundMode", f'<p type="str" name="soundmode" val="{mode}"/>'
        )
        return res.get("result", "")

    # --- WOOFER ---
    async def get_woofer_level(self) -> int:
        return await self._number("GetWooferLevel", "level")

    async def set_woofer_level(self, level: int) -> str:
        res = await self._send_cmd(
            "SetWooferLevel", f'<p type="dec" name="wooferlevel" val="{level}"/>'
        )
        return res.get("result", "")

    # --- BASS, TREBLE AND REAR LEVEL ---
    @staticmethod
    def _check_level(level: int) -> None:
        # Refuse before sending: the soundbar's reaction to values outside the
        # app's range is unknown.
        if not LEVEL_MIN <= level <= LEVEL_MAX:
            raise ValueError(f"Level {level} outside {LEVEL_MIN}..{LEVEL_MAX}")

    async def get_bass(self) -> int:
        return await self._number("GetEQBass", "eqbass")

    async def set_bass(self, level: int) -> str:
        self._check_level(level)
        res = await self._send_cmd(
            "SetEQBass", f'<p type="dec" name="eqbass" val="{level}"/>'
        )
        return res.get("result", "")

    async def get_treble(self) -> int:
        return await self._number("GetEQTreble", "eqtreble")

    async def set_treble(self, level: int) -> str:
        self._check_level(level)
        res = await self._send_cmd(
            "SetEQTreble", f'<p type="dec" name="eqtreble" val="{level}"/>'
        )
        return res.get("result", "")

    async def get_rear_level(self) -> int | None:
        """Return the rear level, or None unless the rear speakers are active."""
        result = await self._send_cmd("GetRearLevel")
        # SetRearLevel always sends activate=on; only offer it when that is
        # already the state, so a level change never switches the rears on.
        if any(
            (result.get(field) or "").strip() != "on"
            for field in ("activate", "connection")
        ):
            return None
        try:
            return int((result.get("level") or "").strip())
        except ValueError as err:
            raise SoundbarAPIError("Invalid number in GetRearLevel response") from err

    async def set_rear_level(self, level: int) -> str:
        self._check_level(level)
        res = await self._send_cmd(
            "SetRearLevel",
            f'<p type="dec" name="level" val="{level}"/>'
            '<p type="str" name="activate" val="on"/>',
        )
        return res.get("result", "")

    # --- EQ PRESETS ---
    async def get_eq_presets(self) -> dict[int, str]:
        """Return the model's equalizer presets as index -> name."""
        response = await self._request("Get7BandEQList")
        presets: dict[int, str] = {}
        for preset in response.iterfind(".//presetlist/preset"):
            index = (preset.findtext("presetindex") or "").strip()
            name = (preset.findtext("presetname") or "").strip()
            if index.isdigit() and name and name not in presets.values():
                presets[int(index)] = name
        if not presets:
            raise SoundbarAPIError("No presets in Get7BandEQList response")
        return presets

    async def get_eq_mode(self) -> int:
        return await self._number("GetCurrentEQMode", "presetindex")

    async def set_eq_mode(self, index: int) -> str:
        res = await self._send_cmd(
            "Set7bandEQMode", f'<p type="dec" name="presetindex" val="{index}"/>'
        )
        return res.get("result", "")

    # --- POWER ---
    async def get_power(self) -> str:
        value = await self._value("GetPowerStatus", "powerStatus")
        if value not in ("0", "1"):
            raise SoundbarAPIError("Invalid power state")
        return value

    async def set_power(self, state: str) -> str:
        # state: "1" (on) or "0" (off/standby)
        res = await self._send_cmd(
            "SetPowerStatus", f'<p type="dec" name="powerStatus" val="{state}"/>'
        )
        return res.get("result", "")

    # --- INFO ---
    async def get_main_info(self) -> dict[str, str]:
        return await self._send_cmd("GetMainInfo")

    async def get_software_version(self) -> str:
        return await self._value("GetSoftwareVersion", "version")
