#!/usr/bin/env python3
"""
DNS Manager GUI - A modern PyQt6 application for managing DNS profiles on Windows 11.
Features:
- Display current DNS status
- Load DNS profiles from JSON file
- Test ping for each profile in separate threads
- Apply selected DNS profile to OS network adapter
- Reload profiles using extract_dns.py
- Reset to Automatic (DHCP)
- Administrator privilege check
"""

import sys
import json
import subprocess
import socket
import ctypes
import re
from pathlib import Path
from typing import Optional, Dict, List, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QFrame, QGridLayout,
    QMessageBox, QProgressBar, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

# Try to import qt-material, fallback gracefully if not available
try:
    import qt_material
    QT_MATERIAL_AVAILABLE = True
except ImportError:
    QT_MATERIAL_AVAILABLE = False


# Color themes for different DNS types
THEMES = {
    'ipv4': {
        'primary': '#7b1fa2',  # Deep purple
        'secondary': '#9c27b0',  # Purple
        'accent': '#e1bee7',  # Light purple
        'text': '#ffffff'
    },
    'ipv6': {
        'primary': '#1976d2',  # Blue
        'secondary': '#2196f3',  # Light blue
        'accent': '#bbdefb',  # Light blue accent
        'text': '#ffffff'
    },
    'dns64': {
        'primary': '#388e3c',  # Green
        'secondary': '#4caf50',  # Light green
        'accent': '#c8e6c9',  # Light green accent
        'text': '#ffffff'
    }
}


