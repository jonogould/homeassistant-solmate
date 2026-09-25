# Changelog

All notable changes to the **Solmate for Home Assistant** integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-09-25

### 🚀 Full Solar Inverter Ecosystem Support
- **Added Support for All 10 Providers**:
  - ☀️ **Sunsynk / Deye Cloud**: Direct cloud API telemetry with RSA PKCS#1 v1.5 auth.
  - ⚡️ **SolarEdge**: Monitoring API integration with power flow and daily solar yield.
  - 🔵 **Victron Energy**: VRM Cloud REST API with live diagnostics and battery state.
  - 🔋 **Tesla Powerwall**: Direct local gateway communication (`/api/system_status/soe` and `/api/meters/aggregates`).
  - ✨ **FoxESS**: Cloud Open API query for real-time solar, battery, grid, and household consumption.
  - 🔌 **GoodWe (SEMS)**: SEMS Portal API integration with live power station telemetry.
  - 🌿 **Growatt**: ShineServer real-time monitoring and daily generation tracking.
  - 🟧 **Enphase (IQ / Envoy)**: Local Envoy gateway telemetry (`/ivp/livedata/status` & `/api/v1/production`).
  - 📡 **Solarman / Sol-Ark**: Open API integration with real-time station metrics.
  - 🎮 **Demo Simulator**: Instant realistic day/night solar generation, battery storage, and grid routing simulation.
- **Provider Architecture**: Clean modular provider architecture in `custom_components/solmate/providers/`.
- **Dynamic Config Flow**: Customized setup forms and validation for each inverter provider.

---

## [1.1.3] - 2026-09-23

### 🔧 Fixes & Improvements
- **Automatic Lovelace Resource Registration**: The custom card is now automatically registered in Home Assistant's Lovelace resources upon integration setup.
- **Dual Static Path & Fallback**: Registered both directory and file endpoints, and added automated sync to `/config/www/solmate-card.js` for seamless `/local/solmate-card.js` fallback.
- **Enhanced Troubleshooting**: Clear guide for addressing "Custom element doesn't exist: solmate-card" and browser caching behavior.

---

## [1.1.2] - 2026-09-23

### ✨ Initial Public Release
- **Real-Time Solar & Battery Monitoring**: Live tracking for solar generation, battery storage, utility grid flow, and household consumption.
- **3D Torus Battery Gauge**: High-resolution circular gauge with battery State of Charge (SOC %) and intelligent Time-to-Full / Time-to-Empty projections.
- **Animated Energy Flow Card**: 4-node animated power routing diagram between solar, battery, grid, and home load.
- **Theme & Appearance Engine**: 6 vibrant glow themes (`electricGold`, `cyberEmerald`, `plasmaCyan`, `solarCrimson`, `ultraViolet`, `titaniumMetal`) and 4 dashboard appearances (`glassDark`, `obsidianOLED`, `pureLight`, `warmWhite`).
- **Zero-Config Bundled Card**: The custom Lovelace card is automatically bundled and served directly by the integration.
- **Demo Simulator Mode**: Built-in simulator to test cards and themes instantly without hardware credentials.
- **Optimized Cloud Telemetry**: Lightweight, efficient cloud updates with built-in rate-limiting protection.
