import streamlit.web.cli as stcli
import os
import sys
import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Run the Employee Attendance System")
    parser.add_argument(
        "--enable-ip-restriction", 
        action="store_true",
        help="Enable IP address restriction"
    )
    parser.add_argument(
        "--disable-ip-restriction", 
        action="store_true",
        help="Disable IP address restriction"
    )
    parser.add_argument(
        "--show-ip-config", 
        action="store_true",
        help="Show the current IP configuration"
    )
    parser.add_argument(
        "--add-ip", 
        type=str,
        help="Add an IP address to the allowed list"
    )
    parser.add_argument(
        "--remove-ip", 
        type=str,
        help="Remove an IP address from the allowed list"
    )
    parser.add_argument(
        "--force-override", 
        action="store_true",
        help="Launch the app with admin override active"
    )
    parser.add_argument(
        "--override-code", 
        type=str,
        help="Set a custom admin override code (default: admin123)"
    )
    
    args = parser.parse_args()
    
    ip_config_path = Path("config/ip_config.json")
    
    # Create config directory if it doesn't exist
    if not ip_config_path.parent.exists():
        ip_config_path.parent.mkdir(parents=True)
    
    # Create default config if it doesn't exist
    if not ip_config_path.exists():
        default_config = {
            "allowed_ips": ["127.0.0.1"],
            "enabled": True,
            "description": "List of IP addresses allowed to access the application"
        }
        with open(ip_config_path, "w") as f:
            json.dump(default_config, f, indent=4)
    
    # Load current config
    try:
        with open(ip_config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error loading IP configuration: {e}")
        config = {
            "allowed_ips": ["127.0.0.1"],
            "enabled": True,
            "description": "List of IP addresses allowed to access the application"
        }
    
    # Process arguments
    if args.enable_ip_restriction:
        config["enabled"] = True
        print("IP restriction ENABLED")
    
    if args.disable_ip_restriction:
        config["enabled"] = False
        print("IP restriction DISABLED")
    
    if args.add_ip:
        ip = args.add_ip
        if ip not in config["allowed_ips"]:
            config["allowed_ips"].append(ip)
            print(f"Added IP address: {ip}")
        else:
            print(f"IP address {ip} already in allowed list")
    
    if args.remove_ip:
        ip = args.remove_ip
        if ip in config["allowed_ips"]:
            config["allowed_ips"].remove(ip)
            print(f"Removed IP address: {ip}")
        else:
            print(f"IP address {ip} not in allowed list")
    
    if args.show_ip_config:
        print("\nCurrent IP Configuration:")
        print(f"IP Restriction: {'ENABLED' if config.get('enabled', True) else 'DISABLED'}")
        print("\nAllowed IP Addresses:")
        for ip in config["allowed_ips"]:
            print(f"  - {ip}")
        print()
    
    # Save the updated config 
    with open(ip_config_path, "w") as f:
        json.dump(config, f, indent=4)
    
    # Set environment variables
    os.environ["IP_RESTRICTION_ENABLED"] = str(config.get("enabled", True)).lower()
    
    # Handle override settings
    if args.override_code:
        os.environ["ADMIN_OVERRIDE_CODE"] = args.override_code
        print(f"Custom admin override code set")
    
    if args.force_override:
        # Create a temporary file to signal force override to the app
        Path(".force_override").touch()
        print("Force override mode enabled - IP restrictions will be bypassed")
    
    # Run the Streamlit application
    sys.argv = ["streamlit", "run", "app.py"]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main() 