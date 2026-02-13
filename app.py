"""
InsightForge - AI-Powered Business Intelligence Assistant
Main Streamlit Application Entry Point

Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import os
import sys

from config import Config
from data_loader import DataLoader
from rag_engine import RAGEngine
from llm_engine import LLMEngine
from visualizer import Visualizer
from sample_data import generate_sales_data, generate_hr_data, generate_marketing_data
from streamlit_mic_recorder import mic_recorder

# ── Page Configuration ──────────────────────────────────────

st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout=Config.LAYOUT,
    initial_sidebar_state="expanded",
)

# ── Authentication Check ────────────────────────────────────
# ── Authentication & Top Bar ────────────────────────────────
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'show_login_page' not in st.session_state:
    st.session_state['show_login_page'] = False

from auth import render_login_page
from profile import render_profile_page, load_profile

# 1. If user wants to see login page, show it and stop
if st.session_state['show_login_page']:
    # Hide Sidebar Completely
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none;}
            section[data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)
    
    # Subtle Back Button (Top Left)
    col_back, _ = st.columns([1, 6])
    with col_back:
        if st.button("← Back", type="secondary"):
            st.session_state['show_login_page'] = False
            st.rerun()
            
    render_login_page()
    st.stop()

# 2. Render Top Bar (Login/Logout)
auth_col1, auth_col2 = st.columns([8, 1]) # Give even more space to content
with auth_col2:
    if st.session_state['logged_in']:
        if st.button("Logout", type="secondary"):
            st.session_state['logged_in'] = False
            st.session_state['username'] = None
            st.rerun()
    else:
        # Short text prevents wrapping/bubble effect
        if st.button("Log in", type="primary"): 
            st.session_state['show_login_page'] = True
            st.rerun()


# ── Custom CSS ──────────────────────────────────────────────

def local_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("styles.css")


# ── Session State Initialization ────────────────────────────

def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "df": None,
        "doc_text": None,
        "file_name": None,
        "data_context": None,
        "rag_engine": None,
        "llm_engine": None,
        "visualizer": Visualizer(),
        "chat_history": [],
        "analysis_result": None,
        "api_key_set": False,
        "current_page": "🏠 Dashboard",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def auto_load_data():
    """Auto-load the most recently modified file in the upload directory."""
    # SECURITY: Only load data if user is logged in
    if not st.session_state.get('logged_in'):
        return

    # Only load if nothing is currently loaded
    if st.session_state.df is not None or st.session_state.doc_text is not None:
        return

    upload_dir = Config.UPLOAD_DIR
    if not os.path.exists(upload_dir):
        return
        
    # Get all files with full paths
    files = [os.path.join(upload_dir, f) for f in os.listdir(upload_dir) 
             if os.path.isfile(os.path.join(upload_dir, f)) and not f.startswith('.')]
    
    if not files:
        return
        
    # Get latest file
    latest_file = max(files, key=os.path.getmtime)
    filename = os.path.basename(latest_file)
    
    # st.sidebar.info(f"🔄 Auto-loading: {filename}") # Optional feedback
    
    try:
        # Load data based on type
        df = None
        doc_text = None
        
        if DataLoader.is_tabular(filename):
            df = DataLoader.load_tabular(latest_file)
        elif DataLoader.is_document(filename):
            doc_text = DataLoader.load_document(latest_file)
        
        if df is not None or doc_text is not None:
            st.session_state.file_name = filename
            st.session_state.df = df
            st.session_state.doc_text = doc_text
            
            # Rebuild RAG context silently
            rag = RAGEngine()
            if df is not None:
                context = DataLoader.dataframe_to_context(df)
                st.session_state.data_context = context
                docs = rag.create_documents_from_dataframe(context, filename)
            else:
                st.session_state.data_context = doc_text
                docs = rag.create_documents_from_text(doc_text, filename)
            
            rag.build_vector_store(docs)
            st.session_state.rag_engine = rag
            
    except Exception as e:
        # Fail silently or log to console, don't break app flow
        print(f"Auto-load failed for {filename}: {e}")

init_session_state()
auto_load_data()


# ── Sidebar ─────────────────────────────────────────────────

def render_sidebar():
    """Render the sidebar with configuration and file upload."""
    with st.sidebar:
        # Brand
        st.markdown("""
        <div class="sidebar-brand">
            <div class="brand-logo">
                <i class="fa-solid fa-chart-line"></i>
            </div>
            <h2>InsightForge</h2>
            <p>AI Business Intelligence</p>
        </div>
        """, unsafe_allow_html=True)

        # Navigation
        st.session_state.current_page = st.radio(
            "**Navigation**",
            ["Dashboard", "AI Analysis", "Ask Questions", "Visualizations", "My Files", "User Profile"],
            label_visibility="visible",
        )

        st.divider()

        # ── API Key Configuration ───────────────
        st.markdown("##### ⚙️ Configuration")

        # Check for persistent key in profile
        default_api_key = ""
        if 'username' in st.session_state and st.session_state.username:
             user_profile = load_profile(st.session_state.username)
             default_api_key = user_profile.get("openai_api_key", "")
        
        if not default_api_key and Config.is_api_key_set():
             default_api_key = Config.OPENAI_API_KEY
        
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=default_api_key,
            help="Enter your OpenAI API key to enable AI features. Key is saved in your Profile.",
            placeholder="sk-...",
        )

        if api_key and api_key != "your-openai-api-key-here":
            st.session_state.api_key_set = True
            if st.session_state.llm_engine is None or st.session_state.llm_engine.api_key != api_key:
                st.session_state.llm_engine = LLMEngine(api_key=api_key)
            st.markdown('<span class="status-badge status-connected">● AI Connected</span>', unsafe_allow_html=True)
        else:
            st.session_state.api_key_set = False
            st.markdown('<span class="status-badge status-disconnected">● AI Disconnected</span>', unsafe_allow_html=True)

        st.divider()

        # ── File Upload ─────────────────────────
        st.markdown("##### 📁 Data Source")

        upload_option = st.radio(
            "Choose data source",
            ["Upload File", "Sample Dataset"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if upload_option == "Upload File":
            uploaded_file = st.file_uploader(
                "Upload your business data",
                type=Config.ALLOWED_EXTENSIONS,
                help="Supported: CSV, Excel, PDF, DOCX, TXT, JSON",
            )

            if uploaded_file is not None and uploaded_file.name != st.session_state.file_name:
                with st.spinner("📥 Processing file..."):
                    try:
                        loader = DataLoader()
                        df, doc_text, save_path = loader.load_file(uploaded_file)

                        st.session_state.file_name = uploaded_file.name
                        st.session_state.df = df
                        st.session_state.doc_text = doc_text

                        # Build RAG
                        rag = RAGEngine()
                        if df is not None:
                            context = loader.dataframe_to_context(df)
                            st.session_state.data_context = context
                            docs = rag.create_documents_from_dataframe(context, uploaded_file.name)
                        else:
                            st.session_state.data_context = doc_text
                            docs = rag.create_documents_from_text(doc_text, uploaded_file.name)

                        rag.build_vector_store(docs)
                        st.session_state.rag_engine = rag

                        st.success(f"✅ Loaded: **{uploaded_file.name}**")
                    except Exception as e:
                        st.error(f"Error: {e}")

        else:
            sample_choice = st.selectbox(
                "Select sample dataset",
                ["Sales Data", "HR Data", "Marketing Data"],
            )

            if st.button("📥 Load Sample", use_container_width=True):
                with st.spinner("Loading sample data..."):
                    generators = {
                        "Sales Data": ("sales_data.csv", generate_sales_data),
                        "HR Data": ("hr_data.csv", generate_hr_data),
                        "Marketing Data": ("marketing_data.csv", generate_marketing_data),
                    }
                    name, gen_func = generators[sample_choice]
                    df = gen_func()
                    st.session_state.df = df
                    st.session_state.doc_text = None
                    st.session_state.file_name = name

                    loader = DataLoader()
                    context = loader.dataframe_to_context(df)
                    st.session_state.data_context = context

                    rag = RAGEngine()
                    docs = rag.create_documents_from_dataframe(context, name)
                    rag.build_vector_store(docs)
                    st.session_state.rag_engine = rag

                    st.success(f"✅ Loaded: **{name}**")
                    st.rerun()

        # ── Data Status ─────────────────────────
        if st.session_state.file_name:
            st.divider()
            st.markdown("##### 📋 Loaded Data")
            st.info(f"**{st.session_state.file_name}**")
            if st.session_state.df is not None:
                st.caption(f"{st.session_state.df.shape[0]:,} rows × {st.session_state.df.shape[1]} columns")
            if st.session_state.rag_engine and st.session_state.rag_engine.is_ready:
                st.caption(f"🧠 RAG: {st.session_state.rag_engine.document_count} chunks indexed")

        # Footer
        st.divider()
        
        # Reset Button (User Request)
        if st.button("🗑️ Reset All Data", type="secondary", use_container_width=True):
            # Clear session state but keep login
            keys_to_keep = ['logged_in', 'username', 'show_login_page']
            for key in list(st.session_state.keys()):
                if key not in keys_to_keep:
                    del st.session_state[key]
            st.rerun()

        st.caption("Built with ❤️ using LangChain, RAG & OpenAI")


render_sidebar()


# ══════════════════════════════════════════════════════════════
# COMPONENT: Top User Header
# ══════════════════════════════════════════════════════════════

def render_user_header():
    """Render the Glass/Gradient User Header if logged in."""
    # Ensure FontAwesome is loaded globally for logged-in users too
    st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">', unsafe_allow_html=True)
    
    if st.session_state.get('logged_in'):
        username = st.session_state.get('username', 'User')
        
        # Avatar Logic
        avatar_path = f"data/avatars/{username}.png"
        import base64
        
        avatar_html = ""
        if os.path.exists(avatar_path):
            with open(avatar_path, "rb") as f:
                b64_img = base64.b64encode(f.read()).decode()
            avatar_html = f'<img src="data:image/png;base64,{b64_img}" style="width: 32px; height: 32px; border-radius: 50%; object-fit: cover; border: 1px solid rgba(255,255,255,0.5);">'
        else:
             avatar_html = f'<div style="width: 32px; height: 32px; background: linear-gradient(135deg, #2979FF, #00E5FF); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1rem; color: #FFFFFF; font-weight: bold;">{username[0].upper()}</div>'

        # Render Header with Glass Gradient
        col_spacer, col_user = st.columns([5, 3])
        with col_user:
            st.markdown(f"""
            <div style="
                display: flex; justify-content: flex-end; align-items: center; 
                padding: 8px 16px; 
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                margin-bottom: 20px;
                width: fit-content;
                margin-left: auto;
            ">
                <div style="display: flex; align-items: center; gap: 10px;">
                    {avatar_html}
                    <span style="font-weight: 600; font-size: 0.9rem; color: #FFFFFF; letter-spacing: 0.5px;">{username}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# PAGE: Image Analysis Dashboard (New)
