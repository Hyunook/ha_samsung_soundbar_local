# Samsung Soundbar (Local)

Local Samsung soundbar control for **Home Assistant 2026.9 or newer**.
Communicates directly with the soundbar's HTTP/XML API on port **56001**.
No SmartThings account, cloud token, or additional Python package is required.

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=V4n1X&repository=ha_samsung_soundbar_local&category=integration)
[![Release](https://img.shields.io/github/v/release/V4n1X/ha_samsung_soundbar_local)](https://github.com/V4n1X/ha_samsung_soundbar_local/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## Features

| Entity | Function |
| --- | --- |
| Media player | Power, volume, mute and input selection |
| Sound mode sensor | Current sound mode, when supported |
| Subwoofer number | Level from -6 to +6, when supported |
| Equalizer select | NONE, POP, JAZZ and CLASSIC presets, when supported |

Configuration is through the Home Assistant UI. Supported devices may also
be discovered through SSDP. All entities share one polling coordinator.

## Compatibility

| Model | Firmware | Verification |
| --- | --- | --- |
| Samsung HW-Q950T | HW-Q950TWWB-1022.0 | Local API previously verified |

The release is checked against Home Assistant **2026.9.4** using simulated
device responses. This is separate from hardware testing: availability of
individual commands depends on model, firmware and operating mode. Other
models have not been verified.

## Install with HACS

1. Open **HACS → ⋮ → Custom repositories**.
2. Add `https://github.com/V4n1X/ha_samsung_soundbar_local` with type **Integration**.
3. Find **Samsung Soundbar (Local)** and download the latest release.
4. Restart Home Assistant.
5. Open **Settings → Devices & services → Add integration** and search for
   **Samsung Soundbar (Local)**.
6. Enter the soundbar's IP address or hostname and confirm.

The button above opens this repository in HACS. This integration is distributed
as a custom repository; it does not require inclusion in the default HACS catalog.

### Manual installation

Download the source archive from [Releases](https://github.com/V4n1X/ha_samsung_soundbar_local/releases).
Copy `custom_components/samsung_soundbar_local/` into your Home Assistant
configuration directory's `custom_components/` folder, including `brand/` and
`translations/`. Restart Home Assistant and follow steps 5–6 above.

## Configuration

| Setting | Default | Description |
| --- | --- | --- |
| Host | Required | Soundbar IP address or hostname |
| Port | 56001 | Local HTTP API port |
| Update interval | 10 seconds | Polling interval; minimum 5 seconds |

Use the integration's **Configure** action to change these settings. Connection
changes are validated against the original device identity and automatically
reload the integration. A DHCP reservation is recommended.

Home Assistant must be able to reach the soundbar's configured TCP port.
SSDP discovery additionally depends on multicast reaching Home Assistant;
manual setup works without discovery.

## Limitations and troubleshooting

- This uses an unofficial, model-specific local API. SmartThings cloud and
  OCF/DTLS commands are not implemented.
- Input choices are `wifi`, `bt`, `optical`, `hdmi1`, `hdmi2`, `aux` and `din`.
  Your model may accept only a subset.
- Sound mode is read-only. EQ and subwoofer support is optional. Unsupported
  entities are unavailable rather than reporting fabricated values.
- Explicitly rejected optional reads are skipped until the integration reloads.
  Failed optional reads are retried after five minutes; core controls continue
  updating. The initial probe may take longer on unsupported devices.
- If the soundbar stops responding in standby, its entities become unavailable.
  Wake-up through the HTTP API is possible only while that API remains reachable.
- If setup fails, check the address, TCP port and network reachability. Some
  models do not expose this API. A device that answers HTTP but rejects a command
  does not necessarily support the remaining features.

Report problems through [GitHub Issues](https://github.com/V4n1X/ha_samsung_soundbar_local/issues),
including model, firmware, Home Assistant version and the failing action.
Remove device identifiers, addresses and credentials from logs before sharing.

## License

[MIT](LICENSE), copyright © 2026 V4n1X.

Independent community project, not affiliated with or endorsed by Samsung.
Samsung names and logos are trademarks of their respective owners; the software
license does not grant rights to those trademarks.
