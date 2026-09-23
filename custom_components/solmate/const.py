"""Constants for the Solmate integration."""

from typing import Final

DOMAIN: Final = "solmate"
NAME: Final = "Solmate"
VERSION: Final = "1.1.2"

# Gateway Configuration
DEFAULT_GATEWAY_URL: Final = "https://api.jonogould.com/solmate"
CONF_GATEWAY_URL: Final = "gateway_url"

# Configuration and options keys
CONF_PROVIDER: Final = "provider"
CONF_EMAIL: Final = "email"
CONF_PASSWORD: Final = "password"
CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_BATTERY_CAPACITY_KWH: Final = "battery_capacity_kwh"

# Supported Providers
PROVIDER_SUNSYNK: Final = "sunsynk"
PROVIDER_DEMO: Final = "demo"

PROVIDER_NAMES = {
    PROVIDER_SUNSYNK: "Sunsynk / Deye Cloud",
    PROVIDER_DEMO: "Demo Simulator",
}

# Defaults
DEFAULT_SCAN_INTERVAL: Final = 60  # seconds (safe for Sunsynk cloud rate limits)
DEFAULT_BATTERY_CAPACITY_KWH: Final = 10.0  # kWh
MIN_SCAN_INTERVAL: Final = 30  # seconds

# Platforms
PLATFORMS: Final = ["sensor"]

# Static web path for Lovelace card
URL_BASE: Final = "/solmate"
CARD_FILENAME: Final = "solmate-card.js"
CARD_URL: Final = f"{URL_BASE}/{CARD_FILENAME}"

# Sensor Keys
SENSOR_BATTERY_SOC: Final = "battery_soc"
SENSOR_PV_POWER: Final = "pv_power"
SENSOR_BATT_POWER: Final = "batt_power"
SENSOR_GRID_POWER: Final = "grid_power"
SENSOR_LOAD_POWER: Final = "load_power"
SENSOR_DAILY_PV: Final = "daily_pv_yield"
SENSOR_DAILY_GRID_IMPORT: Final = "daily_grid_import"
SENSOR_DAILY_GRID_EXPORT: Final = "daily_grid_export"
SENSOR_DAILY_BATT_CHARGE: Final = "daily_batt_charge"
SENSOR_DAILY_BATT_DISCHARGE: Final = "daily_batt_discharge"
SENSOR_DAILY_LOAD: Final = "daily_load"
SENSOR_SOLAR_INDEPENDENCE: Final = "solar_independence"
SENSOR_BATTERY_STATUS: Final = "battery_status"
