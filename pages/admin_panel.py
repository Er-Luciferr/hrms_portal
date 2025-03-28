import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar, time
import os
from utils.styles import style_calendar
from utils.helpers import add_footer
from functools import lru_cache
import numpy as np
import json
from utils.ip_utils import get_allowed_ips, is_valid_ip
import ipaddress

@lru_cache(maxsize=128)
def format_time_12h(time_obj):
    """Format time object to 12-hour format string with caching."""
    if pd.isna(time_obj):
        return ''
    return time_obj.strftime('%I:%M %p')

def load_table(table_name):
    """Load a table from a CSV file in the 'Database' folder."""
    try:
        df = pd.read_csv(f"Database/{table_name}.csv")
        
        # Process date and time columns in batches
        date_columns = ['date', 'date_of_birth', 'date_of_joining']
        time_columns = ['in_time', 'out_time', 'requested_in_time', 'requested_out_time']
        
        # Process date columns efficiently
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        
        # Process time columns efficiently
        for col in time_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%H:%M:%S', errors='coerce').dt.time
        
        return df
    except Exception as e:
        st.error(f"Error loading table {table_name}: {e}")
        return pd.DataFrame()

def save_table(table_name, df):
    """Save a DataFrame to a CSV file in the 'Database' folder."""
    try:
        # Save to CSV file
        df.to_csv(f"Database/{table_name}.csv", index=False)
    except Exception as e:
        st.error(f"Error saving table {table_name}: {e}")

def clear_cache(table_name=None):
    """Clear Streamlit cache."""
    # Clear Streamlit's cache_data
    st.cache_data.clear()

# Constants for reusable styles
CALENDAR_STYLE = {
    'white-space': 'pre-wrap', 
    'text-align': 'left', 
    'vertical-align': 'top',
    'border': '1px solid #e0e0e0',
    'padding': '5px'
}

CALENDAR_TABLE_STYLES = [
    {'selector': 'th', 'props': [('text-align', 'center'), ('font-weight', 'bold')]},
    {'selector': 'td', 'props': [('padding', '5px')]}
]

