"""Integration tests against the real Home Assistant runtime; synthetic data only."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType
from unittest.mock import AsyncMock, patch

import aiohttp
from aiohttp import web
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.samsung_soundbar_local.api import (
    SoundbarAPI,
    SoundbarAPIError,
    SoundbarUnsupportedError,
)
from custom_components.samsung_soundbar_local.config_flow import STEP_USER_DATA_SCHEMA
from custom_components.samsung_soundbar_local.const import DOMAIN
from custom_components.samsung_soundbar_local.coordinator import SoundbarCoordinator

ROOT = Path(__file__).resolve().parents[1]
MAC = ":".join(f"{value:02x}" for value in range(6))


def entry(**data):
    return ConfigEntry(
        version=1,
        minor_version=2,
        domain=DOMAIN,
        title="Synthetic Soundbar",
        data={"host": "example.invalid", **data},
        options={},
        source="user",
        unique_id=MAC,
        discovery_keys=MappingProxyType({}),
        subentries_data=[],
    )


class ReleaseTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        os.symlink(
            ROOT / "custom_components", Path(self.temp.name) / "custom_components"
        )
        self.hass = HomeAssistant(self.temp.name)
        from homeassistant import loader
        from homeassistant.helpers import frame

        loader.async_setup(self.hass)
        frame.async_setup(self.hass)
        from homeassistant.bootstrap import async_from_config_dict

        await async_from_config_dict(
            {"homeassistant": {}, "http": {}, "zeroconf": {}}, self.hass
        )

    async def asyncTearDown(self):
        await self.hass.async_stop(force=True)
        self.temp.cleanup()

    async def test_http_transport_and_errors(self):
        payload = '<root><response result="ok"><volume>23</volume></response></root>'

        async def handler(request):
            self.assertEqual(request.query["cmd"], "<name>GetVolume</name>")
            return web.Response(text=payload)

        app = web.Application()
        app.router.add_get("/UIC", handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "127.0.0.1", 0)
        await site.start()
        port = site._server.sockets[0].getsockname()[1]
        try:
            async with aiohttp.ClientSession() as session:
                api = SoundbarAPI("127.0.0.1", session, port)
                self.assertEqual(await api.get_volume(), 23)
                for value in (
                    "invalid XML",
                    "<root/>",
                    '<response result="ok"><volume/></response>',
                    '<response result="ok"><volume>abc</volume></response>',
                ):
                    payload = value
                    with self.assertRaises(SoundbarAPIError):
                        await api.get_volume()
                payload = '<response result="fail"/>'
                with self.assertRaises(SoundbarUnsupportedError):
                    await api.get_volume()
        finally:
            await runner.cleanup()

    async def test_eq_preset_list(self):
        api = SoundbarAPI("example.invalid", None)
        api._request = AsyncMock(
            return_value=api._parse_xml(
                '<response result="ok"><listcount>4</listcount><presetlist>'
                "<preset><presetindex>0</presetindex><presetname>Off</presetname></preset>"
                "<preset><presetindex>3</presetindex><presetname> Movie </presetname></preset>"
                "<preset><presetindex>x</presetindex><presetname>Bad</presetname></preset>"
                "<preset><presetindex>4</presetindex><presetname/></preset>"
                "</presetlist></response>"
            )
        )
        self.assertEqual(await api.get_eq_presets(), {0: "Off", 3: "Movie"})
        api._request = AsyncMock(
            return_value=api._parse_xml(
                '<response result="ok"><presetlist/></response>'
            )
        )
        with self.assertRaises(SoundbarAPIError):
            await api.get_eq_presets()

    async def test_stored_eq_presets_are_used_when_offline(self):
        stored = entry(eq_presets={"0": "Off", "2": "Music"})
        coordinator = SoundbarCoordinator(self.hass, stored)
        coordinator.api.get_eq_presets = AsyncMock(side_effect=SoundbarAPIError())
        await coordinator._async_setup()
        self.assertEqual(coordinator.eq_presets, {0: "Off", 2: "Music"})

    async def test_optional_failures_do_not_break_core(self):
        coordinator = SoundbarCoordinator(self.hass, entry())
        for name, value in [
            ("get_power", "1"),
            ("get_volume", 20),
            ("get_mute", "off"),
            ("get_input", "wifi"),
        ]:
            setattr(coordinator.api, name, AsyncMock(return_value=value))
        coordinator.api.get_sound_mode = AsyncMock(
            side_effect=SoundbarUnsupportedError()
        )
        coordinator.api.get_woofer_level = AsyncMock(side_effect=SoundbarAPIError())
        coordinator.api.get_eq_mode = AsyncMock(return_value=1)
        for _ in range(2):
            data = await coordinator._async_update_data()
            self.assertTrue(data["power"])
            self.assertEqual(data["volume"], 20)
            self.assertIsNone(data["sound_mode"])
            self.assertIsNone(data["woofer_level"])
        self.assertEqual(coordinator.api.get_sound_mode.call_count, 1)
        self.assertEqual(coordinator.api.get_woofer_level.call_count, 1)
        coordinator.api.get_power.return_value = "0"
        self.assertEqual(await coordinator._async_update_data(), {"power": False})

    async def test_flow_setup_entities_and_unload(self):
        values = {
            "get_main_info": {"spkmacaddr": MAC, "spkmodelname": "Synthetic Soundbar"},
            "get_software_version": "synthetic",
            "get_power": "1",
            "get_volume": 20,
            "get_mute": "off",
            "get_input": "wifi",
            "get_sound_mode": "standard",
            "get_woofer_level": 0,
            "get_eq_mode": 1,
            "get_eq_presets": {0: "Off", 1: "Pop", 5: "Custom"},
        }
        from contextlib import ExitStack

        with ExitStack() as stack:
            for method, result in values.items():
                stack.enter_context(
                    patch.object(SoundbarAPI, method, AsyncMock(return_value=result))
                )
            result = await self.hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "user"},
                data={"host": "example.invalid", "port": 56001, "scan_interval": 10},
            )
            self.assertEqual(result["type"], "create_entry", result)
            await self.hass.async_block_till_done()
            config_entry = result["result"]
            self.assertEqual(config_entry.state.value, "loaded")
            states = self.hass.states.async_all()
            for domain in ("media_player", "sensor", "number", "select"):
                self.assertTrue(
                    any(state.domain == domain for state in states), (domain, states)
                )
            duplicate = await self.hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "user"},
                data={"host": "example.invalid", "port": 56001, "scan_interval": 10},
            )
            self.assertEqual(duplicate["reason"], "already_configured")
            select_state = next(state for state in self.hass.states.async_all("select"))
            self.assertEqual(select_state.state, "Pop")
            self.assertEqual(
                select_state.attributes["options"], ["Off", "Pop", "Custom"]
            )
            self.assertEqual(
                config_entry.data["eq_presets"], {"0": "Off", "1": "Pop", "5": "Custom"}
            )
            with patch.object(
                SoundbarAPI, "set_eq_mode", AsyncMock(return_value="ok")
            ) as set_eq:
                await self.hass.services.async_call(
                    "select",
                    "select_option",
                    {"entity_id": select_state.entity_id, "option": "Custom"},
                    blocking=True,
                )
                set_eq.assert_awaited_once_with(5)
            with patch.object(
                SoundbarAPI, "set_power", AsyncMock(side_effect=SoundbarAPIError())
            ):
                with self.assertRaises(HomeAssistantError) as err:
                    await self.hass.services.async_call(
                        "media_player",
                        "turn_off",
                        {
                            "entity_id": self.hass.states.async_all("media_player")[
                                0
                            ].entity_id
                        },
                        blocking=True,
                    )
                self.assertEqual(err.exception.translation_key, "command_failed")

            flow = await self.hass.config_entries.options.async_init(
                config_entry.entry_id
            )
            self.assertEqual(flow["type"], "form")
            updated = await self.hass.config_entries.options.async_configure(
                flow["flow_id"], {"scan_interval": 15}
            )
            self.assertEqual(updated["type"], "create_entry")
            await self.hass.async_block_till_done()
            self.assertEqual(
                config_entry.runtime_data.update_interval.total_seconds(), 15
            )

            flow = await self.hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "reconfigure", "entry_id": config_entry.entry_id},
            )
            self.assertEqual(flow["step_id"], "reconfigure")
            with patch.object(
                SoundbarAPI,
                "get_main_info",
                AsyncMock(
                    return_value={
                        "spkmacaddr": ":".join(f"{value:02x}" for value in range(1, 7))
                    }
                ),
            ):
                wrong = await self.hass.config_entries.flow.async_configure(
                    flow["flow_id"], {"host": "other.invalid", "port": 56001}
                )
                self.assertEqual(wrong["reason"], "wrong_device")
            flow = await self.hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "reconfigure", "entry_id": config_entry.entry_id},
            )
            done = await self.hass.config_entries.flow.async_configure(
                flow["flow_id"], {"host": "new.invalid", "port": 56002}
            )
            self.assertEqual(done["reason"], "reconfigure_successful")
            await self.hass.async_block_till_done()
            self.assertEqual(
                (config_entry.data["host"], config_entry.data["port"]),
                ("new.invalid", 56002),
            )
            self.assertEqual(config_entry.runtime_data.api.ip, "new.invalid")
            self.assertTrue(
                await self.hass.config_entries.async_unload(config_entry.entry_id)
            )

    async def test_migrates_connection_options(self):
        legacy = ConfigEntry(
            version=1,
            minor_version=1,
            domain=DOMAIN,
            title="Synthetic Soundbar",
            data={"host": "old.invalid", "port": 56001, "scan_interval": 10},
            options={"host": "new.invalid", "port": 56001, "scan_interval": 20},
            source="user",
            unique_id=MAC,
            discovery_keys=MappingProxyType({}),
            subentries_data=[],
        )
        self.hass.config_entries._entries[legacy.entry_id] = legacy
        from custom_components.samsung_soundbar_local import async_migrate_entry

        self.assertTrue(await async_migrate_entry(self.hass, legacy))
        self.assertEqual(legacy.minor_version, 2)
        self.assertEqual(legacy.data["host"], "new.invalid")
        self.assertEqual(dict(legacy.options), {"scan_interval": 20})

    async def test_schemas_and_metadata(self):
        import voluptuous as vol

        for fields in (
            {"host": ""},
            {"host": "example.invalid", "port": 70000},
            {"host": "example.invalid", "scan_interval": 0},
        ):
            with self.assertRaises(vol.Invalid):
                STEP_USER_DATA_SCHEMA(fields)
        root = ROOT / "custom_components" / DOMAIN
        manifest = json.loads((root / "manifest.json").read_text())
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")
        self.assertTrue((root / "brand/icon.png").is_file())
        icons = json.loads((root / "icons.json").read_text())
        strings_entities = json.loads((root / "strings.json").read_text())["entity"]
        for platform, keys in icons["entity"].items():
            self.assertTrue(set(keys) <= set(strings_entities[platform]))
        strings = json.loads((root / "strings.json").read_text())

        def paths(value, prefix=""):
            result = set()
            for key, item in value.items():
                name = prefix + "." + key
                result.add(name)
                if isinstance(item, dict):
                    result |= paths(item, name)
            return result

        for translation in (root / "translations").glob("*.json"):
            self.assertEqual(paths(strings), paths(json.loads(translation.read_text())))


if __name__ == "__main__":
    unittest.main(verbosity=2)
