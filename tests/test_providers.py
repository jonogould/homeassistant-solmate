"""Unit tests for all Solmate solar inverter providers."""

from datetime import datetime, timezone
import json
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock
import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../custom_components/solmate"))
)

from const import (
    CONF_ACCOUNT,
    CONF_API_KEY,
    CONF_APP_ID,
    CONF_APP_SECRET,
    CONF_DEVICE_SN,
    CONF_GATEWAY_IP,
    CONF_PASSWORD,
    CONF_PROVIDER,
    CONF_SITE_ID,
    CONF_STATION_ID,
    CONF_TOKEN,
    CONF_USERNAME,
    PROVIDER_DEMO,
    PROVIDER_ENPHASE,
    PROVIDER_FOXESS,
    PROVIDER_GOODWE,
    PROVIDER_GROWATT,
    PROVIDER_SOLAREDGE,
    PROVIDER_SOLARMAN,
    PROVIDER_SUNSYNK,
    PROVIDER_TESLA,
    PROVIDER_VICTRON,
)
from providers import (
    DemoProvider,
    EnphaseProvider,
    FoxEssProvider,
    GoodWeProvider,
    GrowattProvider,
    SolarEdgeProvider,
    SolarmanProvider,
    SunsynkProvider,
    TeslaProvider,
    VictronProvider,
    get_provider,
)


class MockResponse:
    """Mock aiohttp ClientResponse for testing provider HTTP parsing."""

    def __init__(self, data=None, status=200, text_data=""):
        self._data = data if data is not None else {}
        self.status = status
        self._text = text_data

    async def json(self, *args, **kwargs):
        return self._data

    async def text(self):
        return self._text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


def test_provider_factory_types():
    """Verify that get_provider maps every provider type to the correct class."""
    providers = {
        PROVIDER_SUNSYNK: SunsynkProvider,
        PROVIDER_SOLAREDGE: SolarEdgeProvider,
        PROVIDER_VICTRON: VictronProvider,
        PROVIDER_TESLA: TeslaProvider,
        PROVIDER_FOXESS: FoxEssProvider,
        PROVIDER_GOODWE: GoodWeProvider,
        PROVIDER_GROWATT: GrowattProvider,
        PROVIDER_ENPHASE: EnphaseProvider,
        PROVIDER_SOLARMAN: SolarmanProvider,
        PROVIDER_DEMO: DemoProvider,
    }

    for p_type, expected_cls in providers.items():
        prov = get_provider(p_type, session=None, config={})
        assert isinstance(prov, expected_cls)


@pytest.mark.asyncio
async def test_demo_provider_flow():
    """Verify DemoProvider produces valid normalized EnergyFlowData."""
    provider = DemoProvider(session=None, config={CONF_PROVIDER: PROVIDER_DEMO})
    await provider.test_connection()
    flow = await provider.get_energy_flow()

    assert flow.is_connected is True
    assert 0.0 <= flow.percentage <= 1.0
    assert flow.pv_power is not None
    assert flow.batt_power is not None
    assert flow.grid_power is not None
    assert flow.load_power is not None
    assert flow.daily_pv_yield_kwh == 16.8
    assert 0 <= flow.solar_independence_score <= 100


@pytest.mark.asyncio
async def test_solaredge_provider_flow():
    """Verify SolarEdgeProvider parses power flow and battery status."""
    flow_data = {
        "siteCurrentPowerFlow": {
            "unit": "kW",
            "PV": {"currentPower": 3.5},
            "LOAD": {"currentPower": 1.2},
            "GRID": {"currentPower": 0.3},
            "STORAGE": {"status": "Charging", "currentPower": 2.0, "chargeLevel": 80},
        }
    }
    overview_data = {"overview": {"lastDayData": {"energy": 14200}}}

    session = MagicMock()
    session.get.side_effect = [MockResponse(flow_data), MockResponse(overview_data)]

    provider = SolarEdgeProvider(
        session=session,
        config={CONF_SITE_ID: "123456", CONF_API_KEY: "secret_api_key"},
    )
    flow = await provider.get_energy_flow()

    assert flow.percentage == 0.80
    assert flow.pv_power == 3500.0
    assert flow.batt_power == -2000.0  # Charging is negative
    assert flow.load_power == 1200.0
    assert flow.grid_power == 300.0
    assert flow.daily_pv_yield_kwh == 14.2


@pytest.mark.asyncio
async def test_victron_provider_flow():
    """Verify VictronProvider parses diagnostics records."""
    records = [
        {"description": "Battery state of charge", "rawValue": 75.0},
        {"description": "Solar power", "rawValue": 2100.0},
        {"description": "Battery power", "rawValue": -1500.0},
        {"description": "Grid power", "rawValue": 100.0},
        {"description": "AC Consumption", "rawValue": 700.0},
        {"description": "Today energy yield", "rawValue": 12.8},
    ]
    diag_data = {"records": records, "success": True}

    session = MagicMock()
    session.get.return_value = MockResponse(diag_data)

    provider = VictronProvider(
        session=session,
        config={CONF_SITE_ID: "998877", CONF_TOKEN: "vrm_token"},
    )
    flow = await provider.get_energy_flow()

    assert flow.percentage == 0.75
    assert flow.pv_power == 2100.0
    assert flow.batt_power == -1500.0
    assert flow.grid_power == 100.0
    assert flow.load_power == 700.0
    assert flow.daily_pv_yield_kwh == 12.8


