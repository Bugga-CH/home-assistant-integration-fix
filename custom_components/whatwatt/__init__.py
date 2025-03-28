"""The WhatWatt integration."""
import asyncio
import json
import logging
from typing import Any, Dict

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import ConfigType
from homeassistant.components import persistent_notification

from .const import (
    DOMAIN,
    CONF_MQTT_TOPIC,
    CONF_DEVICE_IP,
    DEFAULT_NAME,
    ATTR_SYS_ID,
    ATTR_METER_ID,
)

_LOGGER = logging.getLogger(__name__)

# Define the platforms we support
PLATFORMS = [Platform.SENSOR, Platform.BUTTON]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WhatWatt component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WhatWatt from a config entry."""
    mqtt_topic = entry.data[CONF_MQTT_TOPIC]
    device_ip = entry.data[CONF_DEVICE_IP]
    name = entry.data.get("name", DEFAULT_NAME)

    # Check if MQTT integration is set up
    if not hass.services.has_service("mqtt", "publish"):
        _LOGGER.error("MQTT integration is not set up")
        
        # Create a persistent notification to guide the user
        persistent_notification.create(
            hass,
            "The WhatWatt integration requires MQTT to be set up. "
            "Please go to Settings > Devices & Services > Add Integration > MQTT "
            "to set up MQTT, then restart Home Assistant.",
            title="WhatWatt - MQTT Required",
            notification_id="whatwatt_mqtt_missing"
        )
        
        raise ConfigEntryNotReady("MQTT integration is not set up")

    # Store device info for use by platforms
    hass.data[DOMAIN][entry.entry_id] = {
        "mqtt_topic": mqtt_topic,
        "device_ip": device_ip,
        "device_info": None,  # Will be populated when we receive the first message
        "sensors": {},
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Subscribe to MQTT topic
    @callback
    async def message_received(msg):
        """Handle new MQTT messages."""
        try:
            payload = json.loads(msg.payload)
            _LOGGER.debug("Received message: %s", payload)

            # Extract device identifiers
            sys_id = payload.get(ATTR_SYS_ID)
            meter_id = payload.get(ATTR_METER_ID)

            if not sys_id:
                _LOGGER.error("Message missing required sys_id field")
                return

            # Create or update device info
            if hass.data[DOMAIN][entry.entry_id]["device_info"] is None:
                device_info = DeviceInfo(
                    identifiers={(DOMAIN, sys_id)},
                    name=name,
                    manufacturer="WhatWatt",
                    model=f"WhatWatt Go",
                    sw_version=payload.get("version", "Unknown"),
                    configuration_url=f"http://{device_ip}",
                )
                hass.data[DOMAIN][entry.entry_id]["device_info"] = device_info

            # Update sensors
            for sensor in hass.data[DOMAIN][entry.entry_id].get("sensors", {}).values():
                sensor.handle_mqtt_message(payload)

        except json.JSONDecodeError:
            _LOGGER.error("Invalid JSON in MQTT message")
        except Exception as ex:
            _LOGGER.error("Error processing MQTT message: %s", ex)

    # Subscribe to the MQTT topic
    unsubscribe = await hass.components.mqtt.async_subscribe(
        mqtt_topic, message_received
    )

    # Store the unsubscribe function for cleanup
    hass.data[DOMAIN][entry.entry_id]["unsubscribe"] = unsubscribe

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unsubscribe from MQTT topic
    if "unsubscribe" in hass.data[DOMAIN][entry.entry_id]:
        hass.data[DOMAIN][entry.entry_id]["unsubscribe"]()

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove entry data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
