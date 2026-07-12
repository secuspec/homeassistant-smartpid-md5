# SmartPID M5 PRO — Home Assistant Integration

Custom integration for the **SmartPID M5 PRO** (M5Stack, two-channel) thermostat
controller. The device has **no MQTT auto-discovery**, so this integration
publishes Home Assistant MQTT *discovery* configs on its behalf. Home Assistant's
built-in **MQTT integration** then creates the entities and binds them to the
SmartPID's own topics.

## How it works

- You enter the 14-character device **`<id>` hash** (e.g. `6e345245af4904`) in the
  config flow. That is the only variable part of the topics — `smartpidM5/pro` is
  fixed for the PRO model. Both the topic path and the device `identifiers` /
  `unique_id` are derived from it.
- On setup the integration publishes all discovery configs **retained** to
  `homeassistant/<component>/smartpidM5_pro_<id>/<object>/config`.
- **Cleanup** (Options → *Remove discovery topics*) clears every discovery config
  by publishing an **empty payload with `retain=True`** — the spec-compliant way
  to delete a retained message. Removing the integration entirely does the same
  via `async_remove_entry`.

## Requirements

- The Home Assistant **MQTT integration** must be configured and connected.
- Its discovery prefix must be the default `homeassistant` (see `const.py`
  `DISCOVERY_PREFIX` if you changed it).

## Installation / deploy

Copy this folder into your Home Assistant config:

```
<config>/custom_components/smartpid_md5/
```

Then restart Home Assistant and add the integration via
**Settings → Devices & Services → Add Integration → “SmartPID M5 PRO”**.

## Entities (per channel CH1 / CH2)

| Entity | Type | Source / command |
| --- | --- | --- |
| Temperature | sensor | `dynamic/CHx` → `temp` |
| Setpoint (readback) | sensor | `dynamic/CHx` → `SP` |
| Power | sensor (%) | `dynamic/CHx` → `pwm` |
| Mode | sensor | `dynamic/CHx` → `mode` |
| Run Mode | sensor | `dynamic/CHx` → `runmode` |
| Countdown / Countup | sensor (s) | `dynamic/CHx` |
| Setpoint | number | command `{"CHx SP": <value>}` |
| Profile | select (1–10) | command `{"CHx profile": <n>}` |
| Run | switch | on `{"CHx profile":1,"start":"standard"}`, off `{"stop":true}` |

Plus device-level diagnostics (IP, SSID, Serial) from `status` and the last
`events/standard` / `events/advanced` event.

## Notes and known limitations

- **Two payload shapes.** `dynamic/CHx` carries `SP`, `mode`, `pwm`, `countdown`,
  `countup` only in *run* mode; in *monitor* mode those fields are absent. All
  optional fields use `default('')` in the value template, so they read as
  unknown until the device is running.
- **`stop` is global.** The device's stop command halts the whole controller, so
  turning either channel's *Run* switch off stops both channels.
- **No `relay` field on PRO.** (An earlier init script keyed a relay switch on
  `value_json.relay`, which only exists on the MINI model — it never populated on
  the PRO.) The *Run* switch derives state from `runmode` instead; `pwm` shows
  heating power.
- **Availability is not modeled.** The `status` topic is published on-demand only
  (`{"status": true}` command) and the firmware documents no MQTT LWT, so there is
  no reliable connected/disconnected signal. If you want a staleness indicator,
  add `expire_after` to the temperature entities — but only if your device
  publishes `dynamic` data periodically while idle.
- **Temperature unit is assumed °C.** The device also reports `unit`, but MQTT
  discovery unit is static. Change it in `discovery.py` if you run in °F.
