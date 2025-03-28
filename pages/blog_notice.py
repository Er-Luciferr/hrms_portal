# pages/blog_notice.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import uuid
from utils.helpers import add_footer
from functools import lru_cache
from pathlib import Path

# Global variables for performance
_table_cache = {}

# Cache for styled HTML
_notice_style = """
<div style="background-color: #ffeeee; padding: 15px; border-radius: 10px; border-left: 5px solid #ff6b6b; margin-bottom: 20px;">
    <h3 style="color: #cc0000;">{title}</h3>
    <p><strong>Posted by:</strong> {author} ({designation}) | <strong>Date:</strong> {date}</p>
    <p>{content}</p>
</div>
"""

_blog_style = """
<div style="background-color: #f9f9f9; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
    <h3>{title}</h3>
    <p><strong>Posted by:</strong> {author} ({designation}) | <strong>Date:</strong> {date}</p>
    <p>{content}</p>
</div>
"""

def load_table(table_name):
    """Load a table from a CSV file in the 'Database' folder with caching."""
    # Check cache first
    if table_name in _table_cache:
        return _table_cache[table_name].copy()
    
    try:
        # Create file if it doesn't exist for blogs table
        if table_name == 'blogs' and not os.path.exists(f"Database/{table_name}.csv"):
            df = pd.DataFrame(columns=[
                'id', 'title', 'content', 'author', 'author_id', 'date', 'image_path', 
                'designation', 'post_type'
            ])
            df.to_csv(f"Database/{table_name}.csv", index=False)
            _table_cache[table_name] = df.copy()
            return df
            
        # Read the existing file
        df = pd.read_csv(f"Database/{table_name}.csv")
        
        # Cache the result
        _table_cache[table_name] = df.copy()
        return df
    except FileNotFoundError:
        # Create an empty DataFrame with appropriate columns
        if table_name == 'blogs':
            df = pd.DataFrame(columns=[
                'id', 'title', 'content', 'author', 'author_id', 'date', 'image_path', 
                'designation', 'post_type'
            ])
            # Ensure directory exists
            os.makedirs("Database", exist_ok=True)
            df.to_csv(f"Database/{table_name}.csv", index=False)
            _table_cache[table_name] = df.copy()
            return df
        return pd.DataFrame()

def save_table(table_name, df):
    """Save a DataFrame to a CSV file in the 'Database' folder and update cache."""
    df.to_csv(f"Database/{table_name}.csv", index=False)
    # Update cache
    _table_cache[table_name] = df.copy()

def clear_cache(table_name=None):
    """Clear specific table cache or all caches."""
    global _table_cache
    if table_name:
        if table_name in _table_cache:
            del _table_cache[table_name]
    else:
        _table_cache = {}

def ensure_directories():
    """Ensure all required directories exist."""
    Path("Database/blog_images").mkdir(parents=True, exist_ok=True)
    
