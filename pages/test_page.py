# app.py
import streamlit as st
from functools import lru_cache
import importlib

# Define page component loader to avoid unnecessary imports until needed
class LazyPageLoader:
    def __init__(self):
        self._page_instances = {}
        self._page_classes = {
            'login': ('pages.login_page', 'LoginPage'),
            'profile': ('pages.user_profile', 'UserProfilePage'),
            'attendance': ('pages.attendance', 'AttendancePage'),
            'admin': ('pages.admin_panel', 'AdminPanelPage'),
            'settings': ('pages.user_settings', 'UserSettingsPage'),
            'blog_notice': ('pages.blog_notice', 'BlogNoticePage')
        }
    
    def get_page(self, page_key):
        """Get page instance with lazy loading."""
        if page_key not in self._page_instances:
            # Lazy import the module and instantiate the class
            module_path, class_name = self._page_classes[page_key]
            module = importlib.import_module(module_path)
            page_class = getattr(module, class_name)
            self._page_instances[page_key] = page_class()
        
        return self._page_instances[page_key]

class EmployeeAttendanceApp:
    def __init__(self):
        # Use lazy loading for pages
        self.page_loader = LazyPageLoader()
        
        # Page to component mapping
        self.page_mapping = {
            "Login": "login",
            "User Profile": "profile",
            "Employee Attendance": "attendance",
            "Admin Panel": "admin",
            "User Settings": "settings",
            "Blogs & Notice": "blog_notice"
        }
        
        # CSS for sidebar - only define once
        self.sidebar_css = """
        <style>
        [data-testid="stSidebarNav"] {
            display: none;
        }
        </style>
        """

    def main(self):
        # Apply sidebar CSS only once
        st.markdown(self.sidebar_css, unsafe_allow_html=True)
        
        # Initialize session state
        if 'logged_in' not in st.session_state:
            st.session_state['logged_in'] = False
            st.session_state['current_page'] = "Login"

        if st.session_state['logged_in']:
            self._render_sidebar()
        
        # Efficiently load and render the current page
        self._render_current_page()

    @st.cache_data
    def _get_sidebar_logo_html(self):
        """Cache sidebar logo HTML to avoid recomputing."""
        return """
            <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
            <img src="artifacts/logo.jpeg" style="width: 100px; height: auto; margin-bottom: 10px;">
            </div>
            """

    def _render_sidebar(self):
        """Render the sidebar with cached components."""
        st.sidebar.title(f"WELCOME {st.session_state['user_data']['name']}")
        st.sidebar.subheader("MENU")
        
        # Define page options based on user role
        page_options = [
            "User Profile",
            "Employee Attendance",
            "User Settings",
            "Blogs & Notice",
            "Logout"
        ]
        
        # Efficiently check designation
        if st.session_state.get('designation', '') == "HR":
            page_options.insert(2, "Admin Panel")

        # Render menu buttons
        for option in page_options:
            if st.sidebar.button(option):
                if option == "Logout":
                    st.session_state['logged_in'] = False
                    st.session_state['current_page'] = "Login"
                else:
                    st.session_state['current_page'] = option
                st.rerun()
                
        # Add logo with cached HTML
        st.sidebar.markdown(self._get_sidebar_logo_html(), unsafe_allow_html=True)

    def _render_current_page(self):
        """Render the current page using lazy loading."""
        current_page = st.session_state['current_page']
        
        if not st.session_state['logged_in']:
            # Load login page
            self.page_loader.get_page('login').display()
        else:
            # Map the current page name to the page key
            page_key = self.page_mapping.get(current_page)
            
            if page_key:
                # Special case for admin panel
                if page_key == 'admin' and st.session_state.get('designation', '') != "HR":
                    st.error("You don't have permission to access the Admin Panel.")
                    return
                    
                # Load and display the page
                self.page_loader.get_page(page_key).display()
            else:
                st.error(f"Page '{current_page}' not found.")

if __name__ == "__main__":
    app = EmployeeAttendanceApp()
    app.main()