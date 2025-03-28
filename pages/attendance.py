import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import calendar
from utils.styles import style_calendar
from utils.helpers import add_footer
from functools import lru_cache
import numpy as np

# Global variables for performance
_MIN_DATETIME = datetime.min

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
        
        # Convert working_hours to float if present
        if 'working_hours' in df.columns:
            df['working_hours'] = pd.to_numeric(df['working_hours'], errors='coerce')
            
        # Add status column if needed for attendance_logs
        if 'status' not in df.columns and table_name == 'attendance_logs' and 'in_time' in df.columns and 'out_time' in df.columns:
            # Create status column with vectorized operations
            conditions = [
                (pd.notna(df['in_time']) & pd.notna(df['out_time'])),
                (pd.notna(df['in_time']) & pd.isna(df['out_time'])),
            ]
            choices = ['P', 'MIS']
            df['status'] = pd.Series('A', index=df.index)  # Default value
            df['status'] = np.select(conditions, choices, default='A')
        
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

class AttendancePage:
    def __init__(self):
        # Precompute time objects for efficiency
        self._min_datetime = _MIN_DATETIME

    def calculate_working_hours(self, in_time, out_time):
        """Calculate working hours between in_time and out_time more efficiently."""
        # Early return if any time is missing
        if pd.isna(in_time) or pd.isna(out_time):
            return 0.0
            
        # Process string inputs efficiently
        if isinstance(in_time, str):
            try:
                in_time_dt = datetime.strptime(in_time, '%H:%M:%S')
            except ValueError:
                return 0.0
        else:
            in_time_dt = datetime.combine(self._min_datetime.date(), in_time)
            
        if isinstance(out_time, str):
            try:
                out_time_dt = datetime.strptime(out_time, '%H:%M:%S')
            except ValueError:
                return 0.0
        else:
            out_time_dt = datetime.combine(self._min_datetime.date(), out_time)
        
        # Calculate total seconds and convert to hours
        delta = out_time_dt - in_time_dt
        
        # Handle case where out_time is on next day
        if delta.total_seconds() < 0:
            # Assume the person worked past midnight - add one day
            out_time_dt += timedelta(days=1)
            delta = out_time_dt - in_time_dt
            
        return round(delta.total_seconds() / 3600, 2)

    def is_late(self, in_time, designation):
        """Determine if an employee is late based on their designation."""
        if pd.isna(in_time):
            return False
            
        # Get the threshold in minutes based on designation - use uppercase for more efficient comparison
        threshold_mins = 20 if designation in ['TRAINER', 'HR'] else 15
        
        # Check if in_time is past any hour plus threshold
        return in_time.minute > threshold_mins

    def record_attendance(self, action):
        """Record IN or OUT time in the attendance_logs CSV more efficiently."""
        # Load attendance logs and users in a single block
        attendance_logs_df = load_table('attendance_logs')
        users_df = load_table('users')
        
        # Get today's date and current time
        today = datetime.now().date()
        current_time = datetime.now().time().replace(microsecond=0)
        
        # Standardize employee code
        employee_code = st.session_state['employee_code'].lower()
        
        # Get employee's designation using vectorized operations
        user_mask = users_df['employee_code'].str.lower().eq(employee_code)
        designation = users_df.loc[user_mask, 'designation'].iloc[0].upper() if user_mask.any() else ""
        
        # Filter for today's record for the current employee more efficiently
        mask = (attendance_logs_df['employee_code'].eq(employee_code)) & (attendance_logs_df['date'].eq(today))
        result = attendance_logs_df[mask]
        
        if action == "IN":
            if result.empty:
                # Check if late based on designation
                is_late = self.is_late(current_time, designation)
                
                # No record exists, create a new one with in_time
                new_row = pd.DataFrame([{
                    'employee_code': employee_code.lower(),  # Convert to lowercase
                    'date': today,
                    'in_time': current_time,
                    'out_time': None,
                    'working_hours': None,
                    'status': 'LA' if is_late else 'MIS'  # Set status to LA if late, otherwise MIS
                }])
                
                # Use concatenate with DataFrame instead of Series for better performance
                attendance_logs_df = pd.concat([attendance_logs_df, new_row], ignore_index=True)
                save_table('attendance_logs', attendance_logs_df)
                st.success("IN time Recorded Successfully!")
            else:
                st.warning("IN time already recorded for today.")
        elif action == "OUT":
            # Check if we have an in_time but no out_time - more efficient condition
            if not result.empty and pd.notna(result.iloc[0]['in_time']) and pd.isna(result.iloc[0]['out_time']):
                # Record exists with in_time but no out_time
                in_time = result.iloc[0]['in_time']
                working_hours = self.calculate_working_hours(in_time, current_time)
                
                # Update more efficiently with loc
                attendance_logs_df.loc[mask, ['out_time', 'working_hours']] = [current_time, working_hours]
                
                # Update status efficiently
                current_status = attendance_logs_df.loc[mask, 'status'].iloc[0]
                if current_status != 'LA':
                    attendance_logs_df.loc[mask, 'status'] = 'P'
                    
                save_table('attendance_logs', attendance_logs_df)
                st.success("OUT time recorded and working hours calculated!")
            else:
                st.warning("Cannot record OUT time without an IN time or OUT time already recorded.")

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

    def display(self):
        """Display the attendance management page with calendar more efficiently."""
        st.title("Attendance Management")
        
        # Check for regularization updates
        self.check_regularization_updates()
        
        st.header("Mark Attendance")
        
        # Move CSS to a separate constant to avoid regenerating in each render
        ATTENDANCE_CSS = """
            <style>
            div.stButton > button[key="in_button"] {
                background-color: #11a62d;
                color: green;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                width: 170px;
                height: 60px;
                cursor: pointer;
            }
            div.stButton > button[key="out_button"] {
                background-color: #9c0d0d;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                width: 170px;
                height: 60px;
                cursor: pointer;
            }
            </style>
            """
        st.markdown(ATTENDANCE_CSS, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("IN", key="in_button", help="Record your IN time"):
                self.record_attendance("IN")
        with col2:
            if st.button("OUT", key="out_button", help="Record your OUT time"):
                self.record_attendance("OUT")

        # Link to regularization request page
        st.header(" ")
        
        # Get the current date components once
        current_date = datetime.now()
        current_month = current_date.month
        current_year = current_date.year
        
        col1, col2 = st.columns(2)
        with col1:
            month = st.selectbox("Select Month:", list(calendar.month_name)[1:], 
                               index=current_month - 1, key="month_select")
        with col2:
            year = st.selectbox("Select Year:", 
                              [current_year - 1, current_year, current_year + 1], 
                              index=1, key="year_select")

        month_num = list(calendar.month_name).index(month)
        
        # Calculate date ranges once
        first_day = datetime(year, month_num, 1).date()
        last_day = datetime(year, month_num, calendar.monthrange(year, month_num)[1]).date()

        # Load and filter attendance logs
        attendance_logs_df = load_table('attendance_logs')
        
        # Convert all employee codes to lowercase for consistency
        attendance_logs_df['employee_code'] = attendance_logs_df['employee_code'].str.lower()
        
        # Use more efficient vectorized operations for filtering
        employee_code = st.session_state['employee_code'].lower()
        date_mask = (attendance_logs_df['date'] >= first_day) & (attendance_logs_df['date'] <= last_day)
        emp_mask = attendance_logs_df['employee_code'].eq(employee_code)
        filtered_df = attendance_logs_df[date_mask & emp_mask]
        
        # Convert to dictionary for easier lookup by day - more efficient with dict comprehension
        attendance_data = {record['date'].day: record for _, record in filtered_df.iterrows()}

        # Build calendar more efficiently
        month_calendar = calendar.monthcalendar(year, month_num)
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        # Pre-generate HTML elements for efficiency
        DATE_DISPLAY_TEMPLATE = '<div style="font-size:1.2em; font-weight:bold; background-color:#f0f0f0; border-radius:50%; width:25px; height:25px; display:inline-block; text-align:center; line-height:25px; margin-bottom:5px;">{}</div>'
        
        display_data, status_data = [], []
        for week in month_calendar:
            week_display, week_status = [], []
            for day in week:
                if day == 0:
                    week_display.append("")
                    week_status.append("")
                else:
                    rec = attendance_data.get(day)
                    date_display = DATE_DISPLAY_TEMPLATE.format(day)
                    
                    if rec is not None:
                        # Cache formatted times to avoid duplicate formatting
                        in_time = format_time_12h(rec['in_time']) if pd.notna(rec['in_time']) else ''
                        out_time = format_time_12h(rec['out_time']) if pd.notna(rec['out_time']) else ''
                        status = rec.get('status', 'A')  # Get status from record, default to A if not present
                        
                        cell_text = f"{date_display}<br>In: {in_time}<br>Out: {out_time}<br>Status: {status}"
                    else:
                        cell_text = f"{date_display}<br>No Record"
                        status = "A"
                        
                    week_display.append(cell_text)
                    week_status.append(status)
            display_data.append(week_display)
            status_data.append(week_status)
            
        # Rest of your calendar display code remains the same
        df_display = pd.DataFrame(display_data, columns=weekday_names)
        df_status = pd.DataFrame(status_data, columns=weekday_names)
        
        # Define the style function separately so it can be pickled
        def style_row(row):
            return [style_calendar(val) for val in df_status.loc[row.name]]
        
        # Remove caching to avoid pickling error
        def get_styled_calendar(_df_display):
            """Style the calendar without caching to avoid pickling issues."""
            return _df_display.style.apply(
                style_row, 
                axis=1
            ).set_properties(**{
                'white-space': 'pre-wrap', 
                'text-align': 'left', 
                'vertical-align': 'top',
                'border': '1px solid #e0e0e0',
                'padding': '5px'
            }).set_table_styles([
                {'selector': 'th', 'props': [('text-align', 'center'), ('font-weight', 'bold')]},
                {'selector': 'td', 'props': [('padding', '5px')]}
            ])
        
        styled_df = get_styled_calendar(df_display)
        
        # Display the calendar
        st.header(f"Attendance Calendar for {month} {year}")
        st.write(styled_df.to_html(escape=False), unsafe_allow_html=True)
        
        # Add footer
        add_footer()