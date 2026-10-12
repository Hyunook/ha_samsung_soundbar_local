# 📝 Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
the project uses [Semantic Versioning](https://semver.org/).

## [1.1.2] - 2026-10-12

No functional changes to the integration.

### 🎨 Changed

- 🖼️ The integration icon (`brand/icon.png`, `brand/icon@2x.png`) no longer
  shows the Samsung logo. It is replaced by a neutral soundbar icon based on the
  Material Design Icons `soundbar` icon (Pictogrammers, Apache 2.0). The
  repository contains no Samsung logos; the README logo is linked from
  [Home Assistant Brands](https://github.com/home-assistant/brands).
- 🔒 The privacy check and tests only allow these two icon files as images.

## [1.1.1] - 2026-10-12

No functional changes to the integration.

### 👷 CI

- ✅ GitHub Actions for the HACS validation and hassfest (push, pull request, daily).
- 🧪 Integration tests in the official Home Assistant container, on the
  minimum version (2026.9.4) and the latest stable release.
- 🚨 Ruff lint and format checks.
- 🔒 Privacy check in CI that blocks personal data and secrets.
- ⬆️ Dependabot for GitHub Actions.

### 📝 Documentation

- 🤝 `CONTRIBUTING.md` with test, CI and personal data rules.
- 🐛 Issue templates for bug reports and feature requests.
- 🏷️ CI status badges in the README.

## [1.1.0] - 2026-10-12

Tested with Home Assistant **2026.10.1** on a Samsung HW-Q950T and with
automated tests on 2026.10.1 and 2026.9.4.

### ✨ Added

- 🎼 Equalizer presets are read from the soundbar (`Get7BandEQList`) instead of
  being hard-coded. The list is refreshed on every start and stored with the
  config entry, so it is still available if the soundbar is offline at startup.
- 🔁 **Reconfigure** flow to change host and port. The new address must belong
  to the same soundbar.
- 🔍 A known soundbar discovered via SSDP at a new address is updated
  automatically. A manual setup with a known address is no longer added twice.
- 🌍 Translated error messages for failed commands and invalid input sources.
- 💬 Field descriptions in all setup dialogs.
- 🎨 Entity icons defined in `icons.json`.

### ♻️ Changed

- ⚙️ **Configure** (options) now only contains the update interval. Host and
  port moved to **Reconfigure**. Existing entries are migrated automatically.
- 🏷️ Subwoofer and equalizer names are translated. Both are now
  configuration entities.
- 🧱 Shared base entity for device info, unique IDs and command handling.
- 🚦 Commands are sent one at a time per platform (`PARALLEL_UPDATES`).
- 📖 README restructured with compatibility, entity and troubleshooting
  sections.

### 🐛 Fixed

- Failed commands are shown as a clear Home Assistant error instead of an
  unhandled exception.
- Subwoofer, equalizer and sound mode entities used inconsistent device info.

### ⚠️ Upgrade notes

- The equalizer options are now the names reported by the device. On the
  HW-Q950T they are unchanged (`NONE`, `POP`, `JAZZ`, `CLASSIC`). Other models
  may report different names, so check automations that use
  `select.select_option` on the equalizer.
- If the preset list has never been read (soundbar unreachable on first start),
  the equalizer entity is not created. Reload the integration while the
  soundbar is on.

## [1.0.0] - 2026-10-12

### ✨ Added

- 🎉 Initial release.
- 🎛️ Media player with power, volume, mute and input selection.
- 🎚️ Subwoofer level, 🎼 equalizer preset and 🎧 sound mode entities.
- 🔍 SSDP discovery and UI setup.
- 🏠 Fully local communication with the soundbar's HTTP/XML API on port 56001.

[1.1.2]: https://github.com/V4n1X/ha_samsung_soundbar_local/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/V4n1X/ha_samsung_soundbar_local/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/V4n1X/ha_samsung_soundbar_local/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/V4n1X/ha_samsung_soundbar_local/releases/tag/v1.0.0
