
import streamlit as st
import hashlib
import json
import os

USER_DB_FILE = "users.json"

def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(str.encode(password)).hexdigest()

def load_users():
    """Load users from the JSON database."""
    if not os.path.exists(USER_DB_FILE):
        return {}
    try:
        with open(USER_DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    """Save users to the JSON database."""
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)

def authenticate(username, password):
    """Check if the username/password combination is valid."""
    users = load_users()
    if username in users and users[username] == hash_password(password):
        return True
    return False

def register_user(username, password):
    """Register a new user."""
    users = load_users()
    if username in users:
        return False # User already exists
    
    users[username] = hash_password(password)
    save_users(users)
    return True

def reset_password(username, new_password):
    """Reset a user's password."""
    users = load_users()
    if username not in users:
        return False
    users[username] = hash_password(new_password)
    save_users(users)
    return True

def render_login_page():
    """Render the login/signup UI with Reset Password option."""
    # Styles are now handled globally by styles.css

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
            <div class="login-card">
                <div class="login-title">InsightForge</div>
                <div class="login-subtitle">Secure Intelligence Platform</div>
            </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["Log In", "Create Account", "Forgot Password"])
        
        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Log In", type="primary")
                
                if submit:
                    if authenticate(username, password):
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = username
                        st.session_state['show_login_page'] = False # Immediate redirect
                        st.success("Access Granted")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")

        with tab2:
            with st.form("signup_form"):
                new_user = st.text_input("Choose Username")
                new_pass = st.text_input("Choose Password", type="password")
                submit_reg = st.form_submit_button("Create Account", type="primary")
                
                if submit_reg:
                    if new_user and new_pass:
                        if register_user(new_user, new_pass):
                            st.success("Account created! Please log in.")
                        else:
                            st.error("Username already exists.")
                    else:
                        st.warning("Please fill in all fields.")
        
        with tab3:
             st.markdown("### Reset Password")
             with st.form("reset_form"):
                reset_user = st.text_input("Enter Username")
                new_pass_reset = st.text_input("New Password", type="password")
                # In a real app, we'd ask for an email or security question here
                st.caption("⚠️ Developer Mode: Password reset is open for testing.")
                submit_reset = st.form_submit_button("Reset Password", type="primary")
                
                if submit_reset:
                    if reset_user and new_pass_reset:
                        if reset_password(reset_user, new_pass_reset):
                            st.success("Password reset successfully! Please log in.")
                        else:
                            st.error("Username not found.")
                    else:
                        st.warning("Please fill in all fields.")
