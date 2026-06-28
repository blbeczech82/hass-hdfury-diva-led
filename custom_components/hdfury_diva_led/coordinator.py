from __future__ import annotations

import asyncio
from datetime import timedelta
import logging
from time import monotonic
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DivaApi, DivaApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)
PENDING_STATE_TTL = 10
DELAYED_REFRESH = 5


class DivaLedCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, api: DivaApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.api = api
        self._pending_state: dict[str, tuple[str, float]] = {}
        self._delayed_refresh_task: asyncio.Task[None] | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.api.async_get_led_state()
        except (TimeoutError, DivaApiError) as err:
            raise UpdateFailed(str(err)) from err

        return self._with_pending_state(data)

    def async_set_pending_state(self, key: str, value: str | int) -> None:
        self._pending_state[key] = (str(value), monotonic() + PENDING_STATE_TTL)
        self.async_set_updated_data(self._with_pending_state(dict(self.data or {})))
        self._schedule_delayed_refresh()

    def _with_pending_state(self, data: dict[str, Any]) -> dict[str, Any]:
        now = monotonic()
        for key, (value, expires_at) in list(self._pending_state.items()):
            if now >= expires_at:
                self._pending_state.pop(key, None)
                continue
            data[key] = value
        return data

    def _schedule_delayed_refresh(self) -> None:
        if self._delayed_refresh_task is not None:
            self._delayed_refresh_task.cancel()
        self._delayed_refresh_task = self.hass.async_create_task(
            self._async_delayed_refresh()
        )

    async def _async_delayed_refresh(self) -> None:
        try:
            await asyncio.sleep(DELAYED_REFRESH)
            await self.async_request_refresh()
        except asyncio.CancelledError:
            pass
