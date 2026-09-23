"""Unit tests for the Solmate API client and calculation models."""

from datetime import datetime, timezone
import os
import sys
import unittest

# Import the module under test
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../custom_components/solmate"))
)

from sunsynk_api import EnergyFlowData, SolmateApiClient, SunsynkApiClient


class TestSolmateApi(unittest.IsolatedAsyncioTestCase):
    """Test suite for Solmate gateway API client and energy models."""

    def test_eta_calculation_charging(self):
        """Verify ETA calculation when battery is actively charging."""
        model = EnergyFlowData(
            percentage=0.50,
            is_connected=True,
            last_updated=datetime.now(timezone.utc),
            batt_power=-2500.0,  # 2.5 kW charging
        )
        # Remaining: 50% of 10kWh = 5000 Wh / 2500 W = 2.0 hours
        self.assertEqual(model.eta_string(battery_capacity_kwh=10.0), "Full in 2h")

    def test_eta_calculation_discharging(self):
        """Verify ETA calculation when battery is discharging."""
        model = EnergyFlowData(
            percentage=0.50,
            is_connected=True,
            last_updated=datetime.now(timezone.utc),
            batt_power=1000.0,  # 1 kW discharging
        )
        # Usable: (0.50 - 0.10) * 10000 Wh = 4000 Wh / 1000 W = 4.0 hours
        self.assertEqual(model.eta_string(battery_capacity_kwh=10.0), "4h left")

    def test_eta_calculation_full(self):
        """Verify ETA calculation when battery is 100% full."""
        model = EnergyFlowData(
            percentage=1.0,
            is_connected=True,
            last_updated=datetime.now(timezone.utc),
            batt_power=-50.0,
        )
        self.assertEqual(model.eta_string(), "Fully Charged")

    def test_solar_independence_score(self):
        """Verify self-sufficiency ratio calculation."""
        model = EnergyFlowData(
            percentage=0.85,
            is_connected=True,
            last_updated=datetime.now(timezone.utc),
            daily_load_kwh=10.0,
            daily_grid_import_kwh=2.0,  # 8 kWh self-supplied -> 80%
        )
        self.assertEqual(model.solar_independence_score, 80)

    async def test_demo_login_and_flow(self):
        """Verify demo account bypass and flow synthesis."""
        client = SolmateApiClient()
        token = await client.login("demo@solmate.app", "any_password")
        self.assertEqual(token, "demo_token")
        self.assertEqual(client.plant_id, 9999)

        flow = await client.get_realtime_flow()
        self.assertTrue(flow.is_connected)
        self.assertGreaterEqual(flow.percentage, 0.0)
        self.assertLessEqual(flow.percentage, 1.0)
        self.assertIsNotNone(flow.load_power)
        await client.close()

    def test_backwards_compatibility_alias(self):
        """Verify SunsynkApiClient is an alias for SolmateApiClient."""
        self.assertIs(SunsynkApiClient, SolmateApiClient)


if __name__ == "__main__":
    unittest.main()
