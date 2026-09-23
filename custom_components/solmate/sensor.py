"""Sensor platform for Solmate integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_EMAIL,
    CONF_PROVIDER,
    DOMAIN,
    NAME,
    PROVIDER_NAMES,
    SENSOR_BATTERY_SOC,
    SENSOR_BATTERY_STATUS,
    SENSOR_BATT_POWER,
    SENSOR_DAILY_BATT_CHARGE,
    SENSOR_DAILY_BATT_DISCHARGE,
    SENSOR_DAILY_GRID_EXPORT,
    SENSOR_DAILY_GRID_IMPORT,
    SENSOR_DAILY_LOAD,
    SENSOR_DAILY_PV,
    SENSOR_GRID_POWER,
    SENSOR_LOAD_POWER,
    SENSOR_PV_POWER,
    SENSOR_SOLAR_INDEPENDENCE,
    VERSION,
)
from .coordinator import SolmateDataUpdateCoordinator
from .sunsynk_api import EnergyFlowData

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class SolmateSensorEntityDescription(SensorEntityDescription):
    """Describes Solmate sensor entity."""

    value_fn: Callable[[EnergyFlowData, SolmateDataUpdateCoordinator], Any]


SENSOR_DESCRIPTIONS: tuple[SolmateSensorEntityDescription, ...] = (
    # Battery SOC %
    SolmateSensorEntityDescription(
        key=SENSOR_BATTERY_SOC,
        translation_key=SENSOR_BATTERY_SOC,
        name="Battery State of Charge",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, _: round(data.percentage * 100.0, 1),
    ),
    # Solar PV Power (W)
    SolmateSensorEntityDescription(
        key=SENSOR_PV_POWER,
        translation_key=SENSOR_PV_POWER,
        name="Solar Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
        value_fn=lambda data, _: data.pv_power,
    ),
    # Battery Flow (W) - negative is charging, positive is discharging
    SolmateSensorEntityDescription(
        key=SENSOR_BATT_POWER,
        translation_key=SENSOR_BATT_POWER,
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-wireless",
        value_fn=lambda data, _: data.batt_power,
    ),
    # Grid Power (W) - positive is import, negative is export
    SolmateSensorEntityDescription(
        key=SENSOR_GRID_POWER,
        translation_key=SENSOR_GRID_POWER,
        name="Grid Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower",
        value_fn=lambda data, _: data.grid_power,
    ),
    # Household Load Power (W)
    SolmateSensorEntityDescription(
        key=SENSOR_LOAD_POWER,
        translation_key=SENSOR_LOAD_POWER,
        name="Home Load Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:home-lightning-bolt",
        value_fn=lambda data, _: data.load_power,
    ),
    # Daily Solar PV Yield (kWh)
    SolmateSensorEntityDescription(
        key=SENSOR_DAILY_PV,
        translation_key=SENSOR_DAILY_PV,
        name="Daily Solar Yield",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:solar-power-variant",
        value_fn=lambda data, _: data.daily_pv_yield_kwh,
    ),
    # Daily Grid Import (kWh)
    SolmateSensorEntityDescription(
        key=SENSOR_DAILY_GRID_IMPORT,
        translation_key=SENSOR_DAILY_GRID_IMPORT,
        name="Daily Grid Import",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:transmission-tower-import",
        value_fn=lambda data, _: data.daily_grid_import_kwh,
    ),
    # Daily Grid Export (kWh)
    SolmateSensorEntityDescription(
        key=SENSOR_DAILY_GRID_EXPORT,
        translation_key=SENSOR_DAILY_GRID_EXPORT,
        name="Daily Grid Export",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:transmission-tower-export",
        value_fn=lambda data, _: data.daily_grid_export_kwh,
    ),
    # Daily Battery Charge (kWh)
    SolmateSensorEntityDescription(
        key=SENSOR_DAILY_BATT_CHARGE,
        translation_key=SENSOR_DAILY_BATT_CHARGE,
        name="Daily Battery Charge",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-arrow-up",
        value_fn=lambda data, _: data.daily_batt_charge_kwh,
    ),
    # Daily Battery Discharge (kWh)
    SolmateSensorEntityDescription(
        key=SENSOR_DAILY_BATT_DISCHARGE,
        translation_key=SENSOR_DAILY_BATT_DISCHARGE,
        name="Daily Battery Discharge",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-arrow-down",
        value_fn=lambda data, _: data.daily_batt_discharge_kwh,
    ),
    # Daily Home Load (kWh)
    SolmateSensorEntityDescription(
        key=SENSOR_DAILY_LOAD,
        translation_key=SENSOR_DAILY_LOAD,
        name="Daily Home Consumption",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:home-lightning-bolt-outline",
        value_fn=lambda data, _: data.daily_load_kwh,
    ),
    # Solar Independence Score (%)
    SolmateSensorEntityDescription(
        key=SENSOR_SOLAR_INDEPENDENCE,
        translation_key=SENSOR_SOLAR_INDEPENDENCE,
        name="Solar Independence Score",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:shield-sun",
        value_fn=lambda data, _: data.solar_independence_score,
    ),
    # Battery Status / ETA projection (text)
    SolmateSensorEntityDescription(
        key=SENSOR_BATTERY_STATUS,
        translation_key=SENSOR_BATTERY_STATUS,
        name="Battery Status",
        icon="mdi:battery-clock",
        value_fn=lambda data, coord: data.eta_string(coord.battery_capacity_kwh),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Solmate sensors based on a config entry."""
    coordinator: SolmateDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        SolmateSensor(coordinator, description, entry)
        for description in SENSOR_DESCRIPTIONS
    )


class SolmateSensor(CoordinatorEntity[SolmateDataUpdateCoordinator], SensorEntity):
    """Representation of a Solmate sensor entity."""

    _attr_has_entity_name = True
    entity_description: SolmateSensorEntityDescription

    def __init__(
        self,
        coordinator: SolmateDataUpdateCoordinator,
        description: SolmateSensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry

        email = entry.data[CONF_EMAIL]
        provider = entry.data.get(CONF_PROVIDER, "sunsynk")
        provider_name = PROVIDER_NAMES.get(provider, provider)

        self._attr_unique_id = f"solmate_{email.lower()}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, email.lower())},
            name=f"Solmate ({email})",
            manufacturer=f"Solmate / {provider_name}",
            model="Solar & Battery Companion Hub",
            sw_version=VERSION,
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(
            self.coordinator.data, self.coordinator
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            super().available
            and self.coordinator.data is not None
            and self.coordinator.data.is_connected
        )
