"""The WhatWatt integration."""
import json
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType
from homeassistant.components import persistent_notification, mqtt

from .const import (
    DOMAIN,
    CONF_MQTT_TOPIC,
    CONF_DEVICE_IP,
    DEFAULT_NAME,
    ATTR_SYS_ID,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the WhatWatt component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WhatWatt from a config entry."""
    mqtt_topic = entry.data[CONF_MQTT_TOPIC]
    device_ip = entry.data[CONF_DEVICE_IP]
    _LOGGER.debug("WhatWatt entry.data: %s", dict(entry.data))
    
    # Check if MQTT integration is available
    if not hass.services.has_service("mqtt", "publish"):
        _LOGGER.error("WhatWatt: MQTT integration is not set up")
        persistent_notification.create(
            hass,
            "The WhatWatt integration requires MQTT to be set up. "
            "Please go to Settings > Devices & Services > Add Integration > MQTT, "
            "then restart Home Assistant.",
            title="WhatWatt - MQTT Required",
            notification_id="whatwatt_mqtt_missing",
        )
        raise ConfigEntryNotReady("MQTT integration is not set up")

    # Initialize entry data — sensors dict will be populated by sensor.py
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "mqtt_topic": mqtt_topic,
        "device_ip": device_ip,
        "sensors": {},
    }

    # Set up sensor and button platforms first
    # (they register themselves into hass.data[DOMAIN][entry.entry_id]["sensors"])
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Now subscribe to MQTT — sensors are ready to receive messages
    @callback
    def message_received(msg):
        """Handle incoming MQTT messages and forward to all sensors."""
        try:
            payload = json.loads(msg.payload)
            _LOGGER.debug("WhatWatt MQTT message received: %s", payload)

            if not payload.get(ATTR_SYS_ID):
                _LOGGER.warning(
                    "WhatWatt: MQTT message missing 'sys_id' field — "
                    "check your MQTT topic and payload format. Payload: %s", payload
                )
                return

            # Push the payload to every registered sensor
            sensors = hass.data[DOMAIN][entry.entry_id].get("sensors", {})
            for sensor in sensors.values():
                sensor.handle_mqtt_message(payload)

        except json.JSONDecodeError:
            _LOGGER.error("WhatWatt: Invalid JSON received on MQTT topic '%s'", mqtt_topic)
        except Exception as ex:
            _LOGGER.error("WhatWatt: Error processing MQTT message: %s", ex)

    unsubscribe = mqtt.async_subscribe(hass, mqtt_topic, message_received)
    hass.data[DOMAIN][entry.entry_id]["unsubscribe"] = unsubscribe

    _LOGGER.info(
        "WhatWatt integration set up. Listening on MQTT topic: %s", mqtt_topic
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entry_data = hass.data[DOMAIN].get(entry.entry_id, {})

    # Unsubscribe from MQTT
    unsubscribe = entry_data.get("unsubscribe")
    if unsubscribe:
        unsubscribe()

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
