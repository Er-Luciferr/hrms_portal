# IP Access Restriction Configuration

This feature restricts access to the application based on the client's IP address. Only users connecting from the allowed IP addresses can access the application.

## Configuration

The allowed IP addresses are stored in the `ip_config.json` file. By default, only localhost (`127.0.0.1`) is allowed.

### IP Configuration File Structure

```json
{
    "allowed_ips": [
        "127.0.0.1",
        "192.168.1.100"
    ],
    "description": "List of IP addresses allowed to access the application"
}
```

## Managing IP Addresses

You can use the `manage_ips.py` script to add, remove, or list allowed IP addresses.

### Listing Allowed IP Addresses

```
python manage_ips.py list
```

### Adding an IP Address

```
python manage_ips.py add 192.168.1.123
```

### Removing an IP Address

```
python manage_ips.py remove 192.168.1.123
```

## Finding Your IP Address

### On Windows
1. Open Command Prompt
2. Type `ipconfig` and press Enter
3. Look for "IPv4 Address" under your network adapter

### On macOS/Linux
1. Open Terminal
2. Type `ifconfig` or `ip addr` and press Enter
3. Look for "inet" under your network adapter

## Important Notes

1. For security, keep this configuration private and only add trusted IP addresses.
2. If you're deploying to Streamlit Cloud, you'll need to adjust the IP detection method as the client's IP might be masked by the proxy.
3. If you're behind a NAT router, devices on your local network will share the same public IP address.
4. For office/company networks, you might need to add a range of IP addresses. 