# ══════════════════════════════════════════════════════════════

def render_image_dashboard():
    """Render the dashboard for Image Analysis mode."""
    st.markdown('<div class="section-title"><div class="icon-circle"><i class="fa-solid fa-eye"></i></div>AI Vision Analysis</div>', unsafe_allow_html=True)
    
    file_path = os.path.join(Config.UPLOAD_DIR, st.session_state.file_name)
    
    if not os.path.exists(file_path):
        st.error("Image file not found.")
        return

    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🖼️ Source Image")
        st.image(file_path, caption=st.session_state.file_name, use_container_width=True)
        
    with col2:
        st.markdown("### 🤖 AI Insights")
        
        if 'image_analysis_result' not in st.session_state:
            st.session_state.image_analysis_result = None
            
        if st.session_state.image_analysis_result:
             st.markdown(st.session_state.image_analysis_result)
             st.markdown("---")
             if st.button("🔄 Re-Analyze", key="reanalyze_btn"):
                 st.session_state.image_analysis_result = None
                 st.rerun()
        else:
             st.info("I can 'see' this image and extract data, trends, and insights for you.")
             if st.button("👁️ Analyze Image", type="primary", use_container_width=True):
                 if not st.session_state.api_key_set:
                     st.warning("Please configure OpenAI API Key first.")
                 else:
                     with st.spinner("🤖 Analyzing image contents... (this requires GPT-4o-mini Vision)"):
                         try:
                             # Prompt optimized for business charts
                             prompt = "Analyze this business image. If it's a chart, extract the data trends. If it's a document/receipt, extract the key info. Provide a structured summary."
                             result = st.session_state.llm_engine.analyze_image(file_path, prompt)
                             st.session_state.image_analysis_result = result
                             st.rerun()
                         except Exception as e:
                             st.error(f"Analysis failed: {e}")