class PingWorker(QThread):
    """Worker thread for testing DNS server ping."""
    ping_result = pyqtSignal(str, str, int)  # profile_name, ip, ping_ms (-1 if failed)
    
    def __init__(self, profile_name: str, ip_address: str, timeout: int = 2):
        super().__init__()
        self.profile_name = profile_name
        self.ip_address = ip_address
        self.timeout = timeout
    
    def run(self):
        """Test ping to the DNS server using ICMP ping."""
        try:
            # Use Windows ping command for accurate ICMP ping
            if ':' in self.ip_address:
                # IPv6 address - use ping -6 explicitly
                result = subprocess.run(
                    ['ping', '-6', '-n', '1', '-w', str(self.timeout * 1000), self.ip_address],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout + 2,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            else:
                # IPv4 address
                result = subprocess.run(
                    ['ping', '-n', '1', '-w', str(self.timeout * 1000), self.ip_address],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout + 2,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
            
            if result.returncode == 0:
                # Parse ping time from output
                output = result.stdout
                import re
                # Match both "time=Xms" and "time<Xms" formats
                match = re.search(r'time[=<](\d+)ms', output, re.IGNORECASE)
                if match:
                    ping_ms = int(match.group(1))
                    self.ping_result.emit(self.profile_name, self.ip_address, ping_ms)
                else:
                    # Fallback: check if ping succeeded but couldn't parse time
                    if 'Reply from' in output or 'von' in output.lower():
                        self.ping_result.emit(self.profile_name, self.ip_address, 50)
                    else:
                        self.ping_result.emit(self.profile_name, self.ip_address, -1)
            else:
                self.ping_result.emit(self.profile_name, self.ip_address, -1)
        except Exception as e:
            self.ping_result.emit(self.profile_name, self.ip_address, -1)


class DNSTile(QFrame):
    """A tile widget representing a DNS profile."""
    
    def __init__(self, profile: Dict[str, Any], dns_type: str, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.dns_type = dns_type
        self.ping_values = {}
        
        self.setup_ui()
        self.apply_theme()
    
    def setup_ui(self):
        """Setup the tile UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.name_label = QLabel(self.profile['profile_name'])
        self.name_label.setFont(QFont('Segoe UI', 11, QFont.Weight.Bold))
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)
        
        self.primary_label = QLabel(f"Primary: {self.profile.get('primary', 'N/A')}")
        self.primary_label.setFont(QFont('Segoe UI', 9))
        self.primary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.primary_label.setWordWrap(True)
        layout.addWidget(self.primary_label)
        
        self.secondary_label = QLabel(f"Secondary: {self.profile.get('secondary', 'N/A')}")
        self.secondary_label.setFont(QFont('Segoe UI', 9))
        self.secondary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.secondary_label.setWordWrap(True)
        layout.addWidget(self.secondary_label)
        
        self.ping_label = QLabel("Ping: -- ms")
        self.ping_label.setFont(QFont('Segoe UI', 9))
        self.ping_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.ping_label)
        
        self.apply_button = QPushButton("Apply")
        self.apply_button.setFont(QFont('Segoe UI', 9, QFont.Weight.Bold))
        self.apply_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.apply_button.clicked.connect(self.on_apply_clicked)
        layout.addWidget(self.apply_button)
        
        self.setMinimumWidth(200)
        self.setMaximumWidth(300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    def apply_theme(self):
        """Apply color theme based on DNS type."""
        theme = THEMES.get(self.dns_type, THEMES['ipv4'])
        
        self.setStyleSheet(f"""
            DNSTile {{
                background-color: {theme['secondary']};
                border-radius: 10px;
                border: 2px solid {theme['primary']};
            }}
            DNSTile:hover {{
                background-color: {theme['primary']};
            }}
            QLabel {{
                color: {theme['text']};
            }}
            QPushButton {{
                background-color: {theme['accent']};
                color: {theme['primary']};
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
            }}
            QPushButton:hover {{
                background-color: #ffffff;
            }}
            QPushButton:pressed {{
                background-color: {theme['primary']};
                color: #ffffff;
            }}
        """)
    
    def update_ping(self, ip: str, ping_ms: int):
        """Update ping value for an IP address."""
        self.ping_values[ip] = ping_ms
        
        valid_pings = [p for p in self.ping_values.values() if p >= 0]
        if valid_pings:
            avg_ping = sum(valid_pings) // len(valid_pings)
            self.ping_label.setText(f"Ping: {avg_ping} ms")
            
            if avg_ping < 50:
                color = "#00e676"
            elif avg_ping < 100:
                color = "#ffeb3b"
            else:
                color = "#ff5252"
            
            self.ping_label.setStyleSheet(f"color: {color}; font-weight: bold;")
        else:
            self.ping_label.setText("Ping: Failed")
            self.ping_label.setStyleSheet("color: #ff5252; font-weight: bold;")
    
    def on_apply_clicked(self):
        """Handle apply button click."""
        # Navigate up the parent chain to find the main window
        parent = self.parent()
        while parent:
            if isinstance(parent, DNSManagerGUI):
                parent.apply_dns_profile(self.profile, self.dns_type)
                return
            parent = parent.parent()


class DNSManagerGUI(QMainWindow):
    """Main window for DNS Manager GUI."""
    
    def __init__(self):
        super().__init__()
        
        self.profiles_data = {}
        self.current_dns = {"ipv4": "Unknown", "ipv6": "Unknown"}
        self.is_admin = self.check_admin_privileges()
        self.active_workers = []
        
        self.setup_ui()
        self.load_profiles()
        self.refresh_current_dns()
        self.test_all_pings()
    
    def check_admin_privileges(self) -> bool:
        """Check if running with administrator privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return True
    
    def setup_ui(self):
        """Setup the main UI."""
        self.setWindowTitle("DNS Manager - Windows 11")
        self.setMinimumSize(800, 600)
        
        if QT_MATERIAL_AVAILABLE:
            try:
                qt_material.apply_stylesheet(self, 'dark_purple.xml')
            except Exception:
                pass
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        title_label = QLabel("🌐 DNS Manager")
        title_label.setFont(QFont('Segoe UI', 20, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #ce93d8; padding: 10px;")
        main_layout.addWidget(title_label)
        
        if not self.is_admin:
            warning_label = QLabel("⚠️ Warning: Not running as Administrator. Some features may not work.")
            warning_label.setFont(QFont('Segoe UI', 10))
            warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            warning_label.setStyleSheet("color: #ffc107; background-color: #333; padding: 8px; border-radius: 5px;")
            main_layout.addWidget(warning_label)
        
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-radius: 10px;
                border: 2px solid #7b1fa2;
            }
        """)
        status_layout = QVBoxLayout(status_frame)
        status_layout.setContentsMargins(15, 15, 15, 15)
        
        status_title = QLabel("📊 Current DNS Status")
        status_title.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        status_title.setStyleSheet("color: #e1bee7;")
        status_layout.addWidget(status_title)
        
        self.ipv4_status_label = QLabel("IPv4 DNS: Loading...")
        self.ipv4_status_label.setFont(QFont('Segoe UI', 10))
        self.ipv4_status_label.setStyleSheet("color: #ffffff;")
        status_layout.addWidget(self.ipv4_status_label)
        
        self.ipv6_status_label = QLabel("IPv6 DNS: Loading...")
        self.ipv6_status_label.setFont(QFont('Segoe UI', 10))
        self.ipv6_status_label.setStyleSheet("color: #ffffff;")
        status_layout.addWidget(self.ipv6_status_label)
        
        main_layout.addWidget(status_frame)
        
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)
        
        self.reload_button = QPushButton("🔄 Reload Profiles (extract_dns.py)")
        self.reload_button.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        self.reload_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reload_button.clicked.connect(self.reload_profiles_from_script)
        self.reload_button.setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #9c27b0;
            }
            QPushButton:pressed {
                background-color: #4a148c;
            }
        """)
        controls_layout.addWidget(self.reload_button)
        
        self.reset_button = QPushButton("🔧 Reset to Automatic (DHCP)")
        self.reset_button.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        self.reset_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_button.clicked.connect(self.reset_to_dhcp)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #f44336;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        controls_layout.addWidget(self.reset_button)
        
        self.refresh_dns_button = QPushButton("🔄 Refresh DNS Status")
        self.refresh_dns_button.setFont(QFont('Segoe UI', 10, QFont.Weight.Bold))
        self.refresh_dns_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_dns_button.clicked.connect(self.refresh_current_dns)
        self.refresh_dns_button.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #2196f3;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        controls_layout.addWidget(self.refresh_dns_button)
        
        controls_layout.addStretch()
        main_layout.addLayout(controls_layout)
        
        profiles_title = QLabel("📋 DNS Profiles")
        profiles_title.setFont(QFont('Segoe UI', 14, QFont.Weight.Bold))
        profiles_title.setStyleSheet("color: #e1bee7; padding: 10px 0;")
        main_layout.addWidget(profiles_title)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)
        
        self.tiles_container = QWidget()
        self.tiles_layout = QGridLayout(self.tiles_container)
        self.tiles_layout.setSpacing(10)
        self.tiles_layout.setContentsMargins(0, 0, 0, 0)
        self.tiles_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.scroll_area.setWidget(self.tiles_container)
        main_layout.addWidget(self.scroll_area)
        
        self.resizeEvent = self.on_resize
    
    def load_profiles(self):
        """Load DNS profiles from JSON file."""
        json_path = Path(__file__).parent / "dns_profiles.json"
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                self.profiles_data = json.load(f)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "dns_profiles.json not found!")
            self.profiles_data = {'ipv4_profiles': [], 'ipv6_profiles': [], 'dns64_profiles': []}
        except json.JSONDecodeError:
            QMessageBox.critical(self, "Error", "Invalid JSON in dns_profiles.json!")
            self.profiles_data = {'ipv4_profiles': [], 'ipv6_profiles': [], 'dns64_profiles': []}
        
        self.display_profiles()
    
    def display_profiles(self):
        """Display all DNS profiles as tiles."""
        while self.tiles_layout.count():
            item = self.tiles_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        row = 0
        col = 0
        max_cols = 4
        
        for profile in self.profiles_data.get('ipv4_profiles', []):
            tile = DNSTile(profile, 'ipv4', self)
            self.tiles_layout.addWidget(tile, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        for profile in self.profiles_data.get('ipv6_profiles', []):
            tile = DNSTile(profile, 'ipv6', self)
            self.tiles_layout.addWidget(tile, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        for profile in self.profiles_data.get('dns64_profiles', []):
            tile = DNSTile(profile, 'dns64', self)
            self.tiles_layout.addWidget(tile, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        self.tiles_layout.setRowStretch(row + 1, 1)
    
    def test_all_pings(self):
        """Test ping for all DNS profiles in separate threads."""
        for worker in self.active_workers:
            worker.terminate()
        self.active_workers.clear()
        
        for profile in self.profiles_data.get('ipv4_profiles', []):
            primary = profile.get('primary')
            secondary = profile.get('secondary')
            
            if primary:
                worker = PingWorker(profile['profile_name'], primary)
                worker.ping_result.connect(self.on_ping_result)
                self.active_workers.append(worker)
                worker.start()
            
            if secondary and secondary != primary:
                worker = PingWorker(profile['profile_name'], secondary)
                worker.ping_result.connect(self.on_ping_result)
                self.active_workers.append(worker)
                worker.start()
        
        for profile in self.profiles_data.get('ipv6_profiles', []):
            primary = profile.get('primary')
            secondary = profile.get('secondary')
            
            if primary:
                worker = PingWorker(profile['profile_name'], primary)
                worker.ping_result.connect(self.on_ping_result)
                self.active_workers.append(worker)
                worker.start()
            
            if secondary and secondary != primary:
                worker = PingWorker(profile['profile_name'], secondary)
                worker.ping_result.connect(self.on_ping_result)
                self.active_workers.append(worker)
                worker.start()
        
        for profile in self.profiles_data.get('dns64_profiles', []):
            primary = profile.get('primary')
            secondary = profile.get('secondary')
            
            if primary:
                worker = PingWorker(profile['profile_name'], primary)
                worker.ping_result.connect(self.on_ping_result)
                self.active_workers.append(worker)
                worker.start()
            
            if secondary and secondary != primary:
                worker = PingWorker(profile['profile_name'], secondary)
                worker.ping_result.connect(self.on_ping_result)
                self.active_workers.append(worker)
                worker.start()
    
    def on_ping_result(self, profile_name: str, ip: str, ping_ms: int):
        """Handle ping result from worker thread."""
        for i in range(self.tiles_layout.count()):
            item = self.tiles_layout.itemAt(i)
            if item and item.widget():
                tile = item.widget()
                if isinstance(tile, DNSTile):
                    # Match by profile name to ensure we update the correct tile
                    if tile.profile.get('profile_name') == profile_name:
                        tile.update_ping(ip, ping_ms)
                        return
    
    def refresh_current_dns(self):
        """Refresh the current DNS status from the system."""
        try:
            # Use PowerShell to get DNS servers for active interfaces (Ethernet and Wi-Fi)
            # Priority: Check which interface is actually UP/CONNECTED first
            ps_command = r'''
$ErrorActionPreference = "SilentlyContinue"

# Get all network adapters with their operational status
$netAdapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" }

# Define priority order for interface aliases (case-insensitive matching)
$priorityInterfaces = @("Wi-Fi", "Ethernet")

$selectedInterface = $null
$ipv4Servers = @()
$ipv6Servers = @()

foreach ($interfaceName in $priorityInterfaces) {
    # Find matching active interface (case-insensitive)
    $matchingAdapter = $netAdapters | Where-Object { 
        $_.Name -like "*$interfaceName*" -or $_.InterfaceDescription -like "*$interfaceName*"
    } | Select-Object -First 1
    
    if ($matchingAdapter) {
        $adapterName = $matchingAdapter.Name
        
        # Get DNS servers for this specific adapter
        $dnsServers = Get-DnsClientServerAddress -InterfaceAlias $adapterName -ErrorAction SilentlyContinue
        
        if ($dnsServers) {
            foreach ($dns in $dnsServers) {
                if ($dns.AddressFamily -eq 2 -and $dns.ServerAddresses.Count -gt 0) {
                    # IPv4 (AddressFamily 2)
                    $ipv4Servers = $dns.ServerAddresses
                } elseif ($dns.AddressFamily -eq 23 -and $dns.ServerAddresses.Count -gt 0) {
                    # IPv6 (AddressFamily 23)
                    $ipv6Servers = $dns.ServerAddresses
                }
            }
            
            # If we found at least one address family for this interface, use it
            if ($ipv4Servers.Count -gt 0 -or $ipv6Servers.Count -gt 0) {
                $selectedInterface = $adapterName
                break
            }
            
            # Reset for next interface check
            $ipv4Servers = @()
            $ipv6Servers = @()
        }
    }
}

# Return result as JSON
$result = @{
    Interface = $selectedInterface
    IPv4 = $ipv4Servers
    IPv6 = $ipv6Servers
}

$result | ConvertTo-Json -Depth 3
'''
            
            result = subprocess.run(
                ['powershell', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                shell=False
            )
            
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                
                ipv4_servers = data.get('IPv4', [])
                ipv6_servers = data.get('IPv6', [])
                interface_name = data.get('Interface', None)
                
                # Ensure they are lists
                if not isinstance(ipv4_servers, list):
                    ipv4_servers = [ipv4_servers] if ipv4_servers else []
                if not isinstance(ipv6_servers, list):
                    ipv6_servers = [ipv6_servers] if ipv6_servers else []
                
                if interface_name:
                    if ipv4_servers:
                        self.current_dns['ipv4'] = ', '.join(ipv4_servers[:2])
                    else:
                        self.current_dns['ipv4'] = 'Not configured'
                    
                    if ipv6_servers:
                        self.current_dns['ipv6'] = ', '.join(ipv6_servers[:2])
                    else:
                        self.current_dns['ipv6'] = 'Not configured'
                    
                    self.current_dns['interface'] = interface_name
                else:
                    self.current_dns['ipv4'] = 'Automatic (DHCP)'
                    self.current_dns['ipv6'] = 'Automatic (DHCP)'
                    self.current_dns['interface'] = 'None'
            else:
                stderr_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self.current_dns['ipv4'] = f'Error retrieving DNS: {stderr_msg}'
                self.current_dns['ipv6'] = f'Error retrieving DNS: {stderr_msg}'
                self.current_dns['interface'] = 'Error'
        
        except FileNotFoundError:
            self.current_dns['ipv4'] = 'Error: PowerShell not found (Windows only)'
            self.current_dns['ipv6'] = 'Error: PowerShell not found (Windows only)'
            self.current_dns['interface'] = 'Error'
        except Exception as e:
            self.current_dns['ipv4'] = f'Error: {str(e)}'
            self.current_dns['ipv6'] = f'Error: {str(e)}'
            self.current_dns['interface'] = 'Error'
        
        interface_info = f" ({self.current_dns.get('interface', 'Unknown')})" if self.current_dns.get('interface') else ""
        self.ipv4_status_label.setText(f"IPv4 DNS{interface_info}: {self.current_dns['ipv4']}")
        self.ipv6_status_label.setText(f"IPv6 DNS{interface_info}: {self.current_dns['ipv6']}")
    
    def apply_dns_profile(self, profile: Dict[str, Any], dns_type: str):
        """Apply the selected DNS profile to the system."""
        if not self.is_admin:
            reply = QMessageBox.question(
                self,
                "Administrator Privileges Required",
                "This operation requires administrator privileges. "
                "Please restart this application as Administrator to apply DNS settings.\n\n"
                "Do you want to continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        primary = profile.get('primary', '')
        secondary = profile.get('secondary', '')
        
        if not primary:
            QMessageBox.warning(self, "Error", "No primary DNS server specified in profile!")
            return
        
        try:
            if dns_type == 'ipv4':
                addresses = [primary]
                if secondary:
                    addresses.append(secondary)
                addr_string = ', '.join([f'"{a}"' for a in addresses])
                
                cmd = f'''
                $adapter = Get-NetAdapter | Where-Object {{ $_.Status -eq 'Up' }} | Select-Object -First 1
                if ($adapter) {{
                    Set-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex -ResetServerAddresses
                    Set-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex -ServerAddresses {addr_string}
                    Write-Output "DNS applied successfully"
                }} else {{
                    Write-Error "No active network adapter found"
                }}
                '''
            else:
                addresses = [primary]
                if secondary:
                    addresses.append(secondary)
                addr_string = ', '.join([f'"{a}"' for a in addresses])
                
                cmd = f'''
                $adapter = Get-NetAdapter | Where-Object {{ $_.Status -eq 'Up' }} | Select-Object -First 1
                if ($adapter) {{
                    Set-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex -ResetServerAddresses
                    Set-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex -ServerAddresses {addr_string} -AddressFamily IPv6
                    Write-Output "DNS applied successfully"
                }} else {{
                    Write-Error "No active network adapter found"
                }}
                '''
            
            result = subprocess.run(
                ['powershell', '-Command', cmd],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            
            # Check for errors in stderr or error output
            if result.returncode != 0 or 'error' in result.stderr.lower() or 'error' in result.stdout.lower():
                error_msg = result.stderr if result.stderr else result.stdout
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"Failed to apply DNS profile. Error:\n{error_msg}\n\n"
                    "Make sure you're running as Administrator."
                )
            else:
                QMessageBox.information(
                    self,
                    "Success",
                    f"DNS profile '{profile['profile_name']}' applied successfully!"
                )
                self.refresh_current_dns()
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to apply DNS profile:\n{str(e)}\n\n"
                "Make sure you're running as Administrator."
            )
    
    def reload_profiles_from_script(self):
        """Run extract_dns.py to reload profiles."""
        script_path = Path(__file__).parent / "extract_dns.py"
        
        if not script_path.exists():
            QMessageBox.critical(self, "Error", "extract_dns.py not found!")
            return
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                QMessageBox.information(
                    self,
                    "Success",
                    "Profiles reloaded successfully!\n\n" + result.stdout
                )
                self.load_profiles()
                self.test_all_pings()
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"Failed to reload profiles:\n{error_msg}"
                )
        
        except subprocess.TimeoutExpired:
            QMessageBox.warning(
                self,
                "Timeout",
                "The script took too long to execute."
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to run extract_dns.py:\n{str(e)}"
            )
    
    def reset_to_dhcp(self):
        """Reset DNS settings to Automatic (DHCP)."""
        if not self.is_admin:
            reply = QMessageBox.question(
                self,
                "Administrator Privileges Required",
                "This operation requires administrator privileges. "
                "Please restart this application as Administrator to reset DNS settings.\n\n"
                "Do you want to continue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        try:
            cmd = '''
            $adapters = Get-NetAdapter | Where-Object { $_.Status -eq 'Up' }
            foreach ($adapter in $adapters) {
                Set-DnsClientServerAddress -InterfaceIndex $adapter.InterfaceIndex -ResetServerAddresses
            }
            '''
            
            result = subprocess.run(
                ['powershell', '-Command', cmd],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                QMessageBox.information(
                    self,
                    "Success",
                    "DNS settings reset to Automatic (DHCP) successfully!"
                )
                self.refresh_current_dns()
            else:
                error_msg = result.stderr if result.stderr else result.stdout
                QMessageBox.warning(
                    self,
                    "Warning",
                    f"Failed to reset DNS settings. Error:\n{error_msg}\n\n"
                    "Make sure you're running as Administrator."
                )
        
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to reset DNS settings:\n{str(e)}\n\n"
                "Make sure you're running as Administrator."
            )
    
    def on_resize(self, event):
        """Handle window resize to rearrange tiles."""
        super().resizeEvent(event)
        
        tile_width = 220
        margin = 50
        available_width = self.width() - margin
        
        max_cols = max(1, available_width // tile_width)
        max_cols = min(max_cols, 4)
        
        tiles = []
        for i in range(self.tiles_layout.count()):
            item = self.tiles_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), DNSTile):
                tiles.append(item.widget())
        
        while self.tiles_layout.count():
            item = self.tiles_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
        
        row = 0
        col = 0
        for tile in tiles:
            self.tiles_layout.addWidget(tile, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Only set Fusion style if qt-material is not available
    if not QT_MATERIAL_AVAILABLE:
        app.setStyle('Fusion')
    
    app.setApplicationName("DNS Manager")
    app.setOrganizationName("DNS Manager")
    
    window = DNSManagerGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
