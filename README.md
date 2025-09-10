# WattBox 300/700 HTTP Integration for Home Assistant

Custom Home Assistant integration for controlling and monitoring **Snap One WattBox WB-300 / WB-300VB / WB-700 / WB-700CH** models over HTTP.

✨ Features:
- Switch entities for each outlet
- Reset buttons (per outlet + reset all)
- Automatic state updates after reset
- Configurable poll interval
- Works with WB-300-IP-3, WB-300VB-IP-5, WB-700-IPV-12, and WB-700CH-IPV-12

---

## Installation

### 1. Prerequisites
- [HACS](https://hacs.xyz/) installed in Home Assistant
- Your WattBox accessible on the network (IP, username, password)

### 2. Add this repository to HACS
1. In Home Assistant go to **HACS → Integrations**  
2. Click the 3-dot menu (top right) → **Custom repositories**  
3. Paste this URL: https://github.com/Vhern/ha-wattbox-300-700
4. Select **Integration** as the category  
5. Click **Add**

### 3. Install the integration
1. After adding the repo, search for **WattBox 300/700 HTTP** in HACS  
2. Install the latest release (e.g. `0.1.0`)  
3. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**  
2. Search for **WattBox 300/700 HTTP**  
3. Enter:
- **Host** (IP of your WattBox)  
- **Username / Password**  
- **Model** (choose your model)  
- **Scan interval** (seconds between polls, default 10s)  
- **Verify SSL** (leave enabled unless you have self-signed cert issues)

Entities will be created for:
- Each outlet as a switch (`switch.wattbox_outlet_X`)  
- Each outlet reset button  
- Reset all button  

---

## Example Use

- **Turn outlets on/off** directly from Home Assistant UI or automations  
- **Reset stuck devices** via the reset button (updates switches immediately, polls every 1s until restored)  
- **Integrate with HA automations** (e.g., reset your modem if it goes offline)

---

## Known Limitations
- WattBox only reports states via XML polling (`wattbox_info.xml`), no push updates  
- Tested on a firmware WB10.F104 (WB-700-IPV-12)

---

## Issues / Feedback
Open an [issue](https://github.com/Vhern/ha-wattbox-300-700/issues) on GitHub with details. PRs are welcome!

---

## Credits
- Developed by [@Vhern](https://github.com/Vhern)  
- Based on WattBox HTTP API documentation  
