HRMS/
├── app.py                 # Main entry point
├── pages/
│   ├── __init__.py       # For importing modules
│   ├── login_page.py     # Login page and authentication logic
│   ├── user_profile.py   # User profile page
│   ├── attendance.py     # Attendance management page
│   ├── admin_panel.py    # Admin panel and related functions
│   ├── user_settings.py  # Miscellaneous settings (password, regularization, etc.)
│   ├── blog_notice.py    # Blogs and notice page
├── utils/
│   ├──__init__.py       # For importing modules
│   ├── database.py       # Database connection and utility functions
│   ├── helpers.py        # Helper functions (e.g., hash_password, footer)
│   └── styles.py         # Styling functions (e.g., calendar styling)
├──__init__.py       # For importing modules
├──.gitignore
├──tasks.txt
└── requirements.txt      # List of dependencies (optional)# Employee_portal

# Employee Attendance System

A Streamlit-based employee attendance management system with IP address restriction.

## IP Address Restriction Feature

This system includes a feature to restrict access based on IP addresses. This ensures that only authorized devices can access the application.

### Running the Application

You can run the application using the `run.py` script:

```bash
# Run with IP restriction enabled (default)
python run.py

# Run with IP restriction disabled
python run.py --disable-ip-restriction

# Run with IP restriction enabled
python run.py --enable-ip-restriction

# Show current IP configuration
python run.py --show-ip-config
```

### Managing Allowed IP Addresses

You can add or remove IP addresses using the command-line arguments:

```bash
# Add an IP address
python run.py --add-ip 192.168.1.100

# Remove an IP address
python run.py --remove-ip 192.168.1.100
```

Alternatively, you can manage IP addresses through the Admin Panel interface if you have HR permissions.

### Finding Your IP Address

To find your computer's IP address:

#### On Windows
1. Open Command Prompt
2. Type `ipconfig` and press Enter
3. Look for "IPv4 Address" under your network adapter

#### On macOS/Linux
1. Open Terminal
2. Type `ifconfig` or `ip addr` and press Enter
3. Look for "inet" under your network adapter

### Configuration File

The IP configuration is stored in `config/ip_config.json`. The file has the following structure:

```json
{
    "allowed_ips": [
        "127.0.0.1",
        "192.168.1.100"
    ],
    "enabled": true,
    "description": "List of IP addresses allowed to access the application"
}
```

- `allowed_ips`: Array of IP addresses that are allowed to access the application
- `enabled`: Boolean indicating whether IP restriction is enabled
- `description`: Description of the configuration

## Admin Override

If you need emergency access from an unauthorized IP, there is an admin override option on the access denied page. The default admin code is "admin123" but should be changed in production by setting the `ADMIN_OVERRIDE_CODE` environment variable.

## Deployment Considerations

When deploying to Streamlit Cloud or other hosting services, please note:

1. The IP detection method may need adjustment as client IPs might be masked by proxies
2. You can disable IP restriction if your hosting service already provides IP filtering
3. Consider setting the `ADMIN_OVERRIDE_CODE` environment variable to a secure value
