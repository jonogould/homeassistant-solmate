<div align="center">

<img src="https://raw.githubusercontent.com/jonogould/homeassistant-solmate/main/icon.png" alt="Solmate Logo" width="120" height="120" style="border-radius: 26px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);" />

# ⚡️ Solmate for Home Assistant

### Universal Real-Time Solar & Battery Energy Companion for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=white)](https://github.com/hacs/integration)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2024.1%2B-blue.svg?style=for-the-badge&logo=home-assistant&logoColor=white)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![Release](https://img.shields.io/github/v/release/jonogould/homeassistant-solmate?style=for-the-badge&color=orange)](https://github.com/jonogould/homeassistant-solmate/releases)

<br>

**Solmate brings the signature mobile solar experience directly into your Home Assistant dashboards.**  
Connect your inverter cloud account (Sunsynk / Deye Cloud or instant Demo Simulator) with the exact same credentials used in the Solmate app, and display a stunning **glowing battery torus gauge** with a **live 4-node animated energy flow diagram**.

<br>

<img src="https://raw.githubusercontent.com/jonogould/homeassistant-solmate/main/docs/screenshot.png" alt="Solmate Home Assistant Card Preview" width="100%" style="border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);" />

</div>

---

## 📑 Table of Contents

- [✨ Key Features](#-key-features)
- [📦 Installation via HACS (Recommended)](#-installation-via-hacs-recommended)
- [🛠 Manual Installation](#-manual-installation)
- [⚙️ Inverter Configuration](#️-inverter-configuration)
- [🎨 Lovelace Dashboard Card](#-lovelace-dashboard-card)
  - [Basic Setup](#1-basic-setup-auto-discovers-solmate-sensors)
  - [Custom Themes & Appearance](#2-custom-themes--appearance)
  - [Using with Any Existing Solar Sensors](#3-use-with-any-existing-solar-sensors-solaredge-tesla-etc)
- [📊 Exposed Sensor Entities](#-exposed-sensor-entities)
- [💡 Supported Inverters](#-supported-inverters)
- [📝 Changelog](CHANGELOG.md)
- [📄 License](#-license)

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| 🔋 **3D Torus Battery Gauge** | High-DPI circular gauge with glowing gradient accents, live State of Charge (SOC %), and adaptive charge/discharge status indicators. |
| ⏱ **Intelligent Battery ETA** | Real-time Time-to-Full and Time-to-Empty projections calculated dynamically from live power flow and battery capacity. |
| ⚡️ **Live 4-Node Energy Flow** | Interactive particle current animation visualizing real-time power routing between **Solar PV**, **Battery Storage**, **Utility Grid**, and **Home Load**. |
| 📊 **Solar Independence Score** | Quantifies your percentage of self-reliance from solar and battery reserves vs. utility grid imports in real time. |
| 🎨 **6 Vibrant Glow Themes** | `electricGold`, `cyberEmerald`, `plasmaCyan`, `solarCrimson`, `ultraViolet`, and `titaniumMetal`. |
| 🌓 **4 Tailored Appearances** | Seamlessly matches your dashboard: `glassDark`, `obsidianOLED`, `pureLight`, and `warmWhite`. |
| 🚀 **Zero-Config Bundled Card** | The backend integration automatically serves the frontend custom card at `/solmate/solmate-card.js`. No separate card repository needed! |
| 🔌 **Universal Compatibility** | Can be used as a standalone card with **any** solar inverter setup in Home Assistant (Tesla, SolarEdge, Enphase, Victron, etc.). |

---

## 📦 Installation via HACS (Recommended)

Installing through [HACS (Home Assistant Community Store)](https://hacs.xyz/) is the easiest method and enables one-click updates:

### Step 1: Add the Custom Repository
1. Open your Home Assistant dashboard and navigate to **HACS**.
2. Click the **three dots (⋮)** in the top right corner and select **Custom repositories**.
3. Fill in the modal fields:
   - **Repository**: `https://github.com/jonogould/homeassistant-solmate`
   - **Type / Category**: Select **`Integration`** (recommended for all-in-one backend + frontend card) or **`Dashboard`** (if installing the standalone Lovelace card)
4. Click **Add**.

### Step 2: Download the Integration
1. Search for **Solmate** in HACS.
2. Click **Solmate Solar & Battery Integration**.
3. Click the **Download** button in the bottom right.
4. When prompted, restart Home Assistant (**Settings** ➔ **System** ➔ **Restart**).

> [!TIP]
> **All-In-One Package**: Installing as an **Integration** via HACS automatically downloads and serves the custom Lovelace card (`solmate-card.js`) directly from your local Home Assistant instance at `/solmate/solmate-card.js`!

---

## 🛠 Manual Installation

If you do not use HACS, you can install the integration manually:

1. Download the latest release from the [Releases page](https://github.com/jonogould/homeassistant-solmate/releases).
2. Copy the `custom_components/solmate` folder into your Home Assistant config directory:
   ```bash
   /config/custom_components/solmate/
   ```
3. Restart Home Assistant.

---

## ⚙️ Inverter Configuration

Once installed, connect your inverter account through the standard Home Assistant UI:

1. Go to **Settings** ➔ **Devices & Services**.
2. Click **Add Integration** in the bottom right corner.
3. Search for **Solmate** and select it.
4. Select your provider:
   - **Sunsynk / Deye Cloud**: Enter the **Email** and **Password** you use for the Sunsynk Connect or Solmate mobile app.
   - **Demo Simulator**: Instant simulated solar and battery telemetry to test themes and cards without hardware.
5. Set your **Battery Capacity** (default: `10.0` kWh) for accurate Time-to-Full and Time-to-Empty estimations.
6. Click **Submit**!

Your solar inverter will appear in your Device Registry with all 13 real-time sensors automatically configured.

---

## 🎨 Lovelace Dashboard Card

### Add the Resource

> [!NOTE]
> **Automatic Registration**: Starting with v1.1.3, when you add the Solmate integration under **Settings ➔ Devices & Services**, the card resource `/solmate/solmate-card.js` is **automatically registered** for you!
>
> If you are setting up manually or using the card standalone with another inverter:
> Go to **Settings** ➔ **Dashboards** ➔ **three dots (⋮)** ➔ **Resources** ➔ **Add Resource**:
> - **URL**: `/solmate/solmate-card.js` (or `/local/solmate-card.js`)
> - **Resource type**: `JavaScript Module`

---

### Card Configuration Examples

Edit your dashboard, click **Add Card**, select **Manual**, and paste one of the examples below:

#### 1. Basic Setup (Auto-discovers Solmate sensors)
```yaml
type: custom:solmate-card
theme: electricGold
appearance: glassDark
```

#### 2. Custom Themes & Appearance
```yaml
type: custom:solmate-card
title: "Solar Reserve Hub"
theme: cyberEmerald          # Options: electricGold, cyberEmerald, plasmaCyan, solarCrimson, ultraViolet, titaniumMetal
appearance: obsidianOLED     # Options: glassDark, obsidianOLED, pureLight, warmWhite
battery_capacity: 10.0        # Battery capacity in kWh (used for ETA calculations)
show_flow: true               # Show/hide 4-node animated energy diagram
show_stats: true              # Show/hide daily yield & independence footer
```

#### 3. Use with Any Existing Solar Sensors (SolarEdge, Tesla, etc.)
If you already have solar entities from another integration, map them directly into the Solmate card:
```yaml
type: custom:solmate-card
title: "My Home Energy"
theme: plasmaCyan
appearance: pureLight
battery_soc: sensor.battery_percentage
solar_power: sensor.solar_power_w
battery_power: sensor.battery_flow_w          # Negative = charging, positive = discharging
grid_power: sensor.grid_feed_in_w             # Positive = import, negative = export
load_power: sensor.household_power_w
daily_pv: sensor.daily_solar_generation_kwh
solar_independence: sensor.solar_self_sufficiency_pct
```

---

## ❓ Troubleshooting: "Custom element doesn't exist: solmate-card"

If you see this error when adding the card, follow these quick steps:

1. **Did you add the integration under Devices & Services?**
   - In Home Assistant, an integration's backend code only runs **after** you add it via **Settings ➔ Devices & Services ➔ Add Integration ➔ Solmate**.
   - If you downloaded via HACS but haven't added the integration yet, the `/solmate/solmate-card.js` web endpoint is not active yet! Add the integration (you can choose **Demo Simulator** if you just want to test).

2. **Did you restart Home Assistant?**
   - After installing any new integration in HACS, a Home Assistant restart is required (**Settings ➔ System ➔ Restart**).

3. **Hard-refresh your browser cache!**
   - Browsers aggressively cache failed JavaScript module loads. Even once the server is ready, the browser won't retry loading until you force refresh:
     - **Mac**: `Cmd` + `Shift` + `R`
     - **Windows / Linux**: `Ctrl` + `F5`
     - **HA Mobile App**: Pull down from the top to refresh, or clear app cache in Settings.

4. **Verify the script loads directly:**
   - In your browser, open `http://<YOUR_HA_IP>:8123/solmate/solmate-card.js`.
   - If it displays the JavaScript code, the server is running properly. Hard-refresh your dashboard and the card will appear!


## 📊 Exposed Sensor Entities

The integration creates 13 first-class Home Assistant sensors grouped under the **Solmate Solar System** device:

| Sensor Entity | Name | Unit | Device Class | State Class |
| :--- | :--- | :---: | :---: | :---: |
| `sensor.solmate_battery_state_of_charge` | Battery State of Charge | `%` | `battery` | `measurement` |
| `sensor.solmate_solar_power` | Solar Generation Power | `W` | `power` | `measurement` |
| `sensor.solmate_battery_power` | Battery Power Flow | `W` | `power` | `measurement` |
| `sensor.solmate_grid_power` | Utility Grid Power | `W` | `power` | `measurement` |
| `sensor.solmate_load_power` | Home Load Consumption | `W` | `power` | `measurement` |
| `sensor.solmate_daily_solar_yield` | Daily Solar Yield | `kWh` | `energy` | `total_increasing` |
| `sensor.solmate_daily_grid_import` | Daily Grid Import | `kWh` | `energy` | `total_increasing` |
| `sensor.solmate_daily_grid_export` | Daily Grid Export | `kWh` | `energy` | `total_increasing` |
| `sensor.solmate_daily_batt_charge` | Daily Battery Charge | `kWh` | `energy` | `total_increasing` |
| `sensor.solmate_daily_batt_discharge` | Daily Battery Discharge | `kWh` | `energy` | `total_increasing` |
| `sensor.solmate_daily_load` | Daily Home Energy Consumed | `kWh` | `energy` | `total_increasing` |
| `sensor.solmate_solar_independence` | Solar Independence Score | `%` | - | `measurement` |
| `sensor.solmate_battery_status` | Battery Status & ETA | - | - | - |

---

## 💡 Supported Inverters

- ☀️ **Sunsynk & Deye**: Direct cloud integration with real-time power flow telemetry and battery status.
- 🎮 **Demo Simulator**: Instant realistic day/night solar generation, battery storage, and grid routing simulation for dashboard testing.
- 🔌 **Extensible Provider Architecture**: Designed to easily add SolarEdge, Victron VRM, Solarman, GoodWe, and FoxESS in upcoming updates.

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

Developed with ⚡️ by [Jono Gould](https://github.com/jonogould).
