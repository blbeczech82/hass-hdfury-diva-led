from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er

from .const import (
    CONF_NAME,
    DEFAULT_NAME,
    DOMAIN,
    STATIC_PROFILE,
)
from .coordinator import DivaLedCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DivaDefaultColorButton(hass, entry, coordinator)])


class DivaDefaultColorButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_name = "Reset to Default Color"

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: DivaLedCoordinator,
    ) -> None:
        self.hass = hass
        self._entry = entry
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry.unique_id}_reset_default_color"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id or entry.entry_id)},
            "name": entry.options.get(CONF_NAME, entry.data.get(CONF_NAME, DEFAULT_NAME)),
            "manufacturer": "HDFury",
            "model": "DIVA",
        }

    async def async_press(self) -> None:
        red = self._number_value("red")
        green = self._number_value("green")
        blue = self._number_value("blue")

        await self._coordinator.api.async_set_many(
            {
                "ledstripenabled": "on",
                "ledprofilevideo": STATIC_PROFILE,
                "ledprofilesync": STATIC_PROFILE,
                "ledprofilens": STATIC_PROFILE,
                "ledcolorred": red,
                "ledcolorgreen": green,
                "ledcolorblue": blue,
            }
        )
        await self._coordinator.async_request_refresh()

    def _number_value(self, channel: str) -> int:
        registry = er.async_get(self.hass)
        entity_id = registry.async_get_entity_id(
            "number",
            DOMAIN,
            f"{self._entry.unique_id}_default_{channel}",
        )
        if entity_id is None:
            return 0

        state = self.hass.states.get(entity_id)
        if state is None:
            return 0

        try:
            value = round(float(state.state))
        except (TypeError, ValueError):
            return 0

        return max(0, min(255, value))
