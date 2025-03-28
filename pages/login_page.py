import streamlit as st
import pandas as pd
from utils.helpers import hash_password, add_footer
from functools import lru_cache

# Cache for loaded tables to avoid redundant file reads
_table_cache = {}

def load_table(table_name):
    """Load a table from a CSV file in the 'Database' folder with caching."""
    # Check if table is already in cache
    if table_name in _table_cache:
        return _table_cache[table_name].copy()
    
    try:
        # Read the CSV file
        df = pd.read_csv(f"Database/{table_name}.csv")
        
        # Define date columns to convert in a single pass
        date_columns = {
            'date_of_birth': '%Y-%m-%d',
            'date': '%Y-%m-%d',
            'date_of_joining': '%Y-%m-%d'
        }
        
        # Convert date columns to datetime.date with the correct format in one pass
        for col, fmt in date_columns.items():
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format=fmt, errors='coerce').dt.date
        
        # Cache the dataframe
        _table_cache[table_name] = df.copy()
        return df
    except FileNotFoundError:
        return pd.DataFrame()

class LoginPage:

    def verify_login(self, employee_code, password, name=None):
        """Verify login credentials using data from users.csv."""
        try:
            users_df = load_table('users')
            
            # Early return if dataframe is empty
            if users_df.empty:
                return False
                
            # Check for either employee code or name - more efficient with .eq()
            if employee_code:
                # Using .eq() is more efficient than == for string comparison
                user_row = users_df[users_df['employee_code'].str.lower().eq(employee_code.lower())]
            elif name:
                user_row = users_df[users_df['name'].str.lower().eq(name.lower())]
            else:
                # Early return if neither credential provided
                return False
                
            if not user_row.empty:
                # Get values directly without using iloc multiple times
                user_data = user_row.iloc[0]
                stored_password = user_data['password']
                hashed_input_password = hash_password(password)
                
                if stored_password == hashed_input_password:
                    # Store user data more efficiently with direct dictionary creation
                    st.session_state['temp_user_data'] = {
                        'name': user_data['name'],
                        'date_of_birth': user_data['date_of_birth'],
                        'date_of_joining': user_data['date_of_joining'],
                        'designation': user_data['designation'],
                        'employee_code': user_data['employee_code'],
                        'photos': user_data.get('Database/photos', '')
                    }
                    return True
            return False
        except Exception as err:
            st.error(f"Error loading user data: {err}")
            return False

    def display(self):
        """Display the login page and handle user input."""
        st.title("Employee Attendance System")
        
        # Use a form to reduce re-renders and improve performance
        with st.form(key="login_form"):
            login_method = st.radio("Login using:", ["Employee Code", "Name"])
            
            employee_code = None
            name = None
            
            if login_method == "Employee Code":
                employee_code = st.text_input("Employee Code")
            else:
                name = st.text_input("Name")
                
            password = st.text_input("Password", type="password")
            
            submitted = st.form_submit_button("Login")
            
            if submitted:
                # Use session state to track login attempts and reduce redundant processing
                if self.verify_login(employee_code, password, name):
                    st.session_state['user_data'] = st.session_state['temp_user_data']
                    st.session_state['logged_in'] = True
                    st.session_state['employee_code'] = st.session_state['user_data']['employee_code']
                    st.session_state['name'] = st.session_state['user_data']['name']
                    st.session_state['designation'] = st.session_state['user_data']['designation']
                    st.session_state['current_page'] = "Employee Attendance"
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        # Add footer outside the form to avoid re-rendering
        add_footer()