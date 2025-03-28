import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from utils.styles import style_calendar
from utils.helpers import add_footer

class AttendancePage:
    def calculate_working_hours(self, in_time, out_time):
        in_time_dt = datetime.strptime(in_time, '%H:%M:%S')
        out_time_dt = datetime.strptime(out_time, '%H:%M:%S')
        delta = out_time_dt - in_time_dt
        return round(delta.total_seconds() / 3600, 2)

    def record_attendance(self, action):
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            today = datetime.now().strftime("%Y-%m-%d")
            current_time = datetime.now().strftime("%H:%M:%S")
            query = "SELECT in_time, out_time FROM attendance_logs WHERE employee_code = %s AND date = %s"
            cursor.execute(query, (st.session_state['employee_code'], today))
            result = cursor.fetchone()
            entry_exists = bool(result)
            in_time = result['in_time'] if result else None
            out_time = result['out_time'] if result else None

            if action == "IN" and not entry_exists:
                cursor.execute(
                    "INSERT INTO attendance_logs (employee_code, date, in_time) VALUES (%s, %s, %s)",
                    (st.session_state['employee_code'], today, current_time)
                )
                conn.commit()
                st.success("IN time Recorded Successfully!")
            elif action == "OUT" and entry_exists and in_time and not out_time:
                working_hours = self.calculate_working_hours(in_time, current_time)
                cursor.execute(
                    "UPDATE attendance_logs SET out_time = %s, working_hours = %s WHERE employee_code = %s AND date = %s",
                    (current_time, working_hours, st.session_state['employee_code'], today)
                )
                conn.commit()
                st.success("OUT time recorded and working hours calculated!")
            elif action == "IN":
                st.warning("IN time already recorded for today.")
            elif action == "OUT":
                st.warning("Cannot record OUT time without an IN time or OUT time already recorded.")
        except Exception as err:
            st.error(f"Database error: {err}")
        finally:
            cursor.close()
            conn.close()

    def display(self):
        st.title("Attendance Management")
        st.header("Mark Attendance")
        st.markdown("""
            <style>
            div.stButton > button[key="in_button"] {
                background-color: #11a62d;
                color: green;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                width: 150px;
                height: 50px;
                cursor: pointer;
            }
            div.stButton > button[key="out_button"] {
                background-color: #9c0d0d;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                width: 150px;
                height: 50px;
                cursor: pointer;
            }
            </style>
            """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("IN", key="in_button", help="Record your IN time"):
                self.record_attendance("IN")
        with col2:
            if st.button("OUT", key="out_button", help="Record your OUT time"):
                self.record_attendance("OUT")

        st.header(" ")
        col1, col2 = st.columns(2)
        with col1:
            month = st.selectbox("Select Month:", list(calendar.month_name)[1:], index=datetime.now().month - 1, key="month_select")
        with col2:
            year = st.selectbox("Select Year:", [2024, 2025, 2026], index=1, key="year_select")

        month_num = list(calendar.month_name).index(month)
        first_day = datetime(year, month_num, 1).date()
        last_day = datetime(year, month_num, calendar.monthrange(year, month_num)[1]).date()

        attendance_data = {}
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                "SELECT date, in_time, out_time, working_hours FROM attendance_logs WHERE employee_code = %s AND date BETWEEN %s AND %s",
                (st.session_state['employee_code'], first_day, last_day)
            )
            results = cursor.fetchall()
            for record in results:
                attendance_data[record['date'].day] = record
        except Exception as err:
            st.error(f"Database error: {err}")
        finally:
            cursor.close()
            conn.close()

        month_calendar = calendar.monthcalendar(year, month_num)
        weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        display_data, status_data = [], []
        for week in month_calendar:
            week_display, week_status = [], []
            for day in week:
                if day == 0:
                    week_display.append("")
                    week_status.append("")
                else:
                    rec = attendance_data.get(day)
                    status = "P" if rec and rec['in_time'] and rec['out_time'] else "MIS" if rec and rec['in_time'] else "A"
                    cell_text = f"**{day}**\nIn: {rec['in_time'] if rec and rec['in_time'] else ''}\nOut: {rec['out_time'] if rec and rec['out_time'] else ''}\nStatus: {status}"
                    week_display.append(cell_text)
                    week_status.append(status)
            display_data.append(week_display)
            status_data.append(week_status)

        df_display = pd.DataFrame(display_data, columns=weekday_names)
        df_status = pd.DataFrame(status_data, columns=weekday_names)
        styled_df = df_display.style.apply(lambda row: [style_calendar(val) for val in df_status.loc[row.name]], axis=1).set_properties(**{
            'white-space': 'pre-wrap', 'text-align': 'left', 'vertical-align': 'top'
        }).set_table_styles([
            {'selector': 'th',
            'props': [
                ('background-color', '#000000'),
                ('color', '#ffffff'),
                ('text-align', 'center')
            ]}
        ])

        st.subheader(f"Calendar for {month} {year}")
        st.write(styled_df.to_html(index=False), unsafe_allow_html=True)
        add_footer()