@pytest.mark.asyncio
async def test_tesla_provider_flow():
    """Verify TeslaProvider parses local gateway SOE and meters."""
    soe_data = {"percentage": 92.5}
    meter_data = {
        "solar": {"instant_power": 4200.0},
        "battery": {"instant_power": -2600.0},
        "site": {"instant_power": -600.0},
        "load": {"instant_power": 1000.0},
    }

    session = MagicMock()
    session.get.side_effect = [MockResponse(soe_data), MockResponse(meter_data)]

    provider = TeslaProvider(
        session=session,
        config={CONF_GATEWAY_IP: "192.168.1.150"},
    )
    flow = await provider.get_energy_flow()

    assert flow.percentage == 0.925
    assert flow.pv_power == 4200.0
    assert flow.batt_power == -2600.0
    assert flow.grid_power == -600.0
    assert flow.load_power == 1000.0


@pytest.mark.asyncio
async def test_foxess_provider_flow():
    """Verify FoxEssProvider parses kW telemetry and converts to Watts."""
    fox_data = {
        "errno": 0,
        "result": [
            {
                "datas": [
                    {"variable": "SoC", "value": 68.0},
                    {"variable": "pvPower", "value": 3.8},
                    {"variable": "batChargePower", "value": 2.3},
                    {"variable": "batDischargePower", "value": 0.0},
                    {"variable": "loadsPower", "value": 1.5},
                    {"variable": "gridConsumptionPower", "value": 0.0},
                    {"variable": "generationToday", "value": 15.6},
                ]
            }
        ],
    }

    session = MagicMock()
    session.post.return_value = MockResponse(fox_data)

    provider = FoxEssProvider(
        session=session,
        config={CONF_DEVICE_SN: "SN123456", CONF_API_KEY: "fox_key"},
    )
    flow = await provider.get_energy_flow()

    assert flow.percentage == 0.68
    assert flow.pv_power == 3800.0
    assert flow.batt_power == -2300.0
    assert flow.load_power == 1500.0
    assert flow.daily_pv_yield_kwh == 15.6


@pytest.mark.asyncio
async def test_goodwe_provider_flow():
    """Verify GoodWeProvider logs in and parses station details."""
    login_data = {"code": 0, "data": {"token": "gw_token", "uid": "gw_uid_1", "timestamp": 123456}}
    monitor_data = {
        "data": {
            "soc": 85.0,
            "pac": 3200.0,
            "pdata": {"battery": -2200.0, "load": 950.0, "grid": 50.0},
            "kpi": {"pacToday": 11.4},
        }
    }

    session = MagicMock()
    session.post.side_effect = [MockResponse(login_data), MockResponse(monitor_data)]

    provider = GoodWeProvider(
        session=session,
        config={CONF_ACCOUNT: "user@goodwe.com", CONF_PASSWORD: "pw"},
    )
    flow = await provider.get_energy_flow()

    assert flow.percentage == 0.85
    assert flow.pv_power == 3200.0
    assert flow.batt_power == -2200.0
    assert flow.load_power == 950.0
    assert flow.daily_pv_yield_kwh == 11.4


@pytest.mark.asyncio
async def test_growatt_provider_flow():
    """Verify GrowattProvider parses plant list title."""
    login_resp = MockResponse(text_data='{"result": "success"}')
    plant_data = {"totalData": [{"currentPower": "4.2 kW", "todayEnergy": "18.3 kWh"}]}
    plant_resp = MockResponse(plant_data)

    session = MagicMock()
    session.post.return_value = login_resp
    session.get.return_value = plant_resp

    provider = GrowattProvider(
        session=session,
        config={CONF_USERNAME: "growatt_user", CONF_PASSWORD: "pw"},
    )
    flow = await provider.get_energy_flow()

    assert flow.pv_power == 4200.0
    assert flow.daily_pv_yield_kwh == 18.3


@pytest.mark.asyncio
async def test_enphase_provider_flow():
    """Verify EnphaseProvider parses local Envoy livedata status."""
    envoy_data = {
        "soc": 88.0,
        "meters": {
            "solar": {"agg_p_w": 2900.0},
            "storage": {"agg_p_w": -1900.0, "soc": 88.0},
            "load": {"agg_p_w": 1000.0},
            "grid": {"agg_p_w": 0.0},
        },
    }

    session = MagicMock()
    session.get.return_value = MockResponse(envoy_data)

    provider = EnphaseProvider(
        session=session,
        config={CONF_GATEWAY_IP: "192.168.1.50"},
    )
    flow = await provider.get_energy_flow()

    assert flow.percentage == 0.88
    assert flow.pv_power == 2900.0
    assert flow.batt_power == -1900.0
    assert flow.load_power == 1000.0


@pytest.mark.asyncio
async def test_solarman_provider_flow():
    """Verify SolarmanProvider acquires token and parses real-time station flow."""
    token_data = {"success": True, "access_token": "solarman_token_xyz"}
    station_data = {
        "success": True,
        "data": {
            "generationPower": 5100.0,
            "batteryPower": -3100.0,
            "batterySoc": 95.0,
            "usePower": 1600.0,
            "gridPower": -400.0,
        },
    }

    session = MagicMock()
    session.post.side_effect = [MockResponse(token_data), MockResponse(station_data)]

    provider = SolarmanProvider(
        session=session,
        config={
            CONF_APP_ID: "app_123",
            CONF_APP_SECRET: "secret_xyz",
            CONF_STATION_ID: "776655",
        },
    )
    flow = await provider.get_energy_flow()

    assert flow.percentage == 0.95
    assert flow.pv_power == 5100.0
    assert flow.batt_power == -3100.0
    assert flow.load_power == 1600.0
    assert flow.grid_power == -400.0
