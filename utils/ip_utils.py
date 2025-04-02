import socket
import os
import json
import ipaddress
from pathlib import Path
import streamlit as st
import requests

def is_valid_ip(ip_str):
    """Check if the given string is a valid IP address"""
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

def get_private_ip():
    """Get the private IP address of the machine running the application"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Use an external IP to determine the outbound interface
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception as e:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# For backward compatibility
def get_machine_ip():
    """Get the IP address of the machine running the application (alias for get_private_ip)"""
    return get_private_ip()

def get_client_ip():
    """Get the client's IP address"""
    try:
        # Get headers using the newer st.context.headers instead of _get_websocket_headers
        if hasattr(st, 'context') and hasattr(st.context, 'headers'):
            headers = st.context.headers
            if headers and "X-Forwarded-For" in headers:
                return headers["X-Forwarded-For"].split(",")[0].strip()
            if headers and "X-Real-IP" in headers:
                return headers["X-Real-IP"]
        
        # Fallback to socket
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except:
        return "127.0.0.1"  # Default to localhost if error

def is_app_running_locally():
    """Determine if the app is running locally or in production"""
    try:
        # Check if running in Streamlit Cloud
        if os.environ.get("IS_STREAMLIT_CLOUD") == "true":
            return False
        
        # Check local environment indicators
        local_hosts = ["localhost", "127.0.0.1", "::1"]
        machine_ip = get_private_ip()
        
        # If machine IP is in local_hosts, it's likely running locally
        if machine_ip in local_hosts:
            return True
            
        # Check if running in development mode
        if os.environ.get("STREAMLIT_ENV", "").lower() == "development":
            return True
            
        return False
    except:
        # Default to assuming production for safety
        return False

def get_allowed_ips():
    """Get the list of allowed IP addresses from config file"""
    config_path = Path(__file__).parent.parent / "config" / "ip_config.json"
    
    if not config_path.exists():
        # Default to localhost if config doesn't exist
        return ["127.0.0.1"]
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            return config.get("allowed_ips", ["127.0.0.1"])
    except Exception as e:
        print(f"Error loading IP configuration: {e}")
        return ["127.0.0.1"]  # Default to localhost if error

def ip_in_allowed_list(ip, allowed_ips=None):
    """Check if the given IP is in the list of allowed IPs"""
    if allowed_ips is None:
        allowed_ips = get_allowed_ips()
    
    # Always allow localhost
    if ip in ["127.0.0.1", "::1", "localhost"]:
        return True
    
    return ip in allowed_ips 