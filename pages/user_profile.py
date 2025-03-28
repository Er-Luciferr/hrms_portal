# pages/user_profile.py
import streamlit as st
from utils.helpers import add_footer
import os
import pandas as pd
from datetime import datetime
from functools import lru_cache

# Cache photo lookup results to avoid redundant filesystem checks
@lru_cache(maxsize=32)
def find_user_photo(employee_code):
    """Find a user's photo file with caching to reduce filesystem operations."""
    valid_extensions = ('jpg', 'jpeg', 'png')
    
    # Use a generator expression for more efficient iteration
    for ext in valid_extensions:
        photo_path = f"Database/photos/{employee_code}.{ext}"
        if os.path.exists(photo_path):
            return photo_path
    return None

# Format date strings efficiently
def format_date(date_value, default="Not provided"):
    """Format date value to a standard display format."""
    if date_value == default:
        return default
        
    try:
        # Only convert if needed
        if not isinstance(date_value, str):
            return date_value.strftime('%d-%m-%Y')
        return pd.to_datetime(date_value).strftime('%d-%m-%Y')
    except (ValueError, AttributeError, TypeError):
        # Specific error handling
        return default

class UserProfilePage:
    def display(self):
        user_data = st.session_state['user_data']
        
        # Check if photo was just updated
        photo_updated = st.session_state.get('photo_updated', False)
        if photo_updated:
            # Clear the flag
            st.session_state['photo_updated'] = False
            st.success("Profile photo updated successfully!")
            # Clear the cache when photo is updated
            if hasattr(find_user_photo, 'cache_clear'):
                find_user_photo.cache_clear()
        
        # Look for photo in the photos directory using cached function
        employee_code = user_data['employee_code']
        photo_path = find_user_photo(employee_code)
        
        if photo_path:
            try:
                # Load the image directly using cached path
                st.image(photo_path, width=200, caption=user_data["name"], use_container_width=False)
            except Exception as e:
                st.write(f"Error displaying image: {e}")
        else:
            st.write("No photo available.")
        
        # Format dates efficiently using helper function
        dob = format_date(user_data.get("date_of_birth", "Not provided"))
        doj = format_date(user_data.get("date_of_joining", "Not provided"))
        
        # Pre-generate markdown to reduce rendering operations
        name_markdown = f'<p class="profile-info"><strong>Name:</strong> {user_data["name"]}</p>'
        doj_markdown = f'<p class="profile-info"><strong>Date of Joining:</strong> {doj}</p>'
        emp_code_markdown = f'<p class="profile-info"><strong>Employee Code:</strong> {user_data.get("employee_code", "Not provided")}</p>'
        dob_markdown = f'<p class="profile-info"><strong>Date of Birth:</strong> {dob}</p>'
        designation_markdown = f'<p class="profile-info"><strong>Designation:</strong> {user_data["designation"]}</p>'
        
        # Display the rest of the user information in two columns
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(name_markdown, unsafe_allow_html=True)
            st.markdown(doj_markdown, unsafe_allow_html=True)
            st.markdown(emp_code_markdown, unsafe_allow_html=True)
        with col2:
            st.markdown(dob_markdown, unsafe_allow_html=True)
            st.markdown(designation_markdown, unsafe_allow_html=True)
        
        add_footer()
