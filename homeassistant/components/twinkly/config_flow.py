"""Config flow to configure the Twinkly integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiohttp import ClientError
import twinkly_client
from voluptuous import Required, Schema

from homeassistant import config_entries, data_entry_flow
from homeassistant.components import dhcp
from homeassistant.const import CONF_HOST

from .const import (
    CONF_ENTRY_HOST,
    CONF_ENTRY_ID,
    CONF_ENTRY_MODEL,
    CONF_ENTRY_NAME,
    DEV_ID,
    DEV_MODEL,
    DEV_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class TwinklyConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle twinkly config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_device: tuple[dict[str, Any], str] | None = None

    async def async_step_user(self, user_input=None):
        """Handle config steps."""
        host = user_input[CONF_HOST] if user_input else None

        schema = {Required(CONF_HOST, default=host): str}
        errors = {}

        if host is not None:
            try:
                device_info = await twinkly_client.TwinklyClient(host).get_device_info()

                await self.async_set_unique_id(device_info[DEV_ID])
                self._abort_if_unique_id_configured()

                return self._create_entry_from_device(device_info, host)

            except (asyncio.TimeoutError, ClientError) as err:
                _LOGGER.info("Cannot reach Twinkly '%s' (client)", host, exc_info=err)
                errors[CONF_HOST] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=Schema(schema), errors=errors
        )

    async def async_step_dhcp(
        self, discovery_info: dhcp.DhcpServiceInfo
    ) -> data_entry_flow.FlowResult:
        """Handle dhcp discovery for twinkly."""
        self._async_abort_entries_match({CONF_ENTRY_HOST: discovery_info.ip})
        device_info = await twinkly_client.TwinklyClient(
            discovery_info.ip
        ).get_device_info()
        await self.async_set_unique_id(device_info[DEV_ID])
        self._abort_if_unique_id_configured(
            updates={CONF_ENTRY_HOST: discovery_info.ip}
        )

        self._discovered_device = (device_info, discovery_info.ip)
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input=None
    ) -> data_entry_flow.FlowResult:
        """Confirm discovery."""
        assert self._discovered_device is not None
        device_info, host = self._discovered_device

        if user_input is not None:
            return self._create_entry_from_device(device_info, host)

        self._set_confirm_only()
        placeholders = {
            "model": device_info[DEV_MODEL],
            "name": device_info[DEV_NAME],
            "host": host,
        }
        return self.async_show_form(
            step_id="discovery_confirm", description_placeholders=placeholders
        )

    def _create_entry_from_device(
        self, device_info: dict[str, Any], host: str
    ) -> data_entry_flow.FlowResult:
        """Create entry from device data."""
        return self.async_create_entry(
            title=device_info[DEV_NAME],
            data={
                CONF_ENTRY_HOST: host,
                CONF_ENTRY_ID: device_info[DEV_ID],
                CONF_ENTRY_NAME: device_info[DEV_NAME],
                CONF_ENTRY_MODEL: device_info[DEV_MODEL],
            },
        )