# ══════════════════════════════════════════════════════════════
# PAGE: Dashboard
# ══════════════════════════════════════════════════════════════

def render_dashboard():
    """Render the main dashboard page."""
    
    # ── GUEST VIEW (Not Logged In) ──
    if not st.session_state.get('logged_in'):
        # 1. Inject CSS and FontAwesome (Hidden from view)
        st.markdown("""
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
            <style>
                /* Deep Blue Aurora Background (No Purple) */
                .stApp {
                    background-color: #02040a !important;
                    background-image: 
                        radial-gradient(circle at 15% 50%, rgba(0, 100, 255, 0.15) 0%, transparent 50%),
                        radial-gradient(circle at 85% 30%, rgba(0, 229, 255, 0.15) 0%, transparent 50%),
                        radial-gradient(circle at 50% 0%, rgba(41, 121, 255, 0.1) 0%, transparent 50%) !important;
                }
                
                .landing-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                    padding-top: 4rem;
                    position: relative;
                    max-width: 1200px;
                    margin: 0 auto;
                    z-index: 10;
                }

                .hero-text {
                    font-size: 5rem;
                    font-weight: 800;
                    color: #FFFFFF;
                    line-height: 1.1;
                    margin-bottom: 1.5rem;
                    letter-spacing: -2px;
                    text-shadow: 0 0 40px rgba(41, 121, 255, 0.4);
                }
                
                .highlight-blue {
                    background: linear-gradient(90deg, #2979FF, #00E5FF);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    display: block; 
                }

                .hero-subtext {
                    font-size: 1.3rem;
                    color: #94A3B8;
                    margin-bottom: 5rem;
                    max-width: 700px;
                    line-height: 1.6;
                }

                /* 3-Box Feature Grid */
                .landing-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 30px;
                    width: 100%;
                    padding: 0 20px;
                }

                .landing-card {
                    background: rgba(255, 255, 255, 0.03);
                    backdrop-filter: blur(20px);
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    border-radius: 24px;
                    padding: 2.5rem;
                    text-align: left;
                    transition: transform 0.3s ease, background 0.3s ease;
                    position: relative;
                    overflow: hidden;
                    cursor: pointer; /* Makes it feel interactive */
                }

                .landing-card:hover {
                    transform: translateY(-10px);
                    background: rgba(255, 255, 255, 0.06);
                    border-color: rgba(41, 121, 255, 0.3);
                    box-shadow: 0 20px 40px rgba(0,0,0,0.5);
                }

                .card-icon {
                    font-size: 2.5rem;
                    color: #2979FF;
                    margin-bottom: 1.5rem;
                    background: rgba(41, 121, 255, 0.1);
                    width: 60px;
                    height: 60px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 16px;
                }

                .card-title {
                    font-size: 1.5rem;
                    font-weight: 700;
                    color: white;
                    margin-bottom: 0.8rem;
                }

                .card-desc {
                    color: #94A3B8;
                    line-height: 1.5;
                    font-size: 1rem;
                }

                /* Floating Icons */
                .floating-icon {
                    position: absolute;
                    color: rgba(255, 255, 255, 0.05);
                    animation: float 6s ease-in-out infinite;
                    z-index: 1; 
                }
                
                @keyframes float {
                    0% { transform: translateY(0px); }
                    50% { transform: translateY(-20px); }
                    100% { transform: translateY(0px); }
                }

                .icon-container { position: relative; width: 100%; height: 0; }
                .icon-1 { top: -20px; left: 10%; font-size: 2rem; animation-delay: 0s; }
                .icon-2 { top: 80px; right: 15%; font-size: 1.5rem; animation-delay: 1s; }
                .icon-3 { bottom: -300px; left: 5%; font-size: 3rem; animation-delay: 2s; }
                .icon-4 { bottom: -250px; right: 8%; font-size: 2.5rem; animation-delay: 0.5s; }

            </style>
        """, unsafe_allow_html=True)

        # 2. Render HTML Content
        st.markdown("""
<div class="landing-container">
<div class="icon-container">
<div class="floating-icon icon-1"><i class="fa-solid fa-chart-line"></i></div>
<div class="floating-icon icon-2"><i class="fa-solid fa-cloud"></i></div>
<div class="floating-icon icon-3"><i class="fa-solid fa-robot"></i></div>
<div class="floating-icon icon-4"><i class="fa-solid fa-shield-halved"></i></div>
</div>

<div class="hero-text">
Everything you need for
<span class="highlight-blue">AI Business Intelligence</span>
</div>

<div class="hero-subtext">
Transform raw data into actionable insights instantly. 
The feature your stakeholders want, but your engineering team hates building from scratch.
</div>

<div class="landing-grid">
<div class="landing-card">
<div class="card-icon"><i class="fa-solid fa-magnifying-glass-chart"></i></div>
<div class="card-title">AI Analysis</div>
<div class="card-desc">Instantly uncover hidden patterns and trends in your data using advanced LLM algorithms.</div>
</div>

<div class="landing-card">
<div class="card-icon"><i class="fa-solid fa-chart-pie"></i></div>
<div class="card-title">Interactive Visuals</div>
<div class="card-desc">Create stunning, dynamic charts that bring your complex datasets to life with a single click.</div>
</div>

<div class="landing-card">
<div class="card-icon"><i class="fa-solid fa-shield-halved"></i></div>
<div class="card-title">Secure & Private</div>
<div class="card-desc">Enterprise-grade encryption ensures your sensitive business data never leaves your secure environment.</div>
</div>
</div>

</div>
""", unsafe_allow_html=True)
            
        return

    # ── AUTHENTICATED VIEW ──
    render_user_header()

    # Hero
    st.markdown("""
    <div class="hero-header">
        <h1><i class="fa-solid fa-chart-line" style="color: #2979FF; margin-right: 15px;"></i>Welcome to InsightForge</h1>
        <p>Transform your business data into actionable intelligence with AI-powered analysis</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Quick Access Grid (Using Premium Icons) ──
    st.markdown("""
    <div class="dashboard-grid">
        <div class="dashboard-card">
            <div class="icon-circle"><i class="fa-solid fa-magnifying-glass-chart"></i></div>
            <div class="feature-title">AI Analysis</div>
            <div class="feature-desc">Deep insights & trends</div>
        </div>
        <div class="dashboard-card">
            <div class="icon-circle"><i class="fa-solid fa-chart-pie"></i></div>
            <div class="feature-title">Interactive Viz</div>
            <div class="feature-desc">Dynamic charts</div>
        </div>
        <div class="dashboard-card">
            <div class="icon-circle"><i class="fa-solid fa-comments"></i></div>
            <div class="feature-title">Conversational BI</div>
            <div class="feature-desc">Chat with your data</div>
        </div>
        <div class="dashboard-card">
            <div class="icon-circle"><i class="fa-solid fa-folder-open"></i></div>
            <div class="feature-title">My Files</div>
            <div class="feature-desc">Manage datasets</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Recent Alerts / Summary could go here...

    if st.session_state.df is None and st.session_state.doc_text is None:
        # Welcome Instructions (Restored)
        st.markdown("""
        **Get started in three simple steps:**

        1. **🔑 Enter your OpenAI API Key** in the sidebar to enable AI-powered analysis
        2. **📁 Upload your data** (CSV, Excel, PDF, DOCX) or load a sample dataset
        3. **🚀 Explore insights** using AI analysis, Q&A, and interactive visualizations
        """)
        st.markdown("<br>", unsafe_allow_html=True)

        st.divider()

        # Feature cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="insight-card">
                <h3>🔍 AI Analysis</h3>
                <p style="color: rgba(255,255,255,0.6);">
                    Get comprehensive analysis with trends, patterns, anomalies, 
                    and actionable recommendations powered by GPT-4.
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="insight-card">
                <h3>💬 Natural Language Q&A</h3>
                <p style="color: rgba(255,255,255,0.6);">
                    Ask questions about your data in plain English and receive 
                    data-driven answers with RAG-enhanced context.
                </p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="insight-card">
                <h3>📊 Smart Visualizations</h3>
                <p style="color: rgba(255,255,255,0.6);">
                    Auto-generated interactive charts that reveal hidden patterns 
                    and make data storytelling effortless.
                </p>
            </div>
            """, unsafe_allow_html=True)
        return

    # ── Data Loaded: Show Dashboard ─────────────────────────
    
    # Check for Image Mode
    if st.session_state.get('doc_text') == "[IMAGE_FILE]":
        render_image_dashboard()
        return

    df = st.session_state.df

    if df is not None:
        viz = st.session_state.visualizer
        
        # ── Row 1: Main Chart & Statistics Ring ────────────────
        row1_col1, row1_col2 = st.columns([2, 1])
        
        with row1_col1:
            st.markdown('<div class="section-title"><div class="icon-circle"><i class="fa-solid fa-chart-line"></i></div>My Dashboard</div>', unsafe_allow_html=True)
            # Attempt to show the most relevant trend/bar chart
            auto_figs = viz.auto_visualize(df)
            if auto_figs:
                # Use the first chart (usually distribution or trend)
                st.plotly_chart(auto_figs[0][1], use_container_width=True)
            else:
                st.info("Not enough data for trend analysis.")

        with row1_col2:
            st.markdown('<div class="section-title"><div class="icon-circle"><i class="fa-solid fa-chart-column"></i></div>Statistics</div>', unsafe_allow_html=True)
            # Create a "Progress Ring" effect using a simple Donut Chart
            # We'll use "Data Completeness" as the metric content for this ring
            missing = df.isnull().sum().sum()
            completeness = ((1 - missing / (df.shape[0] * df.shape[1])) * 100)
            
            # Simple Donut Chart for "Completeness"
            import plotly.graph_objects as go
            ring_fig = go.Figure(data=[go.Pie(
                labels=['Complete', 'Missing'],
                values=[completeness, 100-completeness],
                hole=.7,
                marker_colors=['#00E5FF','#1E1E1E'], # Cyan & Dark Grey
                textinfo='none',
                sort=False
            )])
            ring_fig.update_layout(
                showlegend=False,
                margin=dict(t=0, b=0, l=0, r=0),
                height=250,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                annotations=[dict(text=f"{int(completeness)}%", x=0.5, y=0.5, font_size=40, font_color="#FFFFFF", showarrow=False)]
            )
            st.plotly_chart(ring_fig, use_container_width=True)
            st.caption(f"Data Health Score: {completeness:.1f}%")

        # ── Row 2: KPI Cards ──────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        kpis = Visualizer.compute_kpi_cards(df)
        cols = st.columns(len(kpis))
        for i, kpi in enumerate(kpis):
            with cols[i]:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">{kpi['label']}</div>
                    <div class="kpi-icon">{kpi['icon']}</div>
                    <div class="kpi-value">{kpi['value']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Row 3: Leaderboard & Details ──────────────────────
        row3_col1, row3_col2 = st.columns([2, 1])
        
        with row3_col1:
            st.markdown('<div class="section-title">🏆 Leaderboard / Details</div>', unsafe_allow_html=True)
            st.dataframe(df.head(10), use_container_width=True, height=400)

        with row3_col2:
            st.markdown('<div class="section-title">ℹ️ Quick Stats</div>', unsafe_allow_html=True)
            st.dataframe(df.describe(), use_container_width=True, height=400)

        # Quick auto-charts (remaining)
        if auto_figs and len(auto_figs) > 1:
            st.markdown('<div class="section-title">🧩 Further Insights</div>', unsafe_allow_html=True)
            st.plotly_chart(auto_figs[1][1], use_container_width=True)

    elif st.session_state.doc_text:
        st.markdown('<div class="section-title">📄 Document Preview</div>', unsafe_allow_html=True)
        preview = st.session_state.doc_text[:3000]
        st.text_area("Document Content", preview, height=400, disabled=True)
        st.caption(f"Showing first 3,000 of {len(st.session_state.doc_text):,} characters")


# ══════════════════════════════════════════════════════════════
# PAGE: AI Analysis
# ══════════════════════════════════════════════════════════════

def render_analysis():
    """Render the AI Analysis page."""
    render_user_header()
    # Updated Header with Icon
    st.markdown('<div class="section-title"><div class="icon-circle"><i class="fa-solid fa-magnifying-glass-chart"></i></div>Data Analysis</div>', unsafe_allow_html=True)

    if not st.session_state.api_key_set:
        st.warning("⚠️ Please enter your OpenAI API key in the sidebar to enable AI analysis.")
        return

    if st.session_state.data_context is None:
        st.info("📁 Please upload data or load a sample dataset first.")
        return

    st.markdown("Choose the type of analysis you'd like to perform:")

    analysis_type = st.selectbox(
        "Analysis Type",
        ["Comprehensive Analysis", "Custom Analysis"],
        label_visibility="collapsed",
    )

    if analysis_type == "Comprehensive Analysis":
        if st.button("🚀 Run Comprehensive Analysis", type="primary", use_container_width=True):
            with st.spinner("🤖 AI is analyzing your data... This may take a moment."):
                try:
                    rag_context = ""
                    if st.session_state.rag_engine and st.session_state.rag_engine.is_ready:
                        rag_context = st.session_state.rag_engine.get_context_for_query(
                            "Analyze key trends, patterns, and provide business recommendations"
                        )

                    result = st.session_state.llm_engine.analyze_data(
                        data_context=st.session_state.data_context,
                        rag_context=rag_context,
                    )
                    st.session_state.analysis_result = result
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    else:
        custom_request = st.text_area(
            "Describe your analysis request",
            placeholder="e.g., Analyze sales performance by region and identify the top 3 growth opportunities...",
            height=100,
        )
        if st.button("🚀 Run Custom Analysis", type="primary", use_container_width=True) and custom_request:
            with st.spinner("🤖 Running custom analysis..."):
                try:
                    rag_context = ""
                    if st.session_state.rag_engine and st.session_state.rag_engine.is_ready:
                        rag_context = st.session_state.rag_engine.get_context_for_query(custom_request)

                    result = st.session_state.llm_engine.custom_analysis(
                        analysis_request=custom_request,
                        data_context=st.session_state.data_context,
                        rag_context=rag_context,
                    )
                    st.session_state.analysis_result = result
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    # Display results
    if st.session_state.analysis_result:
        st.divider()
        st.markdown('<div class="insight-card">', unsafe_allow_html=True)
        st.markdown(st.session_state.analysis_result)
        st.markdown('</div>', unsafe_allow_html=True)

        # Download button
        st.download_button(
            label="📥 Download Analysis Report",
            data=st.session_state.analysis_result,
            file_name="insightforge_analysis.md",
            mime="text/markdown",
        )


# ══════════════════════════════════════════════════════════════
# PAGE: Ask Questions (Q&A)
# ══════════════════════════════════════════════════════════════

def render_qa():
    """Render the Q&A chat page."""
    render_user_header()
    # Updated Header with Icon
    st.markdown('<div class="section-title"><div class="icon-circle"><i class="fa-solid fa-comments"></i></div>Ask Questions</div>', unsafe_allow_html=True)

    if not st.session_state.api_key_set:
        st.warning("⚠️ Please enter your OpenAI API key in the sidebar to enable Q&A.")
        return

    if st.session_state.data_context is None:
        st.info("📁 Please upload data or load a sample dataset first.")
        return

    st.markdown("Ask any business question about your data in natural language.")

    # Chat history display
    for msg in st.session_state.chat_history:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            st.markdown(f"""
            <div class="chat-message chat-user">
                <strong>👤 You:</strong><br>{content}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message chat-assistant">
                <strong>🤖 InsightForge:</strong><br>{content}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("Ask any business question about your data in natural language.")

    # ── Voice Input Section (Top) ──
    voice_col1, voice_col2 = st.columns([1, 5])
    with voice_col1:
        st.markdown("**🎙️ Voice Input:**")
        audio = mic_recorder(
            start_prompt="Start Recording 🔴",
            stop_prompt="Stop Recording ⏹️",
            just_once=True,
            key='voice_recorder_top'
        )
    
    voice_text = None
    if audio:
        with st.spinner("🎧 Transcribing..."):
            try:
                import io
                from openai import OpenAI
                
                audio_bytes = audio['bytes']
                # Create a file-like object
                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = "voice_input.wav"
                
                client = OpenAI(api_key=st.session_state.llm_engine.api_key)
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    response_format="text"
                )
                voice_text = transcript
                st.success(f"🗣️ You said: *{voice_text}*")
                
            except Exception as e:
                st.error(f"Voice Error: {e}")

    st.divider()

    # Chat history display
        
    if audio:
        with st.spinner("🎧 Transcribing..."):
            try:
                # Save audio to a temporary file
                import io
                audio_bytes = audio['bytes']
                
                # OpenAI Whisper API expects a file-like object with a name
                # We can't send raw bytes directly to some versions of the SDK, 
                # so we might need a temp file or a named BytesIO
                from openai import OpenAI
                client = OpenAI(api_key=st.session_state.llm_engine.api_key)
                
                # Create a file-like object
                audio_file = io.BytesIO(audio_bytes)
                audio_file.name = "voice_input.wav"
                
                transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    response_format="text"
                )
                
                voice_text = transcript
                
            except Exception as e:
                st.error(f"Voice Error: {e}")

    # Standard Chat Input
    text_input = st.chat_input("Ask a question about your data...")
    
    # Process Inputs
    question_to_ask = None
    if text_input:
        question_to_ask = text_input
    elif voice_text:
        # Use the voice text captured from the top section
        question_to_ask = voice_text
    
    if question_to_ask:
        question = question_to_ask
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": question})

        with st.spinner("🤖 Thinking..."):
            try:
                rag_context = ""
                if st.session_state.rag_engine and st.session_state.rag_engine.is_ready:
                    rag_context = st.session_state.rag_engine.get_context_for_query(question)

                answer = st.session_state.llm_engine.answer_question(
                    question=question,
                    data_context=st.session_state.data_context,
                    rag_context=rag_context,
                )
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
            except Exception as e:
                error_msg = f"Sorry, I encountered an error: {e}"
                st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

        st.rerun()

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

    # Suggested questions
    if not st.session_state.chat_history:
        st.markdown("---")
        st.markdown("**💡 Suggested Questions:**")
        suggestions = [
            "What are the main trends in this data?",
            "Which categories have the highest performance?",
            "Are there any anomalies or outliers I should be aware of?",
            "What recommendations would you make based on this data?",
            "How does performance compare across different segments?",
        ]
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(f"💡 {suggestion}", key=f"suggestion_{i}", use_container_width=True):
                    st.session_state.chat_history.append({"role": "user", "content": suggestion})
                    with st.spinner("🤖 Thinking..."):
                        try:
                            rag_context = ""
                            if st.session_state.rag_engine and st.session_state.rag_engine.is_ready:
                                rag_context = st.session_state.rag_engine.get_context_for_query(suggestion)
                            answer = st.session_state.llm_engine.answer_question(
                                question=suggestion,
                                data_context=st.session_state.data_context,
                                rag_context=rag_context,
                            )
                            st.session_state.chat_history.append({"role": "assistant", "content": answer})
                        except Exception as e:
                            st.session_state.chat_history.append({"role": "assistant", "content": f"Error: {e}"})
                    st.rerun()


