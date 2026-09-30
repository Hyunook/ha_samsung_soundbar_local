"""Configuration and options flows for Samsung Soundbar."""

import logging
import re
from typing import Any
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.service_info.ssdp import SsdpServiceInfo

from .api import SoundbarAPI, SoundbarAPIError
from .const import DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): vol.All(str, str.strip, vol.Length(min=1)),
        vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=5)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    port = data.get(CONF_PORT, DEFAULT_PORT)
    api = SoundbarAPI(data[CONF_HOST], session, port)

    try:
        info = await api.get_main_info()
    except SoundbarAPIError as err:
        raise CannotConnect from err

    mac = info.get("spkmacaddr")
    if not mac:
        raise CannotConnect

    mac = dr.format_mac(mac)
    if not re.fullmatch(r"(?:[0-9a-f]{2}:){5}[0-9a-f]{2}", mac):
        raise CannotConnect
    try:
        version = await api.get_software_version()
    except SoundbarAPIError:
        version = None

    # Return info to store
    return {
        "title": info.get("spkmodelname", "Samsung Soundbar"),
        "mac": mac,
        "model": info.get("spkmodelname", "Unknown Model"),
        "version": version,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Samsung Soundbar Local."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(info["mac"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=info["title"],
                    data={
                        **user_input,
                        "model": info["model"],
                        "version": info["version"],
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_ssdp(
        self, discovery_info: SsdpServiceInfo
    ) -> config_entries.ConfigFlowResult:
        """Handle SSDP discovery."""
        parsed_url = urlparse(discovery_info.ssdp_location)
        host = parsed_url.hostname

        if not host:
            return self.async_abort(reason="cannot_connect")

        # Try to connect and get mac address to use as unique id
        try:
            info = await validate_input(self.hass, {CONF_HOST: host})
            mac = info["mac"]
        except CannotConnect:
            return self.async_abort(reason="cannot_connect")

        await self.async_set_unique_id(mac)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {"host": host}
        self.discovered_host = host
        return await self.async_step_ssdp_confirm()

    async def async_step_ssdp_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Confirm discovery."""
        if user_input is not None:
            host = self.discovered_host
            port = user_input.get(CONF_PORT, DEFAULT_PORT)
            scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            try:
                info = await validate_input(
                    self.hass, {CONF_HOST: host, CONF_PORT: port}
                )
            except CannotConnect:
                return self.async_abort(reason="cannot_connect")

            return self.async_create_entry(
                title=info["title"],
                data={
                    CONF_HOST: host,
                    CONF_PORT: port,
                    CONF_SCAN_INTERVAL: scan_interval,
                    "model": info["model"],
                    "version": info["version"],
                },
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Required(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=5)),
            }
        )
        return self.async_show_form(
            step_id="ssdp_confirm",
            data_schema=schema,
            description_placeholders={"host": self.discovered_host},
        )


class OptionsFlowHandler(config_entries.OptionsFlowWithReload):
    """Handle options flow."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the options."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                if info["mac"] != self.config_entry.unique_id:
                    errors["base"] = "wrong_device"
                else:
                    return self.async_create_entry(title="", data=user_input)

        current_host = self.config_entry.options.get(
            CONF_HOST, self.config_entry.data.get(CONF_HOST, "")
        )
        current_port = self.config_entry.options.get(
            CONF_PORT, self.config_entry.data.get(CONF_PORT, DEFAULT_PORT)
        )
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )

        options_schema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=current_host): vol.All(
                    str, str.strip, vol.Length(min=1)
                ),
                vol.Required(CONF_PORT, default=current_port): cv.port,
                vol.Required(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                    vol.Coerce(int), vol.Range(min=5)
                ),
            }
        )

        return self.async_show_form(
            step_id="init", data_schema=options_schema, errors=errors
        )


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""
