from __future__ import annotations

import asyncio
from typing import Any

import aiohttp


class DivaApiError(Exception):
    """Raised when the DIVA does not respond as expected."""


class DivaApi:
    def __init__(self, session: aiohttp.ClientSession, host: str) -> None:
        self._session = session
        self._base_url = f"http://{host}"

    async def async_get_info(self) -> dict[str, Any]:
        return await self._async_get_json("/ssi/brdinfo.ssi")

    async def async_get_led_state(self) -> dict[str, Any]:
        return await self._async_get_json("/ssi/toolpage.ssi")

    async def async_set(self, key: str, value: str | int) -> None:
        async with asyncio.timeout(8):
            response = await self._session.get(
                f"{self._base_url}/cmd",
                params={key: str(value)},
            )
            text = await response.text()

        if response.status != 200 or text.strip() != "OK":
            raise DivaApiError(f"DIVA command {key}={value} failed: {response.status} {text!r}")

    async def async_set_many(self, values: dict[str, str | int]) -> None:
        for key, value in values.items():
            await self.async_set(key, value)

    async def _async_get_json(self, path: str) -> dict[str, Any]:
        async with asyncio.timeout(8):
            response = await self._session.get(f"{self._base_url}{path}")
            data = await response.json(content_type=None)

        if response.status != 200 or not isinstance(data, dict):
            raise DivaApiError(f"DIVA request {path} failed: {response.status}")

        return data
