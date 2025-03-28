import json
import os
import argparse

CONFIG_PATH = "ip_config.json"

def load_config():
    """Load the IP configuration from file"""
    if not os.path.exists(CONFIG_PATH):
        return {"allowed_ips": ["127.0.0.1"], "description": "List of IP addresses allowed to access the application"}
    
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return {"allowed_ips": ["127.0.0.1"], "description": "List of IP addresses allowed to access the application"}

def save_config(config):
    """Save the configuration to file"""
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
        print("Configuration saved successfully.")
    except Exception as e:
        print(f"Error saving configuration: {e}")

def list_ips():
    """List all allowed IP addresses"""
    config = load_config()
    allowed_ips = config.get("allowed_ips", [])
    
    print("\nAllowed IP Addresses:")
    print("---------------------")
    for i, ip in enumerate(allowed_ips, 1):
        print(f"{i}. {ip}")
    print(f"\nTotal: {len(allowed_ips)} IP address(es)")

def add_ip(ip):
    """Add an IP address to the allowed list"""
    config = load_config()
    allowed_ips = config.get("allowed_ips", [])
    
    if ip in allowed_ips:
        print(f"IP address {ip} is already in the allowed list.")
        return
    
    allowed_ips.append(ip)
    config["allowed_ips"] = allowed_ips
    save_config(config)
    print(f"Added IP address: {ip}")

def remove_ip(ip):
    """Remove an IP address from the allowed list"""
    config = load_config()
    allowed_ips = config.get("allowed_ips", [])
    
    if ip not in allowed_ips:
        print(f"IP address {ip} is not in the allowed list.")
        return
    
    allowed_ips.remove(ip)
    config["allowed_ips"] = allowed_ips
    save_config(config)
    print(f"Removed IP address: {ip}")

def main():
    parser = argparse.ArgumentParser(description="Manage IP addresses for application access control")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all allowed IP addresses")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add an IP address to the allowed list")
    add_parser.add_argument("ip", help="IP address to add")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove an IP address from the allowed list")
    remove_parser.add_argument("ip", help="IP address to remove")
    
    args = parser.parse_args()
    
    if args.command == "list":
        list_ips()
    elif args.command == "add":
        add_ip(args.ip)
    elif args.command == "remove":
        remove_ip(args.ip)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 