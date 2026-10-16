"""Constants for the Samsung Soundbar Local integration."""

DOMAIN = "samsung_soundbar_local"

CONF_EQ_PRESETS = "eq_presets"

DEFAULT_PORT = 56001
DEFAULT_SCAN_INTERVAL = 10

# Supported input sources according to soundbar_control.py
SOURCES = ["wifi", "bt", "optical", "hdmi1", "hdmi2", "aux", "din"]

# Bass, treble and rear level range of the SmartThings app (HW-Q950T).
LEVEL_MIN = -6
LEVEL_MAX = 6
