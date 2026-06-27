from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DEFAULT_NAME, DOMAIN, STATIC_PROFILE
from .coordinator import DivaLedCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DivaLedLight(entry, coordinator)])


class DivaLedLight(CoordinatorEntity[DivaLedCoordinator], LightEntity):
    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB

    def __init__(self, entry: ConfigEntry, coordinator: DivaLedCoordinator) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.unique_id}_led"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id or entry.entry_id)},
            "name": entry.options.get(CONF_NAME, entry.data.get(CONF_NAME, DEFAULT_NAME)),
            "manufacturer": "HDFury",
            "model": "DIVA",
        }

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

    @property
    def is_on(self) -> bool:
        return self._int_state("ledstripenabled") == 1

    @property
    def brightness(self) -> int:
        red, green, blue = self._raw_rgb
        return max(red, green, blue)

    @property
    def rgb_color(self) -> tuple[int, int, int]:
        red, green, blue = self._raw_rgb
        brightness = max(red, green, blue)
        if brightness == 0:
            return (255, 255, 255)
        return tuple(round(channel * 255 / brightness) for channel in (red, green, blue))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "raw_rgb": self._raw_rgb,
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        brightness = int(kwargs.get(ATTR_BRIGHTNESS, self.brightness or 255))
        rgb_color = kwargs.get(ATTR_RGB_COLOR, self.rgb_color)
        raw_rgb = self._scale_rgb(rgb_color, brightness)

        await self.coordinator.api.async_set_many(
            {
                "ledstripenabled": "on",
                "ledprofilevideo": STATIC_PROFILE,
                "ledprofilesync": STATIC_PROFILE,
                "ledprofilens": STATIC_PROFILE,
                "ledcolorred": raw_rgb[0],
                "ledcolorgreen": raw_rgb[1],
                "ledcolorblue": raw_rgb[2],
            }
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.api.async_set("ledstripenabled", "off")
        await self.coordinator.async_request_refresh()

    @property
    def _raw_rgb(self) -> tuple[int, int, int]:
        return (
            self._int_state("ledcolorred"),
            self._int_state("ledcolorgreen"),
            self._int_state("ledcolorblue"),
        )

    def _int_state(self, key: str) -> int:
        data = self.coordinator.data or {}
        try:
            return int(data.get(key, 0))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _scale_rgb(rgb_color: tuple[int, int, int], brightness: int) -> tuple[int, int, int]:
        brightness = max(0, min(255, brightness))
        return tuple(round(max(0, min(255, channel)) * brightness / 255) for channel in rgb_color)
