# Changelog

All notable changes to the **Solmate for Home Assistant** integration will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
