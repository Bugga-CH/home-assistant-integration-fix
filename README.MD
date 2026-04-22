# WhatWatt Home Assistant Integration

Custom Home Assistant integration for WhatWatt Go devices that read data from electricity meters via MQTT.

![WhatWatt Logo](https://avatars.githubusercontent.com/u/201613898?s=200&v=4)

---

## Was macht diese Integration?

Die WhatWatt Go Integration empfängt Messdaten deines WhatWatt Go Geräts über MQTT und stellt sie in Home Assistant als Sensoren zur Verfügung. Du siehst damit in Echtzeit:

- **Leistung** (Watt): Bezug und Einspeisung
- **Energie** (kWh): Gesamtbezug und Einspeisung
- **Spannung** (Volt): L1, L2 und L3

---

## Voraussetzungen

### 1. MQTT Broker
Du brauchst einen laufenden MQTT Broker. Empfohlen wird das **Mosquitto Add-on** direkt in Home Assistant:

1. Geh zu **Einstellungen → Add-ons → Add-on Store**
2. Suche nach „Mosquitto broker" und installiere es
3. Starte das Add-on und aktiviere „Start bei Systemstart"

### 2. MQTT Integration in Home Assistant
1. Geh zu **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Suche nach „MQTT" und folge dem Einrichtungsassistenten
3. Wenn du Mosquitto verwendest, erkennt HA es automatisch

### 3. WhatWatt Go Gerät
Dein WhatWatt Go muss so konfiguriert sein, dass es Daten an deinen MQTT Broker sendet (siehe unten).

---

## WhatWatt Go Gerät konfigurieren

Öffne die Web-Oberfläche deines WhatWatt Go Geräts im Browser (z.B. `http://192.168.1.100`) und konfiguriere die MQTT-Einstellungen:

| Einstellung | Wert (Beispiel) |
|---|---|
| Broker URL | `mqtt://192.168.1.101` |
| Port | `1883` |
| Topic | `whatwatt/meingeraet` |
| Format | JSON |

Das Gerät muss Daten im folgenden JSON-Format senden:

```json
{
  "sys_id": "abc123",
  "power_in": 1234.5,
  "power_out": 0.0,
  "energy_in": 5678.9,
  "energy_out": 12.3,
  "voltage_l1": 230.1,
  "voltage_l2": 229.8,
  "voltage_l3": 231.2
}
```

> ⚠️ **Wichtig:** Das Feld `sys_id` ist zwingend erforderlich. Ohne dieses Feld werden MQTT-Nachrichten ignoriert und es erscheinen keine Sensoren.

Die anderen Felder sind optional — fehlt ein Feld, wird der zugehörige Sensor als „Nicht verfügbar" angezeigt.

---

## Installation

### Option 1: HACS (empfohlen)

1. Öffne HACS in deiner Home Assistant Instanz
2. Gehe zu **Integrationen**
3. Klicke auf die drei Punkte oben rechts → **Benutzerdefinierte Repositories**
4. Füge folgende URL hinzu und wähle Kategorie „Integration":
   ```
   https://github.com/whatwatt-ch/home-assistant-integration
   ```
5. Suche in HACS nach „WhatWatt" und klicke auf **Herunterladen**
6. Starte Home Assistant neu

### Option 2: Manuell

1. Lade dieses Repository herunter oder klone es:
   ```bash
   git clone https://github.com/whatwatt-ch/home-assistant-integration.git
   ```
2. Kopiere den Ordner `custom_components/whatwatt` in dein HA-Konfigurationsverzeichnis:
   ```
   /config/custom_components/whatwatt/
   ```
3. Starte Home Assistant neu

---

## Integration einrichten

1. Geh zu **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Suche nach „WhatWatt"
3. Fülle die Felder aus:

| Feld | Beschreibung | Beispiel |
|---|---|---|
| MQTT Topic | Das Topic, auf dem dein Gerät sendet | `whatwatt/meingeraet` |
| Geräte-IP | IP-Adresse deines WhatWatt Go | `192.168.1.100` |
| Name | Anzeigename in Home Assistant | `Stromzähler` |

4. Klicke auf **Absenden**

Nach dem Einrichten erscheinen die Sensoren automatisch sobald die erste MQTT-Nachricht empfangen wird.

---

## Sensoren & Entities

Nach erfolgreicher Einrichtung erstellt die Integration folgende Entities:

| Entity | Einheit | Beschreibung |
|---|---|---|
| `sensor.X_power_in` | W | Aktueller Strombezug |
| `sensor.X_power_out` | W | Aktuelle Einspeisung |
| `sensor.X_energy_in` | kWh | Gesamtbezug |
| `sensor.X_energy_out` | kWh | Gesamteinspeisung |
| `sensor.X_voltage_l1` | V | Spannung Phase 1 |
| `sensor.X_voltage_l2` | V | Spannung Phase 2 |
| `sensor.X_voltage_l3` | V | Spannung Phase 3 |
| `button.X_configuration` | — | Öffnet die Geräte-Weboberfläche |

---

## Überprüfung / Fehlersuche

**Kommen MQTT-Nachrichten an?**
Geh zu **Entwicklerwerkzeuge → MQTT** und abonniere dein Topic (z.B. `whatwatt/#`). Du solltest dort live die JSON-Nachrichten deines Geräts sehen.

**Erscheinen keine Sensoren?**
- Prüfe ob `sys_id` in der MQTT-Nachricht vorhanden ist
- Stelle sicher dass das Topic in der Integration exakt dem Topic entspricht, auf dem das Gerät sendet
- Schau in **Einstellungen → System → Protokolle** nach Fehlermeldungen von `custom_components.whatwatt`

**MQTT nicht verfügbar?**
Die Integration zeigt eine Benachrichtigung wenn MQTT nicht eingerichtet ist. Richte zuerst die MQTT Integration ein und starte HA danach neu.

---

## Test-Skript

Um die Integration ohne echtes Gerät zu testen, kannst du das mitgelieferte Skript verwenden:

```bash
cd custom_components/whatwatt
pip install paho-mqtt
./test_mqtt_publish.py --broker localhost --port 1883 --topic whatwatt/test --interval 10
```

---

## Lizenz

MIT License — siehe LICENSE Datei.

## Support

Bei Problemen oder Fragen bitte ein Issue auf [GitHub](https://github.com/whatwatt-ch/home-assistant-integration/issues) eröffnen.
