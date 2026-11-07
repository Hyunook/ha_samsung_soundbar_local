<p align="center">
  <img src="https://brands.home-assistant.io/samsungtv/logo@2x.png" width="360" alt="Samsung logo">
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
- 🎚️ **Subwoofer, bass, treble and rear level** and 🎼 **equalizer presets read directly from the device**, when the model supports them
- 🎧 **Sound mode** sensor
- 🔍 **SSDP discovery** and setup entirely through the UI
- 🔁 **Reconfigure** the address without removing the device
- 🌍 Translated into English, German and Korean

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
| Subwoofer | `number` | Level from −12 to +6 *(optional)* |
| Bass | `number` | Level from −6 to +6 *(optional)* |
| Treble | `number` | Level from −6 to +6 *(optional)* |
| Rear level | `number` | Level from −6 to +6, only while the rear speakers are on and connected *(optional, assumed state)* |
| Equalizer | `select` | Presets reported by your soundbar *(optional)* |
| Sound mode | `sensor` | Current sound mode, read-only *(optional)* |

Selectable inputs depend on the model:

| Model | Inputs |
| --- | --- |
| HW-Q950T (verified) | `hdmi1`, `hdmi2`, `optical`, `bt` |
| Other models | `hdmi1`, `hdmi2`, `optical`, `bt`, `aux`, `din` |

On the HW-Q950T, `optical` is the value the soundbar reports for the input the
SmartThings app calls **D.IN / TV ARC**; `din` only switches to that same input
and `aux` does not exist. Other models may support `aux` and `din`, or only some
of the inputs. If you know which ones work on your model, please
[open an issue](https://github.com/V4n1X/ha_samsung_soundbar_local/issues).

While Spotify Connect or casting plays, the input shows as `wifi`. It cannot be
selected; the soundbar only enters it from the app.

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
- While Spotify Connect or casting plays, the soundbar does not answer the
  input query, so the input is shown as `wifi` and each update takes about two
  seconds longer. If a model also stops answering the input query during TV
  playback (reported for a TV session, not verified with TV ARC), the input
  may show as `wifi` there too; control keeps working.
- The rear level and the SmartThings app's **Channel volume → Rear** change the
  same speakers, and the last change wins. The soundbar keeps the two values
  apart, though: the rear level only shows what was last set from Home
  Assistant, never a change made in the app. Home Assistant marks it as an
  assumed state. Bass, treble and subwoofer stay in sync with the app. The
  app's other channel levels (center, side, front top, rear top) are not
  available locally.

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

The integration icon contains no Samsung logo. It is based on the
[Material Design Icons](https://pictogrammers.com/library/mdi/) `soundbar`
icon by Pictogrammers, licensed under
[Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0), modified with a
background and equalizer bars.