class AdminPanelPage:
    def __init__(self):
        # Initialize cache for expensive computations
        self.employee_options_cache = {}
        
    @st.cache_data
    def get_employee_options(_self, users_df):
        """Cache employee options for dropdown menus."""
        employees = users_df[['employee_code', 'name']].drop_duplicates().sort_values('name')
        return {row['name']: row['employee_code'] for index, row in employees.iterrows()}
    
    def check_all_attendance(self):
        """Check attendance of all employees with improved efficiency."""
        st.subheader("Attendance of All Employees")
        
        # Load data once
        users_df = load_table('users')
        attendance_logs_df = load_table('attendance_logs')
        
        # Get employee options efficiently with caching
        employee_options = self.get_employee_options(users_df)
        
        # Create filter controls with more efficient layout
        col1, col2 = st.columns(2)
        with col1:
            selected_employee = st.selectbox(
                "Select Employee:",
                options=["All Employees"] + list(employee_options.keys()),
                index=0,
                key="admin_employee_select"
            )
        with col2:
            # Get the current date components once
            current_date = datetime.now()
            current_month = current_date.month
            current_year = current_date.year
            
            month = st.selectbox(
                "Select Month:",
                list(calendar.month_name)[1:],
                index=current_month - 1,
                key="admin_month_select"
            )
            year = st.selectbox(
                "Select Year:",
                [current_year - 1, current_year, current_year + 1],
                index=1,
                key="admin_year_select"
            )
            
        # Calculate date ranges once
        month_num = list(calendar.month_name).index(month)
        first_day = datetime(year, month_num, 1).date()
        last_day = datetime(year, month_num, calendar.monthrange(year, month_num)[1]).date()
        
        # Filter attendance logs more efficiently
        date_mask = (attendance_logs_df['date'] >= first_day) & (attendance_logs_df['date'] <= last_day)
        filtered_df = attendance_logs_df[date_mask]
        
        # Filter for specific employee if selected
        if selected_employee != "All Employees":
            employee_code = employee_options[selected_employee]
            emp_mask = filtered_df['employee_code'].eq(employee_code)
            filtered_df = filtered_df[emp_mask]
            
        # Build calendar data more efficiently
        calendar_data = self.build_calendar_data(filtered_df, month_num, year)
        
        # Display the calendar
        st.subheader(f"Calendar for {month} {year}")
        st.write(calendar_data.to_html(escape=False), unsafe_allow_html=True)
    
    def build_calendar_data(self, filtered_df, month_num, year):
        """Build calendar display data without caching to avoid pickling issues."""
        month_calendar = calendar.monthcalendar(year, month_num)
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        # Pre-generate templates for efficiency
        DATE_DISPLAY_TEMPLATE = '<div style="font-size:1.2em; font-weight:bold; background-color:#f0f0f0; border-radius:50%; width:25px; height:25px; display:inline-block; text-align:center; line-height:25px; margin-bottom:5px;">{}</div>'
        
        # Convert filtered_df to a nested dictionary for faster lookup
        attendance_data = {}
        for _, record in filtered_df.iterrows():
            date_day = record['date'].day
            emp_code = record['employee_code']
            
            if emp_code not in attendance_data:
                attendance_data[emp_code] = {}
            
            attendance_data[emp_code][date_day] = record
        
        # Build display and status data
        display_data, status_data = [], []
        for week in month_calendar:
            week_display, week_status = [], []
            for day in week:
                if day == 0:
                    week_display.append("")
                    week_status.append("")
                else:
                    # Aggregate attendance for all users on this day
                    day_records = []
                    for emp in attendance_data:
                        if day in attendance_data[emp]:
                            day_records.append(attendance_data[emp][day])
                    
                    if day_records:
                        # Create a consolidated view if there are multiple employees
                        date_display = DATE_DISPLAY_TEMPLATE.format(day)
                        
                        if len(day_records) == 1:
                            # Single employee case
                            rec = day_records[0]
                            in_time = format_time_12h(rec['in_time']) if pd.notna(rec['in_time']) else ''
                            out_time = format_time_12h(rec['out_time']) if pd.notna(rec['out_time']) else ''
                            status = rec.get('status', 'A')  # Get status from record, default to A if not present
                            
                            cell_text = f"{date_display}<br>In: {in_time}<br>Out: {out_time}<br>Status: {status}"
                            cell_status = status
                        else:
                            # Multiple employees case
                            cell_text = f"{date_display}<br>{len(day_records)} employees checked in"
                            # Use aggregated status - present if any employee is present
                            statuses = [rec.get('status', 'A') for rec in day_records]
                            cell_status = 'P' if 'P' in statuses else 'MIS' if 'MIS' in statuses else 'A'
                    else:
                        date_display = DATE_DISPLAY_TEMPLATE.format(day)
                        cell_text = f"{date_display}<br>No Record"
                        cell_status = "A"
                    
                    week_display.append(cell_text)
                    week_status.append(cell_status)
            
            display_data.append(week_display)
            status_data.append(week_status)
        
        # Create and style DataFrames
        df_display = pd.DataFrame(display_data, columns=weekday_names)
        df_status = pd.DataFrame(status_data, columns=weekday_names)
        
        # Apply styles more efficiently
        styled_df = df_display.style.apply(
            lambda row: [style_calendar(val) for val in df_status.loc[row.name]], 
            axis=1
        ).set_properties(**CALENDAR_STYLE).set_table_styles(CALENDAR_TABLE_STYLES)
        
        return styled_df

    def approve_regularization_requests(self):
        """Approve regularization requests with improved efficiency."""
        st.subheader("Approve Regularization Requests")
        
        # Load data once
        requests_df = load_table('regularization_requests')
        
        # Convert all employee codes to lowercase for consistency
        requests_df['employee_code'] = requests_df['employee_code'].str.lower()
        
        # Filter for pending requests more efficiently
        pending_mask = requests_df['status'].eq('Pending')
        pending_requests = requests_df[pending_mask]
        
        if pending_requests.empty:
            st.info("No pending regularization requests.")
            return
            
        # Group requests by employee for better organization
        employees_with_requests = pending_requests['employee_code'].unique()
        
        for employee_code in employees_with_requests:
            # Get employee name for better display
            users_df = load_table('users')
            users_df['employee_code'] = users_df['employee_code'].str.lower()  # Convert to lowercase for comparison
            emp_mask = users_df['employee_code'].eq(employee_code)
            employee_name = users_df.loc[emp_mask, 'name'].iloc[0] if emp_mask.any() else employee_code
            
            st.markdown(f"### Requests from {employee_name} ({employee_code})")
            
            # Filter requests for this employee
            emp_requests = pending_requests[pending_requests['employee_code'].eq(employee_code)]
            
            for _, req in emp_requests.iterrows():
                with st.container():
                    st.write(f"**Request ID:** {req['id']} | **Date:** {req['date']}")
                    st.write(f"**Request Type:** {req['request_type']} | **In-Time:** {req['requested_in_time'] or 'N/A'} | **Out-Time:** {req['requested_out_time'] or 'N/A'}")
                    st.write(f"**Reason:** {req['reason']}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Approve Request {req['id']}", key=f"approve_{req['id']}"):
                            self.process_regularization_request(req, "Approved")
                    with col2:
                        if st.button(f"Reject Request {req['id']}", key=f"reject_{req['id']}"):
                            self.process_regularization_request(req, "Rejected")
                    
                    st.markdown("---")
    
    def process_regularization_request(self, request, status):
        """Process a regularization request (approve or reject)."""
        try:
            # Load required data
            requests_df = load_table('regularization_requests')
            attendance_logs_df = load_table('attendance_logs')
            
            # Update request status
            req_mask = requests_df['id'].eq(request['id'])
            requests_df.loc[req_mask, 'status'] = status
            
            if status == "Approved":
                # Find if there's already a record for this date and employee
                employee_code = request['employee_code'].lower()  # Convert to lowercase
                request_date = request['date']
                
                # Convert existing employee codes to lowercase for comparison
                attendance_logs_df['employee_code'] = attendance_logs_df['employee_code'].str.lower()
                mask = (attendance_logs_df['employee_code'].eq(employee_code)) & (attendance_logs_df['date'].eq(request_date))
                
                if mask.any():
                    # Update existing record based on request type
                    if request['request_type'] == 'Correct In-Time' and pd.notna(request['requested_in_time']):
                        attendance_logs_df.loc[mask, 'in_time'] = request['requested_in_time']
                        
                        # Update status and working hours if out_time exists
                        if pd.notna(attendance_logs_df.loc[mask, 'out_time'].iloc[0]):
                            attendance_logs_df.loc[mask, 'status'] = 'P'
                            
                            # Recalculate working hours
                            in_time = request['requested_in_time']
                            out_time = attendance_logs_df.loc[mask, 'out_time'].iloc[0]
                            working_hours = self.calculate_working_hours(in_time, out_time)
                            attendance_logs_df.loc[mask, 'working_hours'] = working_hours
                        else:
                            attendance_logs_df.loc[mask, 'status'] = 'MIS'
                            
                    elif request['request_type'] == 'Correct Out-Time' and pd.notna(request['requested_out_time']):
                        attendance_logs_df.loc[mask, 'out_time'] = request['requested_out_time']
                        
                        # Update status and calculate working hours if in_time exists
                        if pd.notna(attendance_logs_df.loc[mask, 'in_time'].iloc[0]):
                            attendance_logs_df.loc[mask, 'status'] = 'P'
                            
                            # Calculate working hours
                            in_time = attendance_logs_df.loc[mask, 'in_time'].iloc[0]
                            out_time = request['requested_out_time']
                            working_hours = self.calculate_working_hours(in_time, out_time)
                            attendance_logs_df.loc[mask, 'working_hours'] = working_hours
                else:
                    # Create a new attendance record
                    new_record = pd.DataFrame([{
                        'employee_code': employee_code,  # Already lowercase
                        'date': request_date,
                        'in_time': request['requested_in_time'] if request['request_type'] == 'Correct In-Time' else None,
                        'out_time': request['requested_out_time'] if request['request_type'] == 'Correct Out-Time' else None,
                        'working_hours': None,
                        'status': 'MIS'  # Will be updated if both in and out times are present
                    }])
                    
                    # Append the new record
                    attendance_logs_df = pd.concat([attendance_logs_df, new_record], ignore_index=True)
            
            # Save updates
            save_table('regularization_requests', requests_df)
            save_table('attendance_logs', attendance_logs_df)
            
            # Clear all caches to ensure fresh data is loaded everywhere
            clear_cache()  # Clear all caches instead of just one
            
            # Also clear Streamlit's cache_data
            st.cache_data.clear()
            
            st.success(f"Request {status.lower()} successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error processing request: {e}")
    
    def calculate_working_hours(self, in_time, out_time):
        """Calculate working hours between in_time and out_time efficiently."""
        if pd.isna(in_time) or pd.isna(out_time):
            return 0.0
            
        # Convert to datetime objects
        in_time_dt = datetime.combine(datetime.min.date(), in_time)
        out_time_dt = datetime.combine(datetime.min.date(), out_time)
            
        # Check if out_time is before in_time (overnight shift)
        if out_time_dt < in_time_dt:
            out_time_dt = datetime.combine(datetime.min.date() + pd.Timedelta(days=1), out_time)
            
        delta = out_time_dt - in_time_dt
        return round(delta.total_seconds() / 3600, 2)

    def manage_employees(self):
        """Manage employee information with improved efficiency."""
        st.subheader("Manage Employees")
        
        # Create tabs for better organization
        list_tab, add_tab, edit_tab = st.tabs(["List Employees", "Add Employee", "Edit Employee"])
        
        with list_tab:
            self.list_employees()
            
        with add_tab:
            self.add_employee()
            
        with edit_tab:
            self.edit_employee()
    
    def list_employees(self):
        """List all employees with improved display."""
        users_df = load_table('users')
        
        if users_df.empty:
            st.info("No employees found.")
            return
            
        # Select columns to display
        display_cols = ['name', 'employee_code', 'designation', 'date_of_joining']
        
        # Format dates for display
        users_df_display = users_df[display_cols].copy()
        if 'date_of_joining' in users_df_display.columns:
            users_df_display['date_of_joining'] = users_df_display['date_of_joining'].apply(
                lambda x: x.strftime('%d-%m-%Y') if pd.notna(x) else '')
        
        # Display the data
        st.dataframe(users_df_display, use_container_width=True)
    
    def add_employee(self):
        """Add a new employee with improved form handling."""
        from utils.helpers import hash_password
        
        with st.form("add_employee_form"):
            st.subheader("Add New Employee")
            
            name = st.text_input("Name")
            employee_code = st.text_input("Employee Code")
            designation = st.selectbox("Designation", ["ADMIN", "HR", "TRAINER", "EMPLOYEE"])
            date_of_birth = st.date_input("Date of Birth")
            date_of_joining = st.date_input("Date of Joining")
            password = st.text_input("Password", type="password")
            
            submit_button = st.form_submit_button("Add Employee")
            
            if submit_button:
                if not name or not employee_code or not password:
                    st.error("Name, Employee Code, and Password are required fields.")
                    return
                
                # Check if employee code already exists
                users_df = load_table('users')
                if not users_df.empty and employee_code.lower() in users_df['employee_code'].str.lower().values:
                    st.error(f"Employee with code '{employee_code}' already exists.")
                    return
                
                # Create new employee record
                new_employee = pd.DataFrame([{
                    'name': name,
                    'employee_code': employee_code.lower(),  # Convert to lowercase
                    'designation': designation,
                    'date_of_birth': date_of_birth,
                    'date_of_joining': date_of_joining,
                    'password': hash_password(password)
                }])
                
                # Add to users table
                users_df = pd.concat([users_df, new_employee], ignore_index=True)
                save_table('users', users_df)
                
                st.success(f"Employee '{name}' added successfully!")
    
    def edit_employee(self):
        """Edit an existing employee with improved error handling."""
        users_df = load_table('users')
        
        if users_df.empty:
            st.info("No employees found to edit.")
            return
            
        # Get employee options efficiently with caching
        employee_options = self.get_employee_options(users_df)
        
        selected_employee = st.selectbox(
            "Select Employee to Edit:",
            options=list(employee_options.keys()),
            key="edit_employee_select"
        )
        
        if not selected_employee:
            return
            
        employee_code = employee_options[selected_employee]
        employee_mask = users_df['employee_code'].eq(employee_code)
        
        if not employee_mask.any():
            st.error("Employee not found.")
            return
            
        employee_data = users_df[employee_mask].iloc[0]
        
        with st.form("edit_employee_form"):
            st.subheader(f"Edit Employee: {selected_employee}")
            
            name = st.text_input("Name", value=employee_data['name'])
            designation = st.selectbox("Designation", 
                                     ["ADMIN", "HR", "TRAINER", "EMPLOYEE"],
                                     index=["ADMIN", "HR", "TRAINER", "EMPLOYEE"].index(employee_data['designation']) 
                                            if employee_data['designation'] in ["ADMIN", "HR", "TRAINER", "EMPLOYEE"] else 0)
            
            # Format dates for the date picker
            if pd.notna(employee_data['date_of_birth']):
                date_of_birth = st.date_input("Date of Birth", value=employee_data['date_of_birth'])
            else:
                date_of_birth = st.date_input("Date of Birth")
                
            if pd.notna(employee_data['date_of_joining']):
                date_of_joining = st.date_input("Date of Joining", value=employee_data['date_of_joining'])
            else:
                date_of_joining = st.date_input("Date of Joining")
            
            # Option to reset password
            reset_password = st.checkbox("Reset Password")
            new_password = st.text_input("New Password", type="password", disabled=not reset_password)
            
            submit_button = st.form_submit_button("Update Employee")
            
            if submit_button:
                from utils.helpers import hash_password
                
                # Update employee record
                users_df.loc[employee_mask, 'name'] = name
                users_df.loc[employee_mask, 'designation'] = designation
                users_df.loc[employee_mask, 'date_of_birth'] = date_of_birth
                users_df.loc[employee_mask, 'date_of_joining'] = date_of_joining
                users_df.loc[employee_mask, 'employee_code'] = employee_code.lower()  # Ensure lowercase
                
                if reset_password and new_password:
                    users_df.loc[employee_mask, 'password'] = hash_password(new_password)
                
                save_table('users', users_df)
                st.success(f"Employee '{name}' updated successfully!")

    def display(self):
        """Display the admin panel with improved UI organization."""
        st.title("Admin Panel")
        
        tabs = st.tabs(["Attendance Overview", "Regularization Requests", "Manage Employees", "IP Management"])
        
        with tabs[0]:
            self.check_all_attendance()
            
        with tabs[1]:
            self.approve_regularization_requests()
            
        with tabs[2]:
            self.manage_employees()
            
        with tabs[3]:
            self.ip_management()
    
    def ip_management(self):
        st.header("IP Access Management")
        st.info("This section allows you to manage which IP addresses can access the application.")
        
        # Load current IP addresses
        config_path = "config/ip_config.json"
        
        # Create default config if it doesn't exist
        if not os.path.exists("config"):
            os.makedirs("config")
            
        if not os.path.exists(config_path):
            default_config = {
                "allowed_ips": ["127.0.0.1"],
                "description": "List of IP addresses allowed to access the application"
            }
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=4)
                
        # Load config
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                allowed_ips = config.get("allowed_ips", [])
        except Exception as e:
            st.error(f"Error loading IP configuration: {e}")
            allowed_ips = ["127.0.0.1"]
            
        # Display current IPs
        st.subheader("Currently Allowed IP Addresses")
        
        ip_df = pd.DataFrame({"IP Address": allowed_ips})
        edited_df = st.data_editor(
            ip_df,
            hide_index=True,
            num_rows="dynamic",
            key="ip_editor",
            column_config={
                "IP Address": st.column_config.TextColumn(
                    "IP Address",
                    help="Enter a valid IPv4 address",
                ),
            }
        )
        
        # Save changes button
        if st.button("Save IP Changes"):
            new_ips = edited_df["IP Address"].tolist()
            
            # Manual validation of all IPs
            invalid_ips = []
            for ip in new_ips:
                try:
                    ipaddress.ip_address(ip)
                except ValueError:
                    invalid_ips.append(ip)
                    
            if invalid_ips:
                st.error(f"Invalid IP addresses: {', '.join(invalid_ips)}")
                return
                
            # Save to config
            config["allowed_ips"] = new_ips
            try:
                with open(config_path, "w") as f:
                    json.dump(config, f, indent=4)
                st.success("IP configuration saved successfully!")
            except Exception as e:
                st.error(f"Error saving configuration: {e}")
        
        # Add explanation
        with st.expander("How to Find IP Addresses"):
            st.markdown("""
            ### Finding IP Addresses
            
            #### For Local Network:
            1. **Windows**: Open Command Prompt and type `ipconfig`
            2. **macOS/Linux**: Open Terminal and type `ifconfig` or `ip addr`
            
            #### For Remote Access:
            If you want to allow access from outside your local network, you'll need to use the public IP address.
            Visit [whatismyip.com](https://www.whatismyip.com/) from the device you want to allow.
            
            #### Important Notes:
            - For security, only add trusted IP addresses
            - If someone's IP changes frequently, consider a VPN solution instead
            - The application must be restarted for changes to take effect
            """)

        add_footer()