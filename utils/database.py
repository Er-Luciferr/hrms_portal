# utils/database.py
import pandas as pd

def load_table(table_name):
    """Load a table from a CSV file in the 'Database' folder."""
    try:
        df = pd.read_csv(f"Database/{table_name}.csv")
        
        # Process date and time columns
        date_columns = ['date', 'date_of_birth', 'date_of_joining']
        time_columns = ['in_time', 'out_time', 'requested_in_time', 'requested_out_time']
        
        # Process date columns
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        
        # Process time columns
        for col in time_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], format='%H:%M:%S', errors='coerce').dt.time
                
        return df
    except Exception as e:
        print(f"Error loading {table_name}: {e}")
        return pd.DataFrame()

def save_table(table_name, df):
    """Save a DataFrame to a CSV file in the 'Database' folder."""
    try:
        df.to_csv(f"Database/{table_name}.csv", index=False)
        return True
    except Exception as e:
        print(f"Error saving {table_name}: {e}")
        return False