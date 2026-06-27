from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_NAME, DEFAULT_NAME, DOMAIN
from .coordinator import DivaLedCoordinator


PROFILE_OPTIONS = {
    "0 - OFF": 0,
    "1 - FOLLOW ACTIVE VIDEO": 1,
    "2 - STATIC COLOR": 2,
    "3 - BLINKING STATIC COLOR": 3,
    "4 - PULSATING STATIC COLOR": 4,
    "5 - ROTATING COLORS": 7,
}

NS_PROFILE_OPTIONS = {
    key: value for key, value in PROFILE_OPTIONS.items() if value != 1
}

GAMMA_OPTIONS = {
    "Gamma 2.2": 0,
    "Gamma 2.0": 1,
    "Gamma 1.8": 2,
    "Gamma 1.6": 3,
}


@dataclass(frozen=True)
class DivaSelectDescription:
    key: str
    name: str
    options: dict[str, int]
    icon: str


SELECTS = (
    DivaSelectDescription("ledprofilevideo", "Active Video LED Profile", PROFILE_OPTIONS, "mdi:led-strip-variant"),
    DivaSelectDescription("ledprofilesync", "While Syncing LED Profile", PROFILE_OPTIONS, "mdi:led-strip-variant"),
    DivaSelectDescription("ledprofilens", "Not Supported LED Profile", NS_PROFILE_OPTIONS, "mdi:led-strip-variant"),
    DivaSelectDescription("ledgamma", "Video Gamma", GAMMA_OPTIONS, "mdi:gamma"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [DivaLedSelect(entry, coordinator, description) for description in SELECTS]
    )


class DivaLedSelect(CoordinatorEntity[DivaLedCoordinator], SelectEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: DivaLedCoordinator,
        description: DivaSelectDescription,
    ) -> None:
        super().__init__(coordinator)
        self._description = description
        self._value_to_option = {value: key for key, value in description.options.items()}
        self._attr_name = description.name
        self._attr_unique_id = f"{entry.unique_id}_{description.key}"
        self._attr_options = list(description.options)
        self._attr_icon = description.icon
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.unique_id or entry.entry_id)},
            "name": entry.options.get(CONF_NAME, entry.data.get(CONF_NAME, DEFAULT_NAME)),
            "manufacturer": "HDFury",
            "model": "DIVA",
        }

    @property
    def current_option(self) -> str | None:
        try:
            value = int((self.coordinator.data or {}).get(self._description.key, -1))
        except (TypeError, ValueError):
            return None
        return self._value_to_option.get(value)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api.async_set(self._description.key, self._description.options[option])
        await self.coordinator.async_request_refresh()
