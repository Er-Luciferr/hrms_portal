import streamlit as st
import json
from pathlib import Path

class ReportedIPsPage:
    def __init__(self):
        pass
    
    def display(self):
        st.title("Reported IP Addresses")
        
        # Add refresh button
        if st.button("Refresh IP List"):
            st.rerun()
        
        # Load and display reported IPs
        ip_data_path = Path("config/reported_ips.json")
        
        if ip_data_path.exists():
            try:
                with open(ip_data_path, "r") as f:
                    ip_data = json.load(f)
                    
                if "reported_ips" in ip_data and ip_data["reported_ips"]:
                    st.write(f"Total reported IPs: {len(ip_data['reported_ips'])}")
                    
                    # Create a table to display IPs
                    st.markdown("### IP Address List")
                    for idx, ip in enumerate(ip_data["reported_ips"], 1):
                        st.write(f"{idx}. {ip}")
                        
                    # Allow clearing the IP list
                    if st.button("Clear IP List"):
                        ip_data["reported_ips"] = []
                        with open(ip_data_path, "w") as f:
                            json.dump(ip_data, f, indent=4)
                        st.success("IP list cleared successfully!")
                        st.rerun()
                else:
                    st.info("No IP addresses have been reported yet.")
            except Exception as e:
                st.error(f"Error loading reported IPs: {e}")
        else:
            st.info("No IP addresses have been reported yet.")
        
        # Show information about the IP reporting feature
        with st.expander("About IP Reporting"):
            st.markdown("""
            This page displays private IP addresses reported from user systems.
            
            To enable IP reporting:
            1. Run the application with the `--send-ip` flag
            2. Optionally set a custom endpoint with `--ip-endpoint YOUR_URL`
            
            Example: `python run.py --send-ip`
            
            By default, a built-in HTTP server listens on port 5000 to receive IP reports.
            No external dependencies are required.
            """) 