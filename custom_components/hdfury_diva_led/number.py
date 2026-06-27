from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DEFAULT_NAME, DOMAIN
from .coordinator import DivaLedCoordinator


CHANNELS = (
    ("red", "Default Red", 229),
    ("green", "Default Green", 78),
    ("blue", "Default Blue", 0),
)


@dataclass(frozen=True)
class DivaNumberDescription:
    key: str
    name: str
    minimum: int
    maximum: int
    icon: str


DIVA_NUMBERS = (
    DivaNumberDescription("ledspeedpulsate", "Pulsating Speed", 1, 50, "mdi:sine-wave"),
    DivaNumberDescription("ledspeedrotate", "Rotating Speed", 1, 50, "mdi:rotate-360"),
    DivaNumberDescription("leddelay", "LED Global Delay", 0, 160, "mdi:timer-outline"),
    DivaNumberDescription("ledcolorred", "Static Color Red", 0, 255, "mdi:palette"),
    DivaNumberDescription("ledcolorgreen", "Static Color Green", 0, 255, "mdi:palette"),
    DivaNumberDescription("ledcolorblue", "Static Color Blue", 0, 255, "mdi:palette"),
    DivaNumberDescription("redgain", "Calibration Red Gain", 0, 31, "mdi:tune-variant"),
    DivaNumberDescription("greengain", "Calibration Green Gain", 0, 31, "mdi:tune-variant"),
    DivaNumberDescription("bluegain", "Calibration Blue Gain", 0, 31, "mdi:tune-variant"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [DivaDefaultColorNumber(entry, *channel) for channel in CHANNELS]
        + [DivaLedNumber(entry, coordinator, description) for description in DIVA_NUMBERS]
    )


class DivaDefaultColorNumber(NumberEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_native_min_value = 0
    _attr_native_max_value = 255
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:palette"

    def __init__(
        self,
        entry: ConfigEntry,
        channel: str,
        name: str,
        default: int,
    ) -> None:
        self._channel = channel
        self._value = default
        self._attr_name = name
        self._attr_unique_id = f"{entry.unique_id}_default_{channel}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id or entry.entry_id)},
            "name": entry.options.get(CONF_NAME, entry.data.get(CONF_NAME, DEFAULT_NAME)),
            "manufacturer": "HDFury",
            "model": "DIVA",
        }

    async def async_added_to_hass(self) -> None:
        if (last_state := await self.async_get_last_state()) is None:
            return

        try:
            self._value = self._clamp(round(float(last_state.state)))
        except (TypeError, ValueError):
            return

    @property
    def native_value(self) -> int:
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        self._value = self._clamp(round(value))
        self.async_write_ha_state()

    @staticmethod
    def _clamp(value: int) -> int:
        return max(0, min(255, value))


class DivaLedNumber(CoordinatorEntity[DivaLedCoordinator], NumberEntity):
    _attr_has_entity_name = True
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DivaLedCoordinator,
        description: DivaNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self._description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_native_min_value = description.minimum
        self._attr_native_max_value = description.maximum
        self._attr_icon = description.icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id or entry.entry_id)},
            "name": entry.options.get(CONF_NAME, entry.data.get(CONF_NAME, DEFAULT_NAME)),
            "manufacturer": "HDFury",
            "model": "DIVA",
        }

    @property
    def native_value(self) -> int:
        try:
            return int((self.coordinator.data or {}).get(self._description.key, 0))
        except (TypeError, ValueError):
            return 0

    async def async_set_native_value(self, value: float) -> None:
        rounded = round(value)
        clamped = max(self._description.minimum, min(self._description.maximum, rounded))
        await self.coordinator.api.async_set(self._description.key, clamped)
        await self.coordinator.async_request_refresh()
