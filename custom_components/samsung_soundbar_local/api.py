"""Local Samsung HTTP/XML client."""

import logging
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any

import aiohttp
from homeassistant.exceptions import HomeAssistantError

_LOGGER = logging.getLogger(__name__)


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
        self.base_url = f"http://{self.ip}:{self.port}/UIC?cmd="

    async def _send_cmd(self, cmd_name: str, params: str = "") -> dict[str, Any]:
        encoded_params = urllib.parse.quote(params)
        url = f"{self.base_url}%3Cname%3E{cmd_name}%3C/name%3E{encoded_params}"

        try:
            async with self.session.get(url, timeout=5) as response:
                response.raise_for_status()
                res_text = await response.text()
                return self._parse_xml(res_text)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise SoundbarAPIError("Cannot communicate with soundbar") from err

    def _parse_xml(self, xml_str: str) -> dict[str, Any]:
        try:
            root = ET.fromstring(xml_str)
        except ET.ParseError as err:
            raise SoundbarAPIError("Invalid XML response") from err
        response = root if root.tag == "response" else root.find(".//response")
        if response is None:
            raise SoundbarAPIError("Missing response element")
        if response.get("result", "").lower() != "ok":
            raise SoundbarUnsupportedError("Device rejected command")
        return {"result": "ok", **{child.tag: child.text for child in response}}

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
        return await self._value("GetFunc", "function")

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

    # --- EQ PRESETS ---
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
