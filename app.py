import streamlit as st
import socket
import os
import json
from pages.login_page import LoginPage
from pages.user_profile import UserProfilePage
from pages.attendance import AttendancePage
from pages.admin_panel import AdminPanelPage
from pages.user_settings import UserSettingsPage
from pages.blog_notice import BlogNoticePage
from utils.ip_utils import get_allowed_ips, ip_in_allowed_list, is_app_running_locally

class EmployeeAttendanceApp:
    def __init__(self):  
        self.login_page = LoginPage()
        self.user_profile = UserProfilePage()
        self.attendance = AttendancePage()
        self.admin_panel = AdminPanelPage()
        self.user_settings = UserSettingsPage()
        self.blog_notice = BlogNoticePage()
        
        # Load allowed IP addresses from the utility function
        self.allowed_ips = get_allowed_ips()
        
        # Check for force override file
        if os.path.exists(".force_override"):
            # Apply force override and remove the file
            try:
                os.remove(".force_override")
                st.session_state["admin_override"] = True
            except:
                pass

    def get_client_ip(self):
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

    def main(self):
        # Initialize session state for admin override if not present
        if "admin_override" not in st.session_state:
            st.session_state["admin_override"] = False
        
        st.logo("artifacts/logo.png", size="large", link="https://www.yuhaspro.com/")
            
        # Check if IP restriction is enabled via environment variable
        ip_restriction_enabled = os.environ.get("IP_RESTRICTION_ENABLED", "true").lower() == "true"
         
        # Skip IP check if admin override is active or if restriction is disabled
        if ip_restriction_enabled and not st.session_state.get("admin_override", False):
            # Skip IP check if running locally in development mode
            running_locally = is_app_running_locally()   
            
            # Check if client's IP is allowed 
            client_ip = self.get_client_ip()
            access_allowed = running_locally or ip_in_allowed_list(client_ip, self.allowed_ips)
            
            if not access_allowed:
                st.error("⚠️ Access Denied ⚠️")
                st.write(f"Your IP address ({client_ip}) is not authorized to access this application.")
                st.write("Please contact your system administrator for assistance.")
                
                # Add a small form for admin override (optional)
                with st.expander("Admin Override"):
                    st.warning("This should only be used by system administrators.")
                    override_code = st.text_input("Admin Code", type="password", key="override_code_input")
                    override_button = st.button("Submit Override Code")
                    
                    if override_button and override_code == os.environ.get("ADMIN_OVERRIDE_CODE", "admin123"):
                        st.session_state["admin_override"] = True
                        st.success("Admin override successful. Refreshing...")
                        st.rerun()
                    elif override_button and override_code != "":
                        st.error("Invalid override code. Please try again.")
                
                # Exit early if not allowed and no admin override
                if not st.session_state.get("admin_override", False):
                    return
        
        # If IP is allowed or restriction is disabled, continue with the application
        st.markdown("""
            <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
            </style>
            """, unsafe_allow_html=True)
        
        if 'logged_in' not in st.session_state:
            st.session_state['logged_in'] = False
            st.session_state['current_page'] = "Login"

        if st.session_state['logged_in']:
            st.sidebar.title(f"WELCOME {st.session_state['user_data']['name']}")
            st.sidebar.subheader("MENU")
            page_options = [
                "User Profile",
                "Employee Attendance",
                "User Settings",
                "Blogs & Notice",
                "Logout"
            ]
            if st.session_state.get('designation', 'HR') == "HR":
                page_options.insert(2, "Admin Panel")

            for option in page_options:
                if st.sidebar.button(option):    
                    if option == "Logout":
                        st.session_state['logged_in'] = False    
                        st.session_state['current_page'] = "Login"
                    else:
                        st.session_state['current_page'] = option
                    st.rerun()
 
            # Push the logo to the bottom using an empty container
            st.sidebar.write(' ') 
            st.sidebar.image("artifacts/logo.jpg", width=180, use_container_width=False)

        if not st.session_state['logged_in']:
            self.login_page.display() 
        else:  
            if st.session_state['current_page'] == "User Profile":
                self.user_profile.display()
            elif st.session_state['current_page'] == "Employee Attendance":
                self.attendance.display()
            elif st.session_state['current_page'] == "User Settings":
                self.user_settings.display()
            elif st.session_state['current_page'] == "Blogs & Notice":
                self.blog_notice.display()
            elif st.session_state['current_page'] == "Admin Panel" and st.session_state.get('designation', 'HR') == "HR":
                self.admin_panel.display()

if __name__ == "__main__":
    app = EmployeeAttendanceApp()
    app.main()      