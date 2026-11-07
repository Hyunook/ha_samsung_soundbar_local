"""Constants for the Samsung Soundbar Local integration."""

DOMAIN = "samsung_soundbar_local"

CONF_EQ_PRESETS = "eq_presets"

DEFAULT_PORT = 56001
DEFAULT_SCAN_INTERVAL = 10

# Inputs offered for models that have not been verified.
SOURCES = ["hdmi1", "hdmi2", "optical", "bt", "aux", "din"]

# Inputs verified per model. On the HW-Q950T "optical" is the D.IN / TV ARC
# input, "din" only reports back as "optical" and "aux" never answers.
MODEL_SOURCES = {
    "HW-Q950T": ["hdmi1", "hdmi2", "optical", "bt"],
}

# Reported while Spotify Connect or casting plays; only the app can start it.
NETWORK_SOURCE = "wifi"
