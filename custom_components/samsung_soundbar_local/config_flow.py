"""Configuration, reconfiguration and options flows for Samsung Soundbar."""

import logging
import re
from typing import Any
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo

from .api import SoundbarAPI, SoundbarAPIError
from .const import DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import SoundbarConfigEntry

_LOGGER = logging.getLogger(__name__)

HOST_VALIDATOR = vol.All(str, str.strip, vol.Length(min=1))
SCAN_INTERVAL_VALIDATOR = vol.All(vol.Coerce(int), vol.Range(min=5))

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): HOST_VALIDATOR,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Required(
            CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
        ): SCAN_INTERVAL_VALIDATOR,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    api = SoundbarAPI(
        data[CONF_HOST],
        async_get_clientsession(hass),
        data.get(CONF_PORT, DEFAULT_PORT),
    )

    try:
        info = await api.get_main_info()
    except SoundbarAPIError as err:
        raise CannotConnect from err

    mac = dr.format_mac(info.get("spkmacaddr") or "")
    if not re.fullmatch(r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}", mac):
        raise CannotConnect
    try:
        version = await api.get_software_version()
    except SoundbarAPIError:
        version = None

    return {
        "title": info.get("spkmodelname", "Samsung Soundbar"),
        "mac": mac,
        "model": info.get("spkmodelname", "Unknown Model"),
        "version": version,
    }


class SoundbarConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Samsung Soundbar Local."""

    VERSION = 1
    MINOR_VERSION = 2

    _discovered_host: str

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: SoundbarConfigEntry,
    ) -> "OptionsFlowHandler":
        """Create the options flow."""
        return OptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info["mac"])
                self._abort_if_unique_id_configured(
                    updates={
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    }
                )
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        **user_input,
                        "model": info["model"],
                        "version": info["version"],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
        )

    async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> ConfigFlowResult:
        """Handle SSDP discovery."""
        host = urlparse(discovery_info.ssdp_location).hostname
        if not host:
            return self.async_abort(reason="cannot_connect")

        try:
            info = await validate_input(self.hass, {CONF_HOST: host})
        except CannotConnect:
            return self.async_abort(reason="cannot_connect")

        await self.async_set_unique_id(info["mac"])
        # A soundbar that moved to a new address is updated, not re-added.
        self._abort_if_unique_id_configured(updates={CONF_HOST: host})

        self._discovered_host = host
        self.context["title_placeholders"] = {"name": info["title"]}
        return await self.async_step_ssdp_confirm()

    async def async_step_ssdp_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm discovery."""
        if user_input is not None:
            data = {CONF_HOST: self._discovered_host, **user_input}
            try:
                info = await validate_input(self.hass, data)
            except CannotConnect:
                return self.async_abort(reason="cannot_connect")

            return self.async_create_entry(
                title=info["title"],
                data={**data, "model": info["model"], "version": info["version"]},
            )

        return self.async_show_form(
            step_id="ssdp_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): SCAN_INTERVAL_VALIDATOR,
                }
            ),
            description_placeholders={"host": self._discovered_host},
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the address of the configured soundbar."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(info["mac"])
                self._abort_if_unique_id_mismatch(reason="wrong_device")
                return self.async_update_reload_and_abort(
                    entry, data_updates=user_input
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): HOST_VALIDATOR,
                vol.Required(CONF_PORT): cv.port,
            }
        )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                schema, user_input or entry.data
            ),
            errors=errors,
        )


class OptionsFlowHandler(OptionsFlowWithReload):
    """Handle the polling interval option."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL, default=current
                    ): SCAN_INTERVAL_VALIDATOR
                }
            ),
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""
