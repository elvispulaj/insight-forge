
import streamlit as st
import json
import os

PROFILE_FILE = "user_profiles.json"

def load_profile(username):
    """Load profile data for a specific user."""
    if not os.path.exists(PROFILE_FILE):
        return {}
    
    try:
        with open(PROFILE_FILE, "r") as f:
            profiles = json.load(f)
            return profiles.get(username, {})
    except:
        return {}

def save_profile(username, data):
    """Save profile data for a specific user."""
    profiles = {}
    if os.path.exists(PROFILE_FILE):
        try:
            with open(PROFILE_FILE, "r") as f:
                profiles = json.load(f)
        except:
            pass
    
    profiles[username] = data
    with open(PROFILE_FILE, "w") as f:
        json.dump(profiles, f, indent=4)

def render_profile_page():
    """Render the User Profile management page."""
    st.markdown("## 👤 User Profile")
    st.markdown("Manage your personal information and application settings.")
    
    if 'username' not in st.session_state or not st.session_state['username']:
        st.warning("Please log in to view your profile.")
        return

    username = st.session_state['username']
    profile_data = load_profile(username)

    # Initialize session state for form if not exists
    if "profile_form_data" not in st.session_state or st.session_state.get("last_loaded_user") != username:
         st.session_state["profile_form_data"] = profile_data
         st.session_state["last_loaded_user"] = username

    # Create avatar directory
    avatar_dir = "data/avatars"
    if not os.path.exists(avatar_dir):
        os.makedirs(avatar_dir, exist_ok=True)
    
    avatar_path = os.path.join(avatar_dir, f"{username}.png")
    
    # Check if avatar exists
    has_avatar = os.path.exists(avatar_path)
    
    # ── Profile Header Card ──
    # Allow Upload
    with st.expander("📷 Update Profile Picture"):
        uploaded_file = st.file_uploader("Upload Image (PNG/JPG)", type=['png', 'jpg', 'jpeg'])
        if uploaded_file is not None:
            with open(avatar_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("Profile picture updated!")
            st.rerun()

    # Encode image to base64 for HTML display if exists
    import base64
    avatar_html = ""
    if has_avatar:
        with open(avatar_path, "rb") as f:
            img_data = f.read()
        b64_img = base64.b64encode(img_data).decode()
        avatar_html = f'<img src="data:image/png;base64,{b64_img}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; box-shadow: 0 0 20px rgba(0, 229, 255, 0.4); border: 2px solid #00E5FF;">'
    else:
        # Default Initial
        avatar_html = f'''
            <div style="
                width: 80px; height: 80px; 
                background: linear-gradient(135deg, #2979FF, #00E5FF);
                border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                font-size: 2.5rem; color: #FFFFFF; font-weight: bold;
                box-shadow: 0 0 20px rgba(41, 121, 255, 0.4);
            ">
                {username[0].upper()}
            </div>
        '''

    st.markdown(f"""
    <div class="insight-card" style="margin-bottom: 2rem; display: flex; align-items: center; gap: 1.5rem;">
        {avatar_html}
        <div>
            <h2 style="margin: 0; color: white;">{profile_data.get('full_name', username)}</h2>
            <p style="margin: 0; color: #9E9E9E;">{profile_data.get('role', 'Data Analyst')}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Edit Profile Form ──
    with st.container():
        st.markdown("### ✏️ Edit Profile")
        
        with st.form("profile_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                full_name = st.text_input("Full Name", value=profile_data.get("full_name", ""))
                email = st.text_input("Email Address", value=profile_data.get("email", ""))
                phone = st.text_input("Phone Number", value=profile_data.get("phone", ""))
            
            with col2:
                role = st.text_input("Role / Job Title", value=profile_data.get("role", ""))
                company = st.text_input("Company / Organization", value=profile_data.get("company", ""))
                api_key = st.text_input("OpenAI API Key (Persistent)", type="password", value=profile_data.get("openai_api_key", ""))

            bio = st.text_area("Bio / Notes", value=profile_data.get("bio", ""), height=100)

            submitted = st.form_submit_button("Save Changes", type="primary")

            if submitted:
                updated_data = {
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "role": role,
                    "company": company,
                    "openai_api_key": api_key,
                    "bio": bio
                }
                save_profile(username, updated_data)
                st.success("Profile updated successfully!")
                
                # Update Session State if API Key changed
                if api_key:
                     # You might want to update a config or session var here so it applies immediately
                     st.session_state["persistent_api_key"] = api_key
                
                st.rerun()

    # ── Account Settings ──
    st.markdown("### 🔒 Security")
    with st.expander("Change Password"):
        curr_pass = st.text_input("Current Password", type="password")
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm New Password", type="password")
        if st.button("Update Password"):
            st.warning("Password update functionality coming soon.") 
