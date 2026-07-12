# SmartPID M5 PRO — Home Assistant Integration

Custom integration for the **SmartPID M5 PRO** (M5Stack, two-channel) thermostat
controller. The device has **no MQTT auto-discovery**, so this integration
publishes Home Assistant MQTT *discovery* configs on its behalf. Home Assistant's
built-in **MQTT integration** then creates the entities and binds them to the
SmartPID's own topics.

## Use case — dual-boiler espresso machines

This integration is built for **dual-boiler espresso machines**, where the
SmartPID M5 PRO's two channels each control one boiler:

- **CH1 → brew boiler** (Brühkessel) — the group-head temperature, typically
  around 90–96 °C. Hence the default setpoint limit of **0–98 °C**.
- **CH2 → steam/service boiler** (Dampfkessel) — for steam and hot water,
  typically around 120–125 °C. Hence the default limit of **0–128 °C**.

The per-channel temperature-history chart (with its setpoint ±2 °C tolerance band)
is meant for exactly this: judging how tightly each boiler holds its target, which
is what determines shot consistency.

> I run this with my **La Marzocco Linea Classic** (a dual-boiler machine)
> retrofitted with a SmartPID M5 PRO. The defaults and the dashboard are tuned for
> that setup, but the limits are configurable for any dual-boiler machine.

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

## Prerequisites

Both must be in place **before** you start:

1. **MQTT integration** configured and connected
   (*Settings → Devices & services → MQTT*). Its discovery prefix must be the
   default `homeassistant` (MQTT → *Configure* → the prefix field). If you use a
   different prefix, change `DISCOVERY_PREFIX` in `const.py` to match.
2. **HACS** installed and working (*Settings → Devices & services → HACS*).

## Installation

Follow the steps **in this order**.

### Step 1 — Find your device ID (the 14-character hash)

Every topic contains a device-specific `<id>` such as `6e345245af4904`. To read it:

1. *Settings → Devices & services → MQTT → Configure*.
2. Under **Listen to a topic**, enter `smartpidM5/pro/#` and press **Start listening**.
3. Power on the SmartPID. Incoming topics look like
   `smartpidM5/pro/6e345245af4904/dynamic/CH1`.
4. The **14 characters** between `smartpidM5/pro/` and the next `/` are your ID.

### Step 2 — Install the integration via HACS (private repository)

1. Open **HACS**.
2. Top-right **⋮ menu → Custom repositories**.
3. **Repository:** `https://github.com/secuspec/homeassistant-smartpid-md5`
   **Type:** `Integration` → **Add**.
   (Private repos work because HACS uses your GitHub account's token; it must be
   the same account that owns the repo, or have read access to it.)
4. Close the dialog, search HACS for **“SmartPID M5 PRO”**, open it → **Download**.
5. **Restart Home Assistant** (*Settings → System → top-right ⋮ → Restart*).

> HACS places the files in `custom_components/smartpid_md5/` for you — no manual
> file copying.

### Step 3 — Add and configure the integration

1. *Settings → Devices & services → **Add integration*** → search
   **“SmartPID M5 PRO”**.
2. Enter the **14-character device ID** from Step 1 (and, optionally, a device
   name) → **Submit**.
3. The entities appear immediately. Optionally set the setpoint limits under
   **Configure** (see *Configurable setpoint limits* below).

### Manual alternative (without HACS)

Copy the `custom_components/smartpid_md5/` folder into
`<config>/custom_components/`, restart Home Assistant, then do Step 3.

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

Every entity gets a deterministic `object_id` (`smartpid_<slug>`), so the bundled
dashboard can reference stable entity ids such as `number.smartpid_ch1_setpoint`.
This is unique for a **single** SmartPID device; a second device would collide and
HA would suffix the ids.

## Configurable setpoint limits

**Settings → Devices & Services → SmartPID M5 PRO → Configure** exposes the
per-channel setpoint range:

| Option | Default |
| --- | --- |
| CH1 minimum / maximum | `0` / `98` °C |
| CH2 minimum / maximum | `0` / `128` °C |

These bound the setpoint `number` entity, so both the dashboard slider and the
numeric input box honor them; the input field won't submit an out-of-range value.
(The bound is enforced in the frontend against the entity's `min`/`max`; the
device firmware accepts a wider range.) Changing the limits re-publishes the
discovery configs automatically.

## Dashboard

`dashboards/smartpid-dashboard.yaml` is a ready-made Lovelace dashboard titled
**“La Marzocco Linea Smartpid M5Pro”** (freely editable). Each channel gets its
own section: current-temperature tile, a **setpoint slider**, a **typeable
numeric setpoint field**, run/mode/power, and a continuous **temperature-history
chart** with a setpoint ±2 °C tolerance band for reading stability.

> **HACS cannot install a dashboard config.** The HACS “Dashboard” type only
> installs frontend *cards* (JavaScript), not a finished dashboard. So the
> integration and the ApexCharts card install via HACS with no file copying, but
> the dashboard itself is pasted **once** into the UI (Step 3 below). This is a
> HACS limitation, not an oversight.

### Step 1 — Install the ApexCharts card via HACS

The history charts need it.

1. Open **HACS** and search for **“ApexCharts Card”** (it is in the default HACS
   store — no custom repository needed).
2. Open it → **Download** → **Restart Home Assistant** (or reload resources).

> If your dashboards run in **YAML mode**, also add the resource manually:
> *Settings → Dashboards → ⋮ → Resources →* `/hacsfiles/apexcharts-card/apexcharts-card.js`,
> type **JavaScript Module**. In the default (UI/storage) mode HACS registers it
> automatically.

### Step 2 — Confirm the entity IDs

The dashboard references fixed entity IDs. After adding the integration, open
**Developer Tools → States** and confirm these ten exist exactly:

```
sensor.smartpid_ch1_temp      sensor.smartpid_ch2_temp
number.smartpid_ch1_setpoint  number.smartpid_ch2_setpoint
switch.smartpid_ch1_run       switch.smartpid_ch2_run
sensor.smartpid_ch1_mode      sensor.smartpid_ch2_mode
sensor.smartpid_ch1_pwm       sensor.smartpid_ch2_pwm
```

If some have a `_2` suffix or a different name (e.g. the device was added with an
**older version** and the old IDs stuck in the registry), **delete the device and
re-add it** (Installation Step 3) so the deterministic IDs are generated — or edit
the entity references in the dashboard YAML to match.

### Step 3 — Add the dashboard

1. *Settings → Dashboards → **Add dashboard** → New dashboard from scratch*, give
   it any title → **Create**.
2. Open it → top-right **✏️ Edit** → **⋮ → Raw configuration editor**.
3. **Select all, delete**, then paste the full contents of
   [`dashboards/smartpid-dashboard.yaml`](https://github.com/secuspec/homeassistant-smartpid-md5/blob/main/dashboards/smartpid-dashboard.yaml)
   → **Save**.

The dashboard’s own `title:` line pre-fills **“La Marzocco Linea Smartpid
M5Pro”**; rename it freely.

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
