# SmartPID M5 PRO

Home Assistant custom integration for the **SmartPID M5 PRO** two-channel
thermostat controller, built for **dual-boiler espresso machines**.

The SmartPID has no MQTT auto-discovery, so this integration publishes the
Home Assistant MQTT discovery configs on its behalf. Home Assistant's MQTT
integration then creates the entities and binds them to the SmartPID's topics.

## What you get

- Each channel maps to one boiler — **CH1 = brew boiler** (default limit 0–98 °C),
  **CH2 = steam boiler** (default limit 0–128 °C).
- Per channel: temperature, setpoint (readback + settable `number`), power (PWM),
  mode, run switch, timers, plus device diagnostics and events.
- **Configurable setpoint limits** per channel via the options flow.
- A ready-made **dashboard** (`dashboards/smartpid-dashboard.yaml`) with a slider,
  a typeable setpoint field and a temperature-history chart with a setpoint ±2 °C
  tolerance band for reading boiler stability.

## Requirements

- An MQTT broker reachable by both Home Assistant and the SmartPID (Mosquitto on
  the HA host is recommended), and the **MQTT integration** configured.
- The SmartPID must be pointed at that broker (address + credentials).
- The dashboard's history charts need the **ApexCharts** card (also from HACS).

See the [README](https://github.com/secuspec/homeassistant-smartpid-md5#readme)
for full step-by-step setup, including how to find your device ID and the exact
entity IDs the dashboard expects.
