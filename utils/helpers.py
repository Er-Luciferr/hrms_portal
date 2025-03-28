# utils/helpers.py
import streamlit as st
import hashlib
# import mysql.connector
import base64
# from utils.database import get_db_connection
import pandas as pd

def hash_password(password):
    return password #hashlib.sha256(password.encode()).hexdigest()

def add_footer():
    st.markdown(
        """
        <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f1f1f1;
            text-align: center;
            padding: 10px;
            color: black;
        }
        </style>
        <div class="footer">
            © 2025 YuHasPro IT. All rights reserved.
        </div>
        """,
        unsafe_allow_html=True
    )

def standardize_date_time(df):
    """Standardize date and time formats in a DataFrame."""
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date']).dt.strftime('%d-%m-%Y')
    if 'in_time' in df.columns:
        df['in_time'] = pd.to_datetime(df['in_time'], format='%H:%M:%S', errors='coerce').dt.strftime('%I:%M:%S %p')
    if 'out_time' in df.columns:
        df['out_time'] = pd.to_datetime(df['out_time'], format='%H:%M:%S', errors='coerce').dt.strftime('%I:%M:%S %p')
    if 'date_of_birth' in df.columns:
        df['date_of_birth'] = pd.to_datetime(df['date_of_birth']).dt.strftime('%d-%m-%Y')
    if 'date_of_joining' in df.columns:
        df['date_of_joining'] = pd.to_datetime(df['date_of_joining']).dt.strftime('%d-%m-%Y')
    return df

def save_table(table_name, df):
    """Save a DataFrame to a CSV file in the 'Database' folder."""
    # Standardize date and time formats before saving
    df = standardize_date_time(df)
    df.to_csv(f"Database/{table_name}.csv", index=False)

def load_table(table_name):
    """Load a table from a CSV file in the 'Database' folder."""
    try:
        df = pd.read_csv(f"Database/{table_name}.csv")
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y').dt.date
        if 'in_time' in df.columns:
            df['in_time'] = pd.to_datetime(df['in_time'], format='%I:%M:%S %p', errors='coerce').dt.time
        if 'out_time' in df.columns:
            df['out_time'] = pd.to_datetime(df['out_time'], format='%I:%M:%S %p', errors='coerce').dt.time
        if 'date_of_birth' in df.columns:
            df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], format='%d-%m-%Y').dt.date
        if 'date_of_joining' in df.columns:
            df['date_of_joining'] = pd.to_datetime(df['date_of_joining'], format='%d-%m-%Y').dt.date
        return df
    except FileNotFoundError:
        return pd.DataFrame()
