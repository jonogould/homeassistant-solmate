"""Integration test for Solmate config flow, entry setup, and options flow."""

import pytest

from custom_components.solmate.const import (
    CONF_BATTERY_CAPACITY_KWH,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_PROVIDER,
    CONF_SCAN_INTERVAL,
    DOMAIN,
    PROVIDER_DEMO,
    PROVIDER_SUNSYNK,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.mark.asyncio
async def test_demo_config_flow_and_setup(hass):
    """Test full setup flow for demo simulator (Section 1)."""
    # 1. Config flow - user step (select Demo Simulator)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    # Select Demo Simulator - creates entry and triggers setup automatically
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROVIDER: PROVIDER_DEMO},
    )
    assert result["type"] == "create_entry"
    assert result["title"] == "Solmate (Demo Simulator)"
    assert result["data"][CONF_PROVIDER] == PROVIDER_DEMO

    await hass.async_block_till_done()

    # Verify battery state of charge sensor is populated
    state = hass.states.get("sensor.solmate_demo_solmate_app_battery_state_of_charge")
    assert state is not None
    assert state.state != "unavailable"
    soc_val = float(state.state)
    assert 0.0 <= soc_val <= 100.0

    # Verify solar generation sensor
    state_pv = hass.states.get("sensor.solmate_demo_solmate_app_solar_generation")
    assert state_pv is not None
    assert state_pv.state != "unavailable"

    # Test Options Flow
    entry = result["result"]
    options_flow = await hass.config_entries.options.async_init(entry.entry_id)
    assert options_flow["type"] == "form"
    assert options_flow["step_id"] == "init"

    options_result = await hass.config_entries.options.async_configure(
        options_flow["flow_id"],
        {CONF_SCAN_INTERVAL: 45, CONF_BATTERY_CAPACITY_KWH: 15.0},
    )
    assert options_result["type"] == "create_entry"
    await hass.async_block_till_done()
    assert entry.options.get(CONF_SCAN_INTERVAL) == 45
    assert entry.options.get(CONF_BATTERY_CAPACITY_KWH) == 15.0


@pytest.mark.asyncio
async def test_sunsynk_config_flow_credentials_step(hass):
    """Test config flow for Sunsynk / Deye credentials (Section 2)."""
    # Step 1: user step (select Sunsynk)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == "form"
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROVIDER: PROVIDER_SUNSYNK},
    )
    assert result["type"] == "form"
    assert result["step_id"] == "credentials"

    # Step 2: enter credentials with demo email (which uses mock demo handshake)
    result_cred = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "demo-solar@solmate.local",
            CONF_PASSWORD: "testpassword",
            CONF_BATTERY_CAPACITY_KWH: 10.0,
        },
    )
    assert result_cred["type"] == "create_entry"
    assert result_cred["title"] == "Solmate (demo-solar@solmate.local)"

    await hass.async_block_till_done()
    state = hass.states.get("sensor.solmate_demo_solar_solmate_local_battery_state_of_charge")
    assert state is not None
