import streamlit as st
import pandas as pd
from datetime import date, datetime, time
import os
from utils.helpers import hash_password, add_footer
from functools import lru_cache
from pathlib import Path
import time as time_module
import numpy as np

# Import login page logic at module level to avoid circular imports
import importlib

# Helper functions for file operations without caching
def load_table(table_name):
    """Load a table from a CSV file in the 'Database' folder."""
    try:
        df = pd.read_csv(f"Database/{table_name}.csv")
        
        # Process date and time columns in batches
        date_columns = ['date', 'date_of_birth', 'date_of_joining']
        time_columns = ['in_time', 'out_time', 'requested_in_time', 'requested_out_time']
        
        # Process all date columns in one batch
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        
        # Process all time columns in one batch
        for col in time_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%H:%M:%S', errors='coerce').dt.time
        
        # Special handling for regularization_requests table
        if table_name == 'regularization_requests' and 'id' in df.columns:
            df['id'] = pd.to_numeric(df['id'], errors='coerce')
        
        return df
    except FileNotFoundError:
        return pd.DataFrame()

def save_table(table_name, df):
    """Save a DataFrame to a CSV file in the 'Database' folder."""
    df.to_csv(f"Database/{table_name}.csv", index=False)

def clear_cache(table_name=None):
    """Clear Streamlit cache."""
    # Clear Streamlit's cache_data
    st.cache_data.clear()

# Format time efficiently with caching
@lru_cache(maxsize=128)
def format_time_12h(t):
    """Format a time object to 12-hour format (AM/PM) with caching."""
    if pd.isna(t) or t is None:
        return ''
    return t.strftime('%I:%M %p')