# ══════════════════════════════════════════════════════════════
# PAGE: Visualizations
# ══════════════════════════════════════════════════════════════

def render_visualizations():
    """Render the interactive visualizations page."""
    render_user_header()
    # Updated Header with Icon
    st.markdown('<div class="section-title"><div class="icon-circle"><i class="fa-solid fa-chart-pie"></i></div>Visualizations</div>', unsafe_allow_html=True)

    if st.session_state.df is None:
        st.info("📁 Please upload a tabular dataset (CSV, Excel, JSON) to create visualizations.")
        return

    df = st.session_state.df
    viz = st.session_state.visualizer
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    all_cols = df.columns.tolist()

    tab1, tab2, tab3 = st.tabs(["🤖 Auto-Generated", "🛠️ Custom Charts", "📋 AI Suggestions"])

    # ── Tab 1: Auto-Generated ───────────────
    with tab1:
        st.markdown("Charts automatically selected based on your data profile.")
        auto_figs = viz.auto_visualize(df)
        if auto_figs:
            for title, fig in auto_figs:
                st.markdown(f"**{title}**")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No visualizations could be auto-generated for this dataset.")

    # ── Tab 2: Custom Charts ────────────────
    with tab2:
        st.markdown("Build your own charts by selecting columns and chart type.")

        chart_type = st.selectbox(
            "Chart Type",
            ["Bar Chart", "Line Chart", "Scatter Plot", "Pie Chart", "Box Plot", "Histogram", "Heatmap"],
        )

        col1, col2, col3 = st.columns(3)

        if chart_type == "Bar Chart":
            with col1:
                x_col = st.selectbox("X-Axis (Category)", categorical_cols or all_cols, key="bar_x")
            with col2:
                y_col = st.selectbox("Y-Axis (Value)", numeric_cols, key="bar_y")
            with col3:
                chart_title = st.text_input("Chart Title", f"{y_col} by {x_col}", key="bar_title")
            if st.button("📊 Generate", key="gen_bar", type="primary"):
                fig = viz.create_bar_chart(df, x=x_col, y=y_col, title=chart_title)
                st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Line Chart":
            with col1:
                x_col = st.selectbox("X-Axis", all_cols, key="line_x")
            with col2:
                y_cols = st.multiselect("Y-Axis (Values)", numeric_cols, default=numeric_cols[:1], key="line_y")
            with col3:
                chart_title = st.text_input("Chart Title", "Trend Analysis", key="line_title")
            if st.button("📊 Generate", key="gen_line", type="primary") and y_cols:
                fig = viz.create_line_chart(df, x=x_col, y=y_cols, title=chart_title)
                st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Scatter Plot":
            with col1:
                x_col = st.selectbox("X-Axis", numeric_cols, key="scatter_x")
            with col2:
                y_col = st.selectbox("Y-Axis", numeric_cols, index=min(1, len(numeric_cols)-1), key="scatter_y")
            with col3:
                color_col = st.selectbox("Color By (optional)", [None] + categorical_cols, key="scatter_c")
            if st.button("📊 Generate", key="gen_scatter", type="primary"):
                fig = viz.create_scatter_plot(df, x=x_col, y=y_col, color=color_col)
                st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Pie Chart":
            with col1:
                pie_col = st.selectbox("Category Column", categorical_cols or all_cols, key="pie_col")
            with col2:
                chart_title = st.text_input("Chart Title", f"{pie_col} Distribution", key="pie_title")
            if st.button("📊 Generate", key="gen_pie", type="primary"):
                fig = viz.create_pie_chart(df, pie_col, title=chart_title)
                st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Box Plot":
            with col1:
                y_col = st.selectbox("Value Column", numeric_cols, key="box_y")
            with col2:
                x_col = st.selectbox("Group By (optional)", [None] + categorical_cols, key="box_x")
            if st.button("📊 Generate", key="gen_box", type="primary"):
                fig = viz.create_box_plot(df, y=y_col, x=x_col)
                st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Histogram":
            with col1:
                hist_col = st.selectbox("Column", numeric_cols, key="hist_col")
            if st.button("📊 Generate", key="gen_hist", type="primary"):
                fig = viz.create_distribution_chart(df, [hist_col])
                st.plotly_chart(fig, use_container_width=True)

        elif chart_type == "Heatmap":
            if len(numeric_cols) >= 2:
                selected = st.multiselect("Select Columns", numeric_cols, default=numeric_cols[:5], key="hm_cols")
                if st.button("📊 Generate", key="gen_hm", type="primary") and len(selected) >= 2:
                    fig = viz.create_correlation_heatmap(df, selected)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Need at least 2 numeric columns for a heatmap.")

    # ── Tab 3: AI Suggestions ───────────────
    with tab3:
        st.markdown("Let AI suggest the most insightful visualizations for your data.")
        if not st.session_state.api_key_set:
            st.warning("⚠️ Enter your OpenAI API key in the sidebar to get AI suggestions.")
        elif st.button("🤖 Get AI Visualization Suggestions", type="primary", use_container_width=True):
            with st.spinner("🤖 Analyzing data to suggest visualizations..."):
                try:
                    suggestions = st.session_state.llm_engine.suggest_visualizations(
                        st.session_state.data_context
                    )
                    st.markdown(suggestions)
                except Exception as e:
                    st.error(f"Error: {e}")


