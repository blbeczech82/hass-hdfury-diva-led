from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DivaApi, DivaApiError
from .const import CONF_HOST, CONF_NAME, DEFAULT_HOST, DEFAULT_NAME, DOMAIN


class HdfuryDivaLedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        return await self._async_create_or_show("user", user_input)

    async def async_step_import(
        self, user_input: dict[str, Any]
    ) -> config_entries.ConfigFlowResult:
        return await self._async_create_or_show("import", user_input)

    async def _async_create_or_show(
        self,
        step_id: str,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            name = user_input[CONF_NAME].strip() or DEFAULT_NAME

            try:
                session = async_get_clientsession(self.hass)
                info = await DivaApi(session, host).async_get_info()
            except (aiohttp.ClientError, TimeoutError, DivaApiError):
                errors["base"] = "cannot_connect"
            else:
                serial = str(info.get("serial") or host)
                await self.async_set_unique_id(serial)
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                return self.async_create_entry(
                    title=name,
                    data={CONF_HOST: host, CONF_NAME: name},
                )

        return self.async_show_form(
            step_id=step_id,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                }
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return HdfuryDivaLedOptionsFlow(config_entry)


class HdfuryDivaLedOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        current = {**self._config_entry.data, **self._config_entry.options}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            name = user_input[CONF_NAME].strip() or DEFAULT_NAME

            try:
                session = async_get_clientsession(self.hass)
                await DivaApi(session, host).async_get_info()
            except (aiohttp.ClientError, TimeoutError, DivaApiError):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title="",
                    data={CONF_HOST: host, CONF_NAME: name},
                )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=current.get(CONF_HOST, DEFAULT_HOST),
                    ): str,
                    vol.Required(
                        CONF_NAME,
                        default=current.get(CONF_NAME, DEFAULT_NAME),
                    ): str,
                }
            ),
            errors=errors,
        )
