# DNS Manager - Windows 11

A modern PyQt6 GUI application for managing DNS profiles on Windows 11. This tool allows you to easily view, test, and apply DNS server configurations from various providers worldwide.

![DNS Manager](https://img.shields.io/badge/Platform-Windows%2011-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![PyQt6](https://img.shields.io/badge/PyQt6-6.x-purple)

## Features

- 📊 **Real-time DNS Status** - Display current IPv4 and IPv6 DNS settings
- 🌍 **Multiple DNS Providers** - Pre-configured profiles from Google, Cloudflare, Quad9, Cisco, Yandex, and more
- 🏓 **Ping Testing** - Test latency for each DNS server in separate threads
- 🎨 **Modern UI** - Beautiful dark theme with color-coded tiles
- ⚡ **Quick Apply** - One-click DNS profile application
- 🔄 **Auto-Update** - Reload profiles from online source
- 🔧 **DHCP Reset** - Easily reset to automatic DNS configuration
- 👤 **Admin Check** - Automatic administrator privilege verification

## Supported DNS Types

- **IPv4** - Traditional DNS servers (17+ profiles)
- **IPv6** - Next-generation DNS servers (15+ profiles)
- **DNS64** - NAT64 compatible DNS servers (3+ profiles)

## Included DNS Providers

| Provider | IPv4 | IPv6 | DNS64 |
|----------|------|------|-------|
| Google | ✅ | ✅ | ✅ |
| Cloudflare/APNIC | ✅ | ✅ | ✅ |
| Quad9 | ✅ | ✅ | ❌ |
| Cisco OpenDNS | ✅ | ✅ | ❌ |
| Yandex | ✅ | ✅ | ❌ |
| GCore | ✅ | ✅ | ❌ |
| DNS.SB | ✅ | ✅ | ❌ |
| dns0.eu | ✅ | ✅ | ❌ |
| Hurricane Electric | ✅ | ✅ | ❌ |
| And more... | ✅ | ✅ | ✅ |

## Requirements

- **Operating System**: Windows 11
- **Python**: 3.8 or higher
- **Dependencies**:
  - PyQt6
  - qt-material (optional, for enhanced theming)

## Installation

### 1. Clone or Download

```bash
git clone <repository-url>
cd <project-directory>
```

Or download and extract the ZIP file to your desired location.

### 2. Install Dependencies

```bash
pip install PyQt6 qt-material
```

## Usage

### Method 1: Using the Batch File (Recommended)

Double-click `Run_DNS_tool.bat` to launch the application with administrator privileges.

The batch file will:
- Automatically request administrator rights
- Detect your Python installation
- Launch the DNS Manager GUI

### Method 2: Command Line

1. Open Command Prompt or PowerShell as Administrator
2. Navigate to the project directory
3. Run:

```bash
python dns_manager_gui.py
```

## Application Overview

### Main Window Components

1. **Current DNS Status Panel**
   - Displays active IPv4 and IPv6 DNS servers
   - Refresh button to update status

2. **Control Buttons**
   - **Reload Profiles**: Fetches latest DNS data from the online source
   - **Reset to DHCP**: Restores automatic DNS configuration
   - **Refresh DNS Status**: Updates the current DNS display

3. **DNS Profiles Grid**
   - Color-coded tiles by type (Purple: IPv4, Blue: IPv6, Green: DNS64)
   - Shows primary and secondary DNS addresses
   - Real-time ping test results
   - Apply button for each profile

### Ping Test Results

The application displays ping quality with color indicators:
- 🟢 **Green** (< 50ms): Excellent
- 🟡 **Yellow** (50-100ms): Good
- 🔴 **Red** (> 100ms or failed): Poor/Failed

## File Structure

```
dns-manager/
├── dns_manager_gui.py      # Main GUI application
├── extract_dns.py          # DNS profile extraction script
├── dns_profiles.json       # DNS profiles database
├── Run_DNS_tool.bat        # Windows launcher script
└── README.md               # This file
```

## Configuration Files

### dns_profiles.json

Contains all DNS profiles organized by type:
- `ipv4_profiles`: List of IPv4 DNS configurations
- `ipv6_profiles`: List of IPv6 DNS configurations
- `dns64_profiles`: List of DNS64 configurations

Each profile includes:
```json
{
  "profile_number": 1,
  "profile_name": "Google",
  "primary": "8.8.8.8",
  "secondary": "8.8.4.4"
}
```

## Updating DNS Profiles

To fetch the latest DNS profiles from the online source:

1. Click the **"🔄 Reload Profiles"** button in the GUI, or
2. Run the extraction script manually:

```bash
python extract_dns.py
```

This will download the latest data from the GitHub Gist and update `dns_profiles.json`.

## Technical Details

### How It Works

1. **DNS Detection**: Uses Windows `netsh` commands to read current DNS settings
2. **Profile Application**: Applies DNS settings via `netsh interface ipv4/ipv6 set dnsservers`
3. **Ping Testing**: Uses ICMP ping in worker threads to test DNS server responsiveness
4. **Thread Safety**: All network operations run in background threads to keep UI responsive

### Administrator Privileges

This application requires administrator privileges to modify network settings. The batch file automatically requests elevation. If running manually, ensure you launch with "Run as Administrator".

## Troubleshooting

### Application Won't Start
- Ensure you're running as Administrator
- Verify Python 3.8+ is installed
- Check that dependencies are installed: `pip install PyQt6 qt-material`

### DNS Changes Don't Apply
- Make sure you're running as Administrator
- Some corporate networks may restrict DNS changes
- Try resetting to DHCP first, then apply new settings

### Ping Tests Show Failed
- Firewall may be blocking ICMP requests
- Some DNS servers don't respond to ping but still work
- Network connectivity issues

### Profiles Not Loading
- Ensure `dns_profiles.json` exists in the same directory
- Check internet connection for reload feature
- Verify JSON file is valid format

## Security Notes

- ⚠️ **Always verify DNS providers** before applying their settings
- ⚠️ **Some providers** may log your DNS queries
- ⚠️ **Corporate networks** may have policies against custom DNS
- ✅ **Open source** - All code is visible and auditable

## Contributing

Contributions are welcome! Feel free to:
- Add new DNS providers
- Improve the UI/UX
- Fix bugs
- Add new features

## License

This project is provided as-is for educational and personal use.

## Acknowledgments

- DNS profile data sourced from [public-dns.info](https://public-dns.info/) and community-maintained lists
- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- Theme support by [qt-material](https://github.com/UN-GCPDS/qt-material)

## Support

For issues, questions, or suggestions, please open an issue in the repository.

---

**Made with ❤️ for easier DNS management**
