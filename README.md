<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://brands.home-assistant.io/samsungtv/dark_logo@2x.png">
    <img src="https://brands.home-assistant.io/samsungtv/logo@2x.png" width="360" alt="Samsung logo">
  </picture>
</p>

<h1 align="center">Samsung Soundbar (Local)</h1>

<p align="center">
  🔊 Local control of Samsung soundbars in Home Assistant — no cloud, no account, no extra packages.
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://github.com/V4n1X/ha_samsung_soundbar_local/releases"><img src="https://img.shields.io/github/v/release/V4n1X/ha_samsung_soundbar_local" alt="Release"></a>
  <img src="https://img.shields.io/badge/Home%20Assistant-2026.9%2B-18BCF2?logo=homeassistant&logoColor=white" alt="Home Assistant 2026.9+">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <br>
  <a href="https://github.com/V4n1X/ha_samsung_soundbar_local/actions/workflows/validate.yml"><img src="https://github.com/V4n1X/ha_samsung_soundbar_local/actions/workflows/validate.yml/badge.svg" alt="Validate"></a>
  <a href="https://github.com/V4n1X/ha_samsung_soundbar_local/actions/workflows/tests.yml"><img src="https://github.com/V4n1X/ha_samsung_soundbar_local/actions/workflows/tests.yml/badge.svg" alt="Tests"></a>
</p>

---

## 📑 Contents

- [✨ Features](#-features)
- [✅ Compatibility](#-compatibility)
- [📦 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [🧩 Entities](#-entities)
- [⚠️ Limitations](#️-limitations)
- [🩺 Troubleshooting](#-troubleshooting)
- [🐛 Reporting issues](#-reporting-issues)
- [🤝 Contributing](#-contributing)
- [📝 Changelog](CHANGELOG.md)
- [📄 License](#-license)

## ✨ Features

- 🏠 **100 % local** – talks directly to the soundbar's HTTP/XML API on port `56001`
- 🎛️ **Media player** – power, volume, mute and input selection
- 🎚️ **Subwoofer level** and 🎼 **equalizer presets read directly from the device**, when the model supports them
- 🎧 **Sound mode** sensor
- 🔍 **SSDP discovery** and setup entirely through the UI
- 🔁 **Reconfigure** the address without removing the device
- 🌍 Translated into English and German

## ✅ Compatibility

| Model | Firmware | Status |
| --- | --- | --- |
| Samsung HW-Q950T | HW-Q950TWWB-1022.0 | ✅ Tested on hardware with Home Assistant 2026.10.1 |

| Home Assistant | Status |
| --- | --- |
| 2026.10.1 | ✅ Tested (hardware and automated tests) |
| 2026.9.4 | ✅ Tested (automated tests, minimum version) |

> [!NOTE]
> Which commands work depends on model, firmware and operating mode. Other
> models have not been verified yet. Reports are welcome.

## 📦 Installation

### HACS (recommended)

[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=V4n1X&repository=ha_samsung_soundbar_local&category=integration)

1. Click the button above, or open **HACS → ⋮ → Custom repositories** and add
   `https://github.com/V4n1X/ha_samsung_soundbar_local` with type **Integration**.
2. Search for **Samsung Soundbar (Local)** and click **Download**.
3. Restart Home Assistant.

### Manual

1. Download the latest release from
   [Releases](https://github.com/V4n1X/ha_samsung_soundbar_local/releases).
2. Copy `custom_components/samsung_soundbar_local/` into the `custom_components/`
   folder of your Home Assistant configuration directory.
3. Restart Home Assistant.

## ⚙️ Configuration

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=samsung_soundbar_local)

Go to **Settings → Devices & services → Add integration** and search for
**Samsung Soundbar (Local)**. Discovered soundbars appear there automatically.

| Setting | Default | Description |
| --- | --- | --- |
| Host | – | IP address or hostname of the soundbar |
| Port | `56001` | Local HTTP API port |
| Update interval | `10` s | Polling interval, minimum 5 seconds |

- 🔁 **Reconfigure** (entry menu ⋮) changes host and port. The new address is
  checked to make sure it is still the same soundbar.
- 🕒 **Configure** changes the update interval.

> [!TIP]
> Give the soundbar a DHCP reservation in your router so its address stays
> stable. A soundbar found again via SSDP at a new address is updated
> automatically.

## 🧩 Entities

| Entity | Type | Description |
| --- | --- | --- |
| Soundbar | `media_player` | Power, volume, mute, input source |
| Subwoofer | `number` | Level from −6 to +6 *(optional)* |
| Equalizer | `select` | Presets reported by your soundbar *(optional)* |
| Sound mode | `sensor` | Current sound mode, read-only *(optional)* |

Available inputs: `wifi`, `bt`, `optical`, `hdmi1`, `hdmi2`, `aux`, `din`.
Your model may accept only some of them.

🎼 **Equalizer presets are read from the device.** The preset list
(`Get7BandEQList`) is fetched when the integration starts and stored with the
config entry. Names and options therefore always match your model and firmware.
If the soundbar is unreachable at startup, the last stored list is used. After a
firmware update, reload the integration to pick up changed presets.

Optional entities become **unavailable** when the soundbar does not support
them. They never show made-up values.

## ⚠️ Limitations

- Uses an unofficial, model-specific local API. SmartThings cloud and
  OCF/DTLS commands are not implemented.
- If the soundbar stops answering in deep standby, its entities become
  unavailable. Turning it on through the API only works while the API is
  reachable.
- Optional commands the device rejects are skipped until the integration
  reloads. Failed optional reads are retried after five minutes.

## 🩺 Troubleshooting

| Problem | What to check |
| --- | --- |
| *Failed to connect* during setup | IP address, port `56001` reachable from Home Assistant, soundbar powered on |
| Soundbar is not discovered | SSDP needs multicast between the soundbar and Home Assistant. Manual setup always works. |
| Subwoofer / equalizer unavailable | Your model or current input does not support it |
| Equalizer entity missing | The preset list could not be read yet. Reload the integration while the soundbar is on. |
| Entities unavailable after a router change | Use **Reconfigure** to enter the new address |

## 🐛 Reporting issues

Open an issue in [GitHub Issues](https://github.com/V4n1X/ha_samsung_soundbar_local/issues)
and include the soundbar model, firmware, Home Assistant version and the
action that failed.

> [!CAUTION]
> Remove IP addresses, MAC addresses, serial numbers and other identifiers from
> logs before sharing them.

## 🤝 Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for tests,
CI and the rules on personal data.

## 📄 License

[MIT](LICENSE) © 2026 V4n1X

This is an independent community project. It is not affiliated with or endorsed
by Samsung. The logo above is loaded from
[Home Assistant Brands](https://github.com/home-assistant/brands) and is not
part of this repository. Samsung names and logos are trademarks of their
respective owners.