# pages/admin_panel.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
import calendar, time
from utils.database import get_db_connection
from utils.styles import style_calendar
from utils.helpers import add_footer




class AdminPanelPage:

    def check_all_attendance(self):
        st.subheader("Attendance of All Employees")
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Fetch employee names and codes
            cursor.execute("SELECT DISTINCT employee_code, name FROM users ORDER BY name")
            employees = cursor.fetchall()
            employee_options = {emp['name']: emp['employee_code'] for emp in employees}
            
            # UI Components (reusing structure from AttendancePageTest)
            col1, col2 = st.columns(2)
            with col1:
                selected_employee = st.selectbox(
                    "Select Employee:",
                    options=["All Employees"] + list(employee_options.keys()),
                    index=0,
                    key="admin_employee_select"
                )
            with col2:
                month = st.selectbox(
                    "Select Month:",
                    list(calendar.month_name)[1:],
                    index=datetime.now().month - 1,
                    key="admin_month_select"
                )
            
                year = st.selectbox(
                    "Select Year:",
                    [datetime.now().year - 1, datetime.now().year, datetime.now().year + 1],
                    index=1,
                    key="admin_year_select"
                )

            # Calculate date range (reused logic)
            month_num = list(calendar.month_name).index(month)
            first_day = datetime(year, month_num, 1).date()
            last_day = datetime(year, month_num, calendar.monthrange(year, month_num)[1]).date()

            # Fetch attendance data (adapted from AttendancePageTest)
            attendance_data = {}
            if selected_employee == "All Employees":
                query = """
                    SELECT a.employee_code, e.name, a.date, a.in_time, 
                           a.out_time, a.working_hours 
                    FROM attendance_logs a
                    JOIN users e ON a.employee_code = e.employee_code
                    WHERE a.date BETWEEN %s AND %s
                    ORDER BY a.date DESC
                """
                cursor.execute(query, (first_day, last_day))
            else:
                employee_code = employee_options[selected_employee]
                query = """
                    SELECT a.employee_code, e.name, a.date, a.in_time, 
                           a.out_time, a.working_hours 
                    FROM attendance_logs a
                    JOIN users e ON a.employee_code = e.employee_code
                    WHERE a.employee_code = %s AND a.date BETWEEN %s AND %s
                    ORDER BY a.date DESC
                """
                cursor.execute(query, (employee_code, first_day, last_day))
            
            results = cursor.fetchall()
            
            if results:
                # Display DataFrame (your original approach)
                #st.dataframe(pd.DataFrame(results))
                
                # Calendar display (reused from AttendancePageTest)
                st.subheader(f"Calendar for {month} {year}")
                month_calendar = calendar.monthcalendar(year, month_num)
                weekday_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                display_data, status_data = [], []
                
                # Prepare calendar data (reused logic)
                attendance_data = {record['date'].day: record for record in results}
                for week in month_calendar:
                    week_display, week_status = [], []
                    for day in week:
                        if day == 0:
                            week_display.append("")
                            week_status.append("")
                        else:
                            rec = attendance_data.get(day)
                            status = "P" if rec and rec['in_time'] and rec['out_time'] else "MIS" if rec and rec['in_time'] else "A"
                            cell_text = f"**{day}**\nIn: {rec['in_time'] if rec and rec['in_time'] else ''}\nOut: {rec['out_time'] if rec and rec['out_time'] else ''}\nStatus: {status}"
                            week_display.append(cell_text)
                            week_status.append(status)
                    display_data.append(week_display)
                    status_data.append(week_status)
                
                # Styled calendar (reused from AttendancePageTest)
                df_display = pd.DataFrame(display_data, columns=weekday_names)
                df_status = pd.DataFrame(status_data, columns=weekday_names)
                styled_df = df_display.style.apply(
                    lambda row: [style_calendar(val) for val in df_status.loc[row.name]], 
                    axis=1
                ).set_properties(**{
                    'white-space': 'pre-wrap', 'text-align': 'left', 'vertical-align': 'top'
                }).set_table_styles([
                    {'selector': 'th',
                     'props': [
                         ('background-color', '#000000'),
                         ('color', '#ffffff'),
                         ('text-align', 'center')
                     ]}
                ])
                
                st.write(styled_df.to_html(index=False), unsafe_allow_html=True)
                add_footer()  # Reused from AttendancePageTest

                
            else:
                st.info("No attendance records found for the selected criteria.")
                
        except Exception as err:
            st.error(f"Database error: {err}")
        finally:
            cursor.close()
            conn.close()


    def approve_regularization_requests(self):
        st.subheader("Approve Regularization Requests")
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, employee_code, date, request_type, requested_in_time, requested_out_time, reason FROM regularization_requests WHERE status = 'Pending'")
            requests = cursor.fetchall()
            if requests:
                for req in requests:
                    st.write(f"**Request ID:** {req['id']} | **employee_code:** {req['employee_code']} | **Date:** {req['date']}")
                    st.write(f"**Request Type:** {req['request_type']} | **In-Time:** {req['requested_in_time'] or 'N/A'} | **Out-Time:** {req['requested_out_time'] or 'N/A'}")
                    st.write(f"**Reason:** {req['reason']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Approve Request {req['id']}", key=f"approve_{req['id']}"):
                            if req['request_type'] == 'Correct In-Time' and req['requested_in_time']:
                                cursor.execute(
                                    "INSERT INTO attendance_logs (employee_code, date, in_time) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE in_time = %s",
                                    (req['employee_code'], req['date'], req['requested_in_time'], req['requested_in_time'])
                                )
                            elif req['request_type'] == 'Correct Out-Time' and req['requested_out_time']:
                                cursor.execute(
                                    "INSERT INTO attendance_logs (employee_code, date, out_time) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE out_time = %s",
                                    (req['employee_code'], req['date'], req['requested_out_time'], req['requested_out_time'])
                                )
                            cursor.execute("UPDATE regularization_requests SET status = 'Approved' WHERE id = %s", (req['id'],))
                            conn.commit()
                            st.success(f"Request {req['id']} approved.")
                    with col2:
                        if st.button(f"Reject Request {req['id']}", key=f"reject_{req['id']}"):
                            cursor.execute("UPDATE regularization_requests SET status = 'Rejected' WHERE id = %s", (req['id'],))
                            conn.commit()
                            st.success(f"Request {req['id']} rejected.")
            else:
                st.info("No pending regularization requests.")
        except Exception as err:
            st.error(f"Database error: {err}")
        finally:
            cursor.close()
            conn.close()

    '''def submit_regularization_request(self, regularization_date, request_type, in_time_correction, out_time_correction, reason):
        """
        Submits the attendance regularization request to the database for admin approval.
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            in_time_str = in_time_correction.strftime('%H:%M:%S') if in_time_correction else None
            out_time_str = out_time_correction.strftime('%H:%M:%S') if out_time_correction else None
            insert_query = """
                INSERT INTO regularization_requests (employee_code, date, request_type, requested_in_time, requested_out_time, reason,status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                st.session_state['employee_code'],
                regularization_date,
                request_type,
                in_time_str,
                out_time_str,
                reason,
                "Pending"
            ))
            conn.commit()
            return True
        except conn.Error as err:
            st.error(f"Database error: {err}")
            return False
        finally:
            cursor.close()
            conn.close()'''

    def attendance_regularization(self):
        st.title("Attendance Regularization Request")
        st.write("Forget to LogIn/LogOut? Apply for a regularization request!")
        
        with st.form("regularization_form"):
            # Date selection with a max value of today
            regularization_date = st.date_input("Date of Attendance Issue", max_value=date.today())
            
            # Request type selection
            request_type = st.selectbox("Type of Request:", ['Correct In-Time', 'Correct Out-Time'])
            
            # Define a default time (00:00) to detect if the user hasn’t provided a time
            DEFAULT_TIME = time(0, 0)
            
            # Time input with default value
            in_time_correction = st.time_input("Enter correct time", value=DEFAULT_TIME, key="in_time_correction") if request_type == 'Correct In-Time' else None
            out_time_correction = st.time_input("Enter correct time", value=DEFAULT_TIME, key="out_time_correction") if request_type == 'Correct Out-Time' else None
            
            # Reason input
            reason = st.text_area("Reason for Regularization Request", max_chars=500)
            
            # Submit button
            submit_button = st.form_submit_button("Submit Request")
            
            # Form submission logic
            if submit_button:
                # Check if reason is provided
                if not reason.strip():
                    st.error("Reason for regularization is required.")
                # Check if corrected in-time is still the default
                elif request_type == 'Correct In-Time' and in_time_correction == DEFAULT_TIME:
                    st.error("Please provide a corrected in-time different from the default (00:00).")
                # Check if corrected out-time is still the default
                elif request_type == 'Correct Out-Time' and out_time_correction == DEFAULT_TIME:
                    st.error("Please provide a corrected out-time different from the default (00:00).")
                else:
                    # Proceed with database insertion
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        # Convert time to string for database, or None if not applicable
                        in_time_str = in_time_correction.strftime('%H:%M:%S') if request_type == 'Correct In-Time' else None
                        out_time_str = out_time_correction.strftime('%H:%M:%S') if request_type == 'Correct Out-Time' else None
                        
                        # Insert request into database
                        cursor.execute(
                            "INSERT INTO regularization_requests (employee_code, date, request_type, requested_in_time, requested_out_time, reason, status) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (st.session_state['employee_code'], regularization_date, request_type, in_time_str, out_time_str, reason, "Pending")
                        )
                        conn.commit()
                        
                        # Success message
                        st.success("Regularization request submitted successfully!")
                        st.info("Your request is pending HR approval.")
                    except Exception as err:
                        st.error(f"Database error: {err}")
                    finally:
                        cursor.close()
                        conn.close()


    def view_employee_birthdays(self):
        st.subheader("Employee Birthdays")
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT name, date_of_birth FROM users ORDER BY date_of_birth")
            results = cursor.fetchall()
            if results:
                st.dataframe(pd.DataFrame(results))
            else:
                st.info("No employee records found.")
        except Exception as err:
            st.error(f"Database error: {err}")
        finally:
            cursor.close()
            conn.close()

    def generate_employee_records(self):
        st.subheader("Generate Employee Records")
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT employee_code, name, date_of_birth, date_of_joining FROM users")
            results = cursor.fetchall()
            if results:
                st.dataframe(pd.DataFrame(results))
            else:
                st.info("No employee records found.")
        except Exception as err:
            st.error(f"Database error: {err}")
        finally:
            cursor.close()
            conn.close()

    def display(self):
        st.title("Admin Panel")
        st.subheader("Admin Functionalities")
        admin_options = [
            "Check All Employee Attendance",
            "Approve Regularization Requests",
            "View Employee Birthdays",
            "Generate Employee Records"
        ]
        selected_option = st.selectbox("Select an action:", admin_options)
        if selected_option == "Check All Employee Attendance":
            self.check_all_attendance()
        elif selected_option == "Approve Regularization Requests":
            self.approve_regularization_requests()
        elif selected_option == "View Employee Birthdays":
            self.view_employee_birthdays()
        elif selected_option == "Generate Employee Records":
            self.generate_employee_records()