class UserSettingsPage:
    def change_password(self):
        """Handle password change with improved efficiency."""
        st.title("Change Password")
        
        # Use a form to reduce re-renders and improve performance
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            submit_button = st.form_submit_button("Change Password")
            
            if submit_button:
                # Load LoginPage dynamically to avoid circular imports
                LoginPage = importlib.import_module('pages.login_page').LoginPage
                
                if not current_password or not new_password or not confirm_password:
                    st.error("Please fill in all password fields.")
                    return
                
                if new_password != confirm_password:
                    st.error("New passwords do not match")
                    return
                
                # Verify current password
                if LoginPage().verify_login(st.session_state['employee_code'], current_password):
                    users_df = load_table('users')
                    # More efficient filtering with Series.eq
                    mask = users_df['employee_code'].eq(st.session_state['employee_code'])
                    
                    if mask.any():
                        # Update password
                        users_df.loc[mask, 'password'] = hash_password(new_password)
                        save_table('users', users_df)
                        st.success("Password changed successfully!")
                    else:
                        st.error("User not found.")
                else:
                    st.error("Current password is incorrect")

    def check_regularization_updates(self):
        """Check if there are any approved regularization requests that need to be reflected."""
        requests_df = load_table('regularization_requests')
        
        if requests_df.empty:
            return
            
        # Convert all employee codes to lowercase for consistency
        requests_df['employee_code'] = requests_df['employee_code'].str.lower()
            
        # Filter for approved requests for the current user more efficiently
        employee_code = st.session_state['employee_code'].lower()
        mask = (requests_df['employee_code'].eq(employee_code)) & (requests_df['status'].eq('Approved'))
        approved_requests = requests_df[mask]
                                        
        if not approved_requests.empty:
            # Mark these requests as reflected in the calendar
            requests_df.loc[mask, 'status'] = 'Completed'
            save_table('regularization_requests', requests_df)
            
            # Clear all caches to ensure fresh data is loaded everywhere
            clear_cache()  # Clear Streamlit cache
            
            # Force reload attendance_logs to ensure we have the latest data
            # This is critical as admin_panel may have updated this file
            attendance_logs_df = load_table('attendance_logs')
            
            # Notify the user
            st.success("Your regularization requests have been approved and reflected in the calendar!")
            
            # Refresh the page to ensure all data is updated
            st.rerun()
            
    def display_regularization_requests(self):
        """Display all regularization requests made by the employee with their status."""
        st.header("Your Regularization Requests")
        
        # Load regularization requests
        requests_df = load_table('regularization_requests')
        
        if requests_df.empty:
            st.info("No regularization requests found.")
            return
        
        # Convert employee codes to lowercase
        requests_df['employee_code'] = requests_df['employee_code'].str.lower()
        
        # Filter for the current employee
        employee_code = st.session_state['employee_code'].lower()
        emp_mask = requests_df['employee_code'].eq(employee_code)
        user_requests = requests_df[emp_mask]
        
        if user_requests.empty:
            st.info("You haven't made any regularization requests yet.")
            return
        
        # Sort by date and status (pending first)
        user_requests = user_requests.sort_values(['date', 'status'], ascending=[False, True])
        
        # Display all requests in a table
        st.subheader("Your Request History")
        
        # Create a display dataframe with formatted columns
        display_df = user_requests.copy()
        
        # Format date
        if 'date' in display_df.columns:
            display_df['date'] = display_df['date'].apply(lambda x: x.strftime('%d-%m-%Y') if pd.notna(x) else '')
        
        # Format times
        if 'requested_in_time' in display_df.columns:
            display_df['requested_in_time'] = display_df['requested_in_time'].apply(
                lambda x: format_time_12h(x) if pd.notna(x) else 'N/A')
            
        if 'requested_out_time' in display_df.columns:
            display_df['requested_out_time'] = display_df['requested_out_time'].apply(
                lambda x: format_time_12h(x) if pd.notna(x) else 'N/A')
        
        # Create status indicators with color coding
        def color_status(val):
            color = "green" if val == "Completed" else "blue" if val == "Approved" else "orange" if val == "Pending" else "red"
            return f'<span style="color:{color};font-weight:bold">{val}</span>'
            
        display_df['status'] = display_df['status'].apply(color_status)
        
        # Select and reorder columns for display
        cols_to_display = ['date', 'request_type', 'requested_in_time', 'requested_out_time', 'reason', 'status']
        display_df = display_df[cols_to_display]
        
        # Rename columns for better display
        display_df.columns = ['Date', 'Request Type', 'Requested In-Time', 'Requested Out-Time', 'Reason', 'Status']
        
        # Display the table with HTML formatting
        st.write(display_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    
    def create_regularization_request(self):
        """Form for creating a new regularization request."""
        st.subheader("Submit New Request")
        
        with st.form("regularization_form"):
            # Date selection
            request_date = st.date_input("Date to Regularize", datetime.now().date(), max_value=date.today())
            
            # Request type
            request_type = st.selectbox(
                "Request Type", 
                ["Correct In-Time", "Correct Out-Time"],
                key="request_type"
            )
            
            # Conditional time inputs based on request type
            if request_type == "Correct In-Time":
                col1, col2 = st.columns(2)
                with col1:
                    hour = st.selectbox("Hour (In-Time)", list(range(0, 24)), 9)
                with col2:
                    minute = st.selectbox("Minute (In-Time)", [0, 15, 30, 45], 0)
                requested_in_time = time(hour=hour, minute=minute)
                requested_out_time = None
            else:  # Correct Out-Time
                col1, col2 = st.columns(2)
                with col1:
                    hour = st.selectbox("Hour (Out-Time)", list(range(0, 24)), 18)
                with col2:
                    minute = st.selectbox("Minute (Out-Time)", [0, 15, 30, 45], 0)
                requested_out_time = time(hour=hour, minute=minute)
                requested_in_time = None
            
            # Reason
            reason = st.text_area("Reason", height=100, 
                               help="Please provide a detailed reason for this regularization request")
            
            # Submit button
            submit_button = st.form_submit_button("Submit Request")
            
            if submit_button:
                if not reason:
                    st.error("Please provide a reason for your request.")
                    return
                
                # Load current requests
                requests_df = load_table('regularization_requests')
                
                # Get the next ID
                next_id = 1
                if not requests_df.empty and 'id' in requests_df.columns:
                    next_id = requests_df['id'].max() + 1 if pd.notna(requests_df['id'].max()) else 1
                
                # Create new request
                employee_code = st.session_state['employee_code'].lower()
                
                new_request = pd.DataFrame([{
                    'id': next_id,
                    'employee_code': employee_code,
                    'date': request_date,
                    'request_type': request_type,
                    'requested_in_time': requested_in_time,
                    'requested_out_time': requested_out_time,
                    'reason': reason,
                    'status': 'Pending',
                    'request_timestamp': datetime.now()
                }])
                
                # Add to requests table
                if requests_df.empty:
                    requests_df = new_request
                else:
                    requests_df = pd.concat([requests_df, new_request], ignore_index=True)
                
                # Save updated table
                save_table('regularization_requests', requests_df)
                
                # Clear cache and notify user
                clear_cache('regularization_requests')
                st.success("Your regularization request has been submitted successfully!")
                st.rerun()

    def attendance_regularization(self):
        """Handle attendance regularization with improved UI organization."""
        st.subheader("Attendance Regularization")
        
        # Check for regularization updates
        self.check_regularization_updates()
        
        # Create tabs for displaying and creating requests
        create_tab, view_tab = st.tabs(["Create Request", "View Requests"])
        
        with create_tab:
            self.create_regularization_request()
            
        with view_tab:
            self.display_regularization_requests()

    def change_photo(self):
        """Handle photo change with improved file operations."""
        st.subheader("Change Profile Photo")
        uploaded_file = st.file_uploader("Choose a new profile photo", type=["jpg", "jpeg", "png"])
        
        if uploaded_file is not None:
            # Show preview of uploaded image
            st.image(uploaded_file, caption="Preview", width=200)
            
            if st.button("Upload Photo"):
                # Validate file type more efficiently
                file_extension = Path(uploaded_file.name).suffix.lower()
                valid_extensions = {'.jpg', '.jpeg', '.png'}
                
                if file_extension not in valid_extensions:
                    st.error(f"Unsupported file type. Please use one of: {', '.join(valid_extensions)}")
                    return
                
                # Create photos directory if it doesn't exist
                photos_dir = Path("Database/photos")
                photos_dir.mkdir(parents=True, exist_ok=True)
                
                # Remove existing photos more efficiently
                employee_code = st.session_state['employee_code']
                
                # Use pathlib for better file operations
                for ext in valid_extensions:
                    existing_file = photos_dir / f"{employee_code}{ext}"
                    if existing_file.exists():
                        try:
                            existing_file.unlink()
                        except (OSError, PermissionError) as e:
                            st.error(f"Could not remove existing photo: {e}")
                            return
                
                # Save the new photo - use with block for better resource management
                file_extension = file_extension if file_extension.startswith('.') else f".{file_extension}"
                save_path = photos_dir / f"{employee_code}{file_extension}"
                
                try:
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Set flag to indicate photo was changed
                    st.session_state['photo_updated'] = True
                    
                    # Add a small delay to ensure file is written before reload
                    time_module.sleep(0.5)
                    
                    # Force a rerun to refresh the page
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving photo: {e}")

    def display(self):
        """Display user settings with improved UI organization."""
        st.title("Miscellaneous")
        
        # Use tabs for better organization
        tabs = st.tabs(['Change Password', 'Regularization Request', 'Change Photo', 'Holidays'])
        
        with tabs[0]:
            self.change_password()
        
        with tabs[1]:
            self.attendance_regularization()
        
        with tabs[2]:
            st.subheader("Change Photo")
            st.write("Keep Calm & Change your Photo")
            self.change_photo()
            
        with tabs[3]:
            st.subheader("List of Holidays")
            st.info("Holiday information will be displayed here.")
        
        add_footer()