"""Sensor platform for WhatWatt integration."""
import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    SENSOR_TYPES,
    DEFAULT_NAME,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the WhatWatt sensor platform."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    name = config_entry.data.get("name", DEFAULT_NAME)
    device_ip = entry_data["device_ip"]
    mqtt_topic = entry_data["mqtt_topic"]

    sensors = []
    for sensor_type, sensor_config in SENSOR_TYPES.items():
        sensor = WhatWattSensor(
            config_entry.entry_id,
            name,
            device_ip,
            mqtt_topic,
            sensor_type,
            sensor_config,
        )
        sensors.append(sensor)
        # Register sensor so __init__.py can push updates to it
        entry_data["sensors"][sensor_type] = sensor

    async_add_entities(sensors)


class WhatWattSensor(SensorEntity):
    """Representation of a WhatWatt sensor."""

    def __init__(
        self,
        entry_id: str,
        device_name: str,
        device_ip: str,
        mqtt_topic: str,
        sensor_type: str,
        sensor_config: Dict[str, Any],
    ) -> None:
        """Initialize the sensor."""
        self._entry_id = entry_id
        self._device_name = device_name
        self._device_ip = device_ip
        self._mqtt_topic = mqtt_topic
        self._sensor_type = sensor_type
        self._sensor_config = sensor_config
        self._state = None
        self._available = False
        self._sys_id = None  # Will be set on first MQTT message

        # Use entry_id as unique_id base until we get sys_id from MQTT
        self._attr_name = f"{device_name} {sensor_config['name']}"
        self._attr_unique_id = f"{entry_id}_{sensor_type}"
        self._attr_native_unit_of_measurement = sensor_config["unit"]
        self._attr_icon = sensor_config["icon"]
        self._attr_device_class = sensor_config["device_class"]
        self._attr_state_class = sensor_config["state_class"]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info. Uses sys_id once available, falls back to entry_id."""
        identifier = self._sys_id if self._sys_id else self._entry_id
        return DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=self._device_name,
            manufacturer="WhatWatt",
            model="WhatWatt Go",
            configuration_url=f"http://{self._device_ip}",
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self._state

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @callback
    def handle_mqtt_message(self, payload: Dict[str, Any]) -> None:
        """Handle new MQTT messages."""
        # Store sys_id for stable device_info identifiers
        if self._sys_id is None and payload.get("sys_id"):
            self._sys_id = payload["sys_id"]

        if self._sensor_type in payload:
            try:
                self._state = float(payload[self._sensor_type])
                self._available = True
            except (ValueError, TypeError) as ex:
                _LOGGER.error(
                    "Could not parse %s value %s: %s",
                    self._sensor_type,
                    payload[self._sensor_type],
                    ex,
                )
                self._available = False

        self.async_write_ha_state()