class BlogNoticePage:
    def __init__(self):
        # Ensure directories exist at initialization
        ensure_directories()
        
    def display(self):
        st.title("Blogs and Notice Board")
        
        # Create tabs for viewing and posting
        view_tab, post_tab = st.tabs(["View Posts", "Create Post"])
        
        with view_tab:
            self._display_posts()
        
        with post_tab:
            self._create_post()
        
        add_footer()
    
    def _display_posts(self):
        # Load blogs with caching
        blogs_df = load_table("blogs")
        
        if blogs_df.empty:
            st.info("No posts yet. Be the first to share your thoughts!")
            return
        
        # Use more efficient filtering with query
        notices = blogs_df.query("post_type == 'Notice'").sort_values('date', ascending=False)
        blogs = blogs_df.query("post_type == 'Blog'").sort_values('date', ascending=False)
        
        # Display notices first with a distinct style
        if not notices.empty:
            st.markdown("## 📢 Important Notices")
            self._render_posts(notices, is_notice=True)
            
        # Display regular blog posts
        if not blogs.empty:
            st.markdown("## Blog Posts")
            self._render_posts(blogs, is_notice=False)
    
    def _render_posts(self, posts_df, is_notice=False):
        """Render a group of posts more efficiently."""
        template = _notice_style if is_notice else _blog_style
        
        for _, post in posts_df.iterrows():
            with st.container():
                # Format post with template string - more efficient than f-strings
                html = template.format(
                    title=post['title'],
                    author=post['author'],
                    designation=post['designation'],
                    date=post['date'],
                    content=post['content']
                )
                st.markdown(html, unsafe_allow_html=True)
                
                # Display image if it exists - more efficient path checking
                image_path = post.get('image_path')
                if pd.notna(image_path) and os.path.exists(image_path):
                    st.image(image_path, width=400, use_container_width=False)
                
                # Delete button for HR users
                is_hr = st.session_state.get('user_data', {}).get('designation', '').upper() == 'HR'
                if is_hr:
                    post_type = "Notice" if is_notice else "Post"
                    if st.button(f"Delete {post_type}", key=f"delete_{post_type.lower()}_{post['id']}"):
                        self._delete_post(post['id'])
                
                st.markdown("<hr>", unsafe_allow_html=True)
    
    def _delete_post(self, post_id):
        """Delete a post with better error handling."""
        try:
            blogs_df = load_table("blogs")
            
            # Get image path before deleting
            post_row = blogs_df[blogs_df['id'] == post_id]
            if not post_row.empty and pd.notna(post_row.iloc[0]['image_path']):
                image_path = post_row.iloc[0]['image_path']
                # Try to delete the image file
                try:
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except OSError:
                    # Continue even if image deletion fails
                    pass
            
            # Filter out the deleted post
            blogs_df = blogs_df[blogs_df['id'] != post_id]
            save_table("blogs", blogs_df)
            st.success("Post deleted successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error deleting post: {e}")
    
    def _create_post(self):
        """Create a new post with improved form handling and validation."""
        # Get user data
        user_data = st.session_state.get('user_data', {})
        if not user_data:
            st.warning("You must be logged in to post.")
            return
        
        is_hr = user_data.get('designation', '').upper() == 'HR'
        
        # Post type selection (HR can post notices)
        post_type = 'Blog'
        if is_hr:
            post_type = st.radio("Select post type:", ["Blog", "Notice"])
        
        # Create post form
        with st.form(key="blog_post_form"):
            st.subheader(f"Create a New {post_type}")
            title = st.text_input("Title")
            content = st.text_area("Content", height=200)
            uploaded_file = st.file_uploader("Add an image (optional)", type=["jpg", "jpeg", "png"])
            
            submit_button = st.form_submit_button("Post")
            
            if submit_button:
                if self._validate_and_submit_post(title, content, post_type, uploaded_file, user_data):
                    st.rerun()
    
    def _validate_and_submit_post(self, title, content, post_type, uploaded_file, user_data):
        """Validate and submit a post with better error handling."""
        # Validate inputs
        if not title.strip():
            st.error("Please provide a title for your post.")
            return False
        
        if not content.strip():
            st.error("Please write some content for your post.")
            return False
        
        # Process image if uploaded
        image_path = None
        if uploaded_file is not None:
            try:
                # Create unique filename more efficiently
                file_extension = Path(uploaded_file.name).suffix
                unique_filename = f"{uuid.uuid4()}{file_extension}"
                image_dir = Path("Database/blog_images")
                image_path = str(image_dir / unique_filename)
                
                # Make sure directory exists
                image_dir.mkdir(parents=True, exist_ok=True)
                
                # Save the file with better resource management
                with open(image_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
            except Exception as e:
                st.error(f"Error saving image: {e}")
                return False
        
        try:
            # Load existing blogs with caching
            blogs_df = load_table("blogs")
            
            # Create new blog entry with more efficient ID generation
            new_id = str(uuid.uuid4())
            
            # Create new post directly as DataFrame row
            new_post = pd.DataFrame([{
                'id': new_id,
                'title': title,
                'content': content,
                'author': user_data.get('name', 'Anonymous'),
                'author_id': user_data.get('employee_code', ''),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'image_path': image_path,
                'designation': user_data.get('designation', ''),
                'post_type': post_type
            }])
            
            # Append new post and save more efficiently
            blogs_df = pd.concat([blogs_df, new_post], ignore_index=True)
            save_table("blogs", blogs_df)
            
            st.success(f"Your {post_type.lower()} has been posted successfully!")
            return True
        except Exception as e:
            st.error(f"Error creating post: {e}")
            return False