from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DEFAULT_NAME, DOMAIN
from .coordinator import DivaLedCoordinator


@dataclass(frozen=True)
class DivaSwitchDescription:
    key: str
    name: str
    icon: str
    on_value: str | int = "on"
    off_value: str | int = "off"
    state_key: str | None = None
    bit: int | None = None


SWITCHES = (
    DivaSwitchDescription("ledstripenabled", "LEDs Enabled", "mdi:led-strip-variant"),
    DivaSwitchDescription("ledbbdet", "LED Black Bar Detect", "mdi:movie-open-outline"),
    DivaSwitchDescription("ledsynckeep", "Never Turn Off", "mdi:power-standby", 1, 0),
    DivaSwitchDescription("leddimleft", "Dim Left Side", "mdi:arrow-left-bold-outline", state_key="leddim", bit=0),
    DivaSwitchDescription("leddimtop", "Dim Top Side", "mdi:arrow-up-bold-outline", state_key="leddim", bit=1),
    DivaSwitchDescription("leddimright", "Dim Right Side", "mdi:arrow-right-bold-outline", state_key="leddim", bit=2),
    DivaSwitchDescription("leddimbot", "Dim Bottom Side", "mdi:arrow-down-bold-outline", state_key="leddim", bit=3),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [DivaLedSwitch(entry, coordinator, description) for description in SWITCHES]
    )


class DivaLedSwitch(CoordinatorEntity[DivaLedCoordinator], SwitchEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DivaLedCoordinator,
        description: DivaSwitchDescription,
    ) -> None:
        super().__init__(coordinator)
        self._description = description
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_icon = description.icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id or entry.entry_id)},
            "name": entry.options.get(CONF_NAME, entry.data.get(CONF_NAME, DEFAULT_NAME)),
            "manufacturer": "HDFury",
            "model": "DIVA",
        }

    @property
    def is_on(self) -> bool:
        data = self.coordinator.data or {}
        key = self._description.state_key or self._description.key
        try:
            value = int(data.get(key, 0))
        except (TypeError, ValueError):
            return False

        if self._description.bit is not None:
            return bool(value & (1 << self._description.bit))
        return value == 1

    async def async_turn_on(self, **kwargs: object) -> None:
        await self.coordinator.api.async_set(self._description.key, self._description.on_value)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: object) -> None:
        await self.coordinator.api.async_set(self._description.key, self._description.off_value)
        await self.coordinator.async_request_refresh()
