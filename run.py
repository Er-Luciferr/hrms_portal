import streamlit.web.cli as stcli
import os
import sys
import argparse
import json
from pathlib import Path
import logging
import subprocess

# Setup logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - [%(levelname)s] - %(message)s')
logger = logging.getLogger("run")

def start_http_server():
    """Start the HTTP server for IP reporting as a separate process"""
    try:
        # Create a detached process
        if os.name == 'nt':  # Windows
            proc = subprocess.Popen([sys.executable, '-m', 'api.ip_endpoint'],
                                   creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:  # Unix/Linux
            proc = subprocess.Popen([sys.executable, '-m', 'api.ip_endpoint'],
                                   start_new_session=True)
        logger.info(f"Started HTTP server as process ID {proc.pid}")
        return True
    except Exception as e:
        logger.error(f"Failed to start HTTP server: {e}")
        return False

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
    parser.add_argument(
        "--send-ip", 
        action="store_true",
        help="Send private IP to the configured endpoint"
    )
    parser.add_argument(
        "--ip-endpoint", 
        type=str,
        help="Set the endpoint URL for sending private IP data"
    )
    parser.add_argument(
        "--start-server", 
        action="store_true",
        help="Start the HTTP server for receiving IP reports"
    )
    parser.add_argument(
        "--server-host", 
        type=str,
        help="Set the server hostname for IP reporting"
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
            "description": "List of IP addresses allowed to access the application",
            "report_ip": False,
            "ip_endpoint": "http://localhost:5000/api/ip-report"
        }
        with open(ip_config_path, "w") as f:
            json.dump(default_config, f, indent=4)
    
    # Load current config
    try:
        with open(ip_config_path, "r") as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Error loading IP configuration: {e}")
        config = {
            "allowed_ips": ["127.0.0.1"],
            "enabled": True,
            "description": "List of IP addresses allowed to access the application",
            "report_ip": False,
            "ip_endpoint": "http://localhost:5000/api/ip-report"
        }
    
    # Process arguments
    if args.enable_ip_restriction:
        config["enabled"] = True
        logger.info("IP restriction ENABLED")
    
    if args.disable_ip_restriction:
        config["enabled"] = False
        logger.info("IP restriction DISABLED")
    
    if args.add_ip:
        ip = args.add_ip
        if ip not in config["allowed_ips"]:
            config["allowed_ips"].append(ip)
            logger.info(f"Added IP address: {ip}")
        else:
            logger.info(f"IP address {ip} already in allowed list")
    
    if args.remove_ip:
        ip = args.remove_ip
        if ip in config["allowed_ips"]:
            config["allowed_ips"].remove(ip)
            logger.info(f"Removed IP address: {ip}")
        else:
            logger.info(f"IP address {ip} not in allowed list")
    
    if args.send_ip:
        config["report_ip"] = True
        logger.info("IP reporting ENABLED")
    
    if args.ip_endpoint:
        config["ip_endpoint"] = args.ip_endpoint
        logger.info(f"IP reporting endpoint set to: {args.ip_endpoint}")
    
    if args.server_host:
        os.environ["SERVER_HOST"] = args.server_host
        logger.info(f"Server hostname set to: {args.server_host}")
    
    if args.show_ip_config:
        logger.info("\nCurrent IP Configuration:")
        logger.info(f"IP Restriction: {'ENABLED' if config.get('enabled', True) else 'DISABLED'}")
        logger.info(f"IP Reporting: {'ENABLED' if config.get('report_ip', False) else 'DISABLED'}")
        if config.get('report_ip', False):
            logger.info(f"Reporting Endpoint: {config.get('ip_endpoint', 'http://localhost:5000/api/ip-report')}")
        logger.info("\nAllowed IP Addresses:")
        for ip in config["allowed_ips"]:
            logger.info(f"  - {ip}")
    
    # Save the updated config 
    with open(ip_config_path, "w") as f:
        json.dump(config, f, indent=4)
    
    # Set environment variables
    os.environ["IP_RESTRICTION_ENABLED"] = str(config.get("enabled", True)).lower()
    os.environ["IP_REPORTING_ENABLED"] = str(config.get("report_ip", False)).lower()
    os.environ["IP_REPORTING_ENDPOINT"] = config.get("ip_endpoint", "http://localhost:5000/api/ip-report")
    
    # Start the HTTP server if requested
    if args.start_server:
        success = start_http_server()
        if success:
            logger.info("HTTP server for IP reporting started successfully")
        else:
            logger.error("Failed to start HTTP server")
    
    # Send private IP to endpoint if enabled
    if config.get("report_ip", False):
        try:
            from utils.ip_sender import send_private_ip_to_endpoint
            if send_private_ip_to_endpoint():
                logger.info("Successfully sent private IP to endpoint")
            else:
                logger.error("Failed to send private IP to endpoint")
        except Exception as e:
            logger.error(f"Error sending private IP: {e}")
    
    # Handle override settings
    if args.override_code:
        os.environ["ADMIN_OVERRIDE_CODE"] = args.override_code
        logger.info(f"Custom admin override code set")
    
    if args.force_override:
        # Create a temporary file to signal force override to the app
        Path(".force_override").touch()
        logger.info("Force override mode enabled - IP restrictions will be bypassed")
    
    # Run the Streamlit application
    logger.info("Starting Streamlit application...")
    sys.argv = ["streamlit", "run", "app.py"]
    sys.exit(stcli.main())

if __name__ == "__main__":
    main() 