# ══════════════════════════════════════════════════════════════
# PAGE: Documents
# ══════════════════════════════════════════════════════════════

def render_documents():
    """Render the file manager page with Trash Can functionality."""
    render_user_header()
    # Updated Header with Icon
    st.markdown('<div class="section-title"><div class="icon-circle"><i class="fa-solid fa-folder-open"></i></div>My Files</div>', unsafe_allow_html=True)

    # 1. List Files
    upload_dir = Config.UPLOAD_DIR
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    files = os.listdir(upload_dir)
    
    if not files:
        st.info("No files uploaded yet. Go to the sidebar to upload a dataset or document.")
        return

    # Create a nice dataframe for the files
    file_list = []
    for f in files:
        file_path = os.path.join(upload_dir, f)
        stats = os.stat(file_path)
        file_list.append({
            "Select": False, # For deletion
            "File Name": f,
            "Size (KB)": round(stats.st_size / 1024, 2),
            "Type": f.split('.')[-1].upper() if '.' in f else "UNKNOWN"
        })
    
    files_df = pd.DataFrame(file_list)

    # Display editable dataframe for selection
    edited_df = st.data_editor(
        files_df,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "Delete?",
                help="Select to delete",
                default=False,
            ),
            "File Name": st.column_config.TextColumn(
                "File Name",
                width="large",
                disabled=True
            ),
            "Size (KB)": st.column_config.NumberColumn(
                "Size (KB)",
                format="%.2f",
                disabled=True
            ),
            "Type": st.column_config.TextColumn(
                "Type",
                width="small",
                disabled=True
            ),
        },
        disabled=["File Name", "Size (KB)", "Type"],
        hide_index=True,
        use_container_width=True,
        key="file_editor"
    )

    # Check for deletions
    selected_rows = edited_df[edited_df["Select"] == True]
    
    if not selected_rows.empty:
        st.warning(f"⚠️ You have selected {len(selected_rows)} file(s) for deletion.")
        if st.button("🗑️ Permanently Delete Selected Files", type="primary", use_container_width=True):
            for index, row in selected_rows.iterrows():
                file_to_delete = row["File Name"]
                path = os.path.join(upload_dir, file_to_delete)
                try:
                    if os.path.exists(path):
                        os.remove(path)
                        st.toast(f"Deleted: {file_to_delete}")
                        
                        # If the deleted file was the active one, clear session
                        if st.session_state.get('file_name') == file_to_delete:
                            st.session_state.df = None
                            st.session_state.doc_text = None
                            st.session_state.file_name = None
                            st.session_state.rag_engine = None
                            st.session_state.data_context = None
                except Exception as e:
                    st.error(f"Error deleting {file_to_delete}: {e}")
            
            st.rerun()

    st.divider()

    # 2. Show Current Loaded Data
    st.markdown("### ⚡ Currently Loaded in Retrieval Engine")
    
    if st.session_state.file_name:
        st.success(f"**active:** {st.session_state.file_name}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.session_state.df is not None:
                st.markdown("**Tabular Data**")
                st.dataframe(st.session_state.df.head(), height=150)
            elif st.session_state.doc_text:
                st.markdown("**Document Text**")
                st.text_area("Preview", st.session_state.doc_text[:500], height=150, disabled=True)
        
        with col2:
             if st.session_state.rag_engine and st.session_state.rag_engine.is_ready:
                 st.metric("Indexed Chunks", st.session_state.rag_engine.document_count)
                 st.info("This file is ready for Q&A.")
    else:
        st.warning("No file currently loaded in memory. Select or upload one.")


# ══════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════

page = st.session_state.current_page

if page == "Dashboard":
    render_dashboard()
elif page == "AI Analysis":
    render_analysis()
elif page == "Ask Questions":
    render_qa()
elif page == "Visualizations":
    render_visualizations()
elif page == "My Files":
    render_documents()
elif page == "User Profile":
    render_profile_page()
