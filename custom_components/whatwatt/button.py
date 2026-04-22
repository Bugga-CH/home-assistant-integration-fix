"""Button platform for WhatWatt integration."""
import logging
from typing import Any, Dict

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_DEVICE_IP, DEFAULT_NAME

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the WhatWatt button."""
    device_ip = config_entry.data.get(CONF_DEVICE_IP)
    name = config_entry.data.get("name", DEFAULT_NAME)

    async_add_entities([WhatWattConfigButton(config_entry.entry_id, device_ip, name)])


class WhatWattConfigButton(ButtonEntity):
    """Button to open the WhatWatt configuration page."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:cog"

    def __init__(self, entry_id: str, device_ip: str, device_name: str) -> None:
        """Initialize the button entity."""
        self._entry_id = entry_id
        self._device_ip = device_ip
        self._device_name = device_name

        # No dependency on device_info — use entry_id as stable identifier
        self._attr_unique_id = f"{entry_id}_config"
        self._attr_name = f"{device_name} Configuration"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info so the button appears under the same device as sensors."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=self._device_name,
            manufacturer="WhatWatt",
            model="WhatWatt Go",
            configuration_url=f"http://{self._device_ip}",
        )

    def press(self) -> None:
        """Handle the button press — logs the config URL."""
        _LOGGER.info(
            "WhatWatt configuration page available at: http://%s", self._device_ip
        )
