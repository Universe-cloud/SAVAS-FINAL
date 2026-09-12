import streamlit as st
import os
import json
import time
import pandas as pd
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from translator import LANGUAGES, TRANSLATIONS, t, get_languages, auto_translate, translate_text, translate_scheme_content
from auth import register_or_login_user, get_user, is_valid_email, is_valid_phone
from engine import SASVAEngine
from notifier import send_notification, send_email_real, send_sms_real
from voice_module import get_voice_assistant_html
from doc_copilot import DocumentCopilot
from feedback import save_feedback, get_feedback_stats, get_success_journey

st.set_page_config(
    page_title="SASVA - Govt Scheme Matching Portal",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
   .main-header {
        background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
        padding: 12px 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
   .govt-badge {
        background: #000080;
        color: white;
        padding: 5px 12px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
        display: inline-block;
    }
   .scheme-card {
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 16px;
        margin: 10px 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #FF6B35;
    }
   .score-high { background: #d4edda; color: #155724; padding: 4px 10px; border-radius: 20px; font-weight: bold; }
   .score-medium { background: #fff3cd; color: #856404; padding: 4px 10px; border-radius: 20px; font-weight: bold; }
   .stButton>button {
        background: #FF6B35;
        color: white;
        border-radius: 25px;
        border: none;
        padding: 8px 20px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'language' not in st.session_state:
    st.session_state.language = 'en'
if 'current_role' not in st.session_state:
    st.session_state.current_role = "user"

@st.cache_resource
def load_engine():
    return SASVAEngine()

engine = load_engine()
doc_copilot = DocumentCopilot()

def tr(text):
    try:
        lang_code = st.session_state.language
    except:
        lang_code = 'en'
    if lang_code == 'en':
        return text
    return auto_translate(text, lang_code)

def language_selector():
    col1, col2 = st.columns([3,1])
    with col2:
        lang = st.selectbox(
            "🌐 Language / भाषा / ভাষা",
            options=list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x],
            index=list(LANGUAGES.keys()).index(st.session_state.language),
            key="lang_select"
        )
        if lang!= st.session_state.language:
            st.session_state.language = lang
            st.rerun()
    return st.session_state.language

lang = language_selector()

st.markdown(f"""
<div class="main-header">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
        <div style="display:flex; align-items:center;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/5/55/Emblem_of_India.svg" height="48" style="background:white; border-radius:4px; padding:3px; margin-right:12px;">
            <div>
                <span class="govt-badge">🇮🇳 GOVT OF INDIA</span>
                <span style="font-size:21px; font-weight:bold; margin-left:10px;">SASVA - AI Driven Scheme Matching</span>
            </div>
        </div>
        <div style="text-align:right; font-size:12px; line-height:1.6;">
            <span>🔒 Direct Secure Login</span><br>
            <span>📞 CSC Support • 🌐 EN / HI / BN</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

def show_auth_page():
    st.markdown(f"### 🔐 Login / Sign Up - No OTP")
    left, center, right = st.columns([1,2,1])
    with center:
        role = st.radio(
            "Select Role",
            options=["user", "csc_operator", "admin"],
            format_func=lambda x: "👤 User" if x=="user" else "👨‍💼 CSC Operator" if x=="csc_operator" else "👑 Admin",
            horizontal=False
        )
        st.session_state.current_role = role

        identifier = st.text_input(
            "Enter Phone Number or Email ID",
            placeholder="e.g. 9876543210 or name@example.com",
            key="identifier_input"
        )

        # DIRECT LOGIN - NO OTP
        if st.button("🚀 Login Directly", type="primary", use_container_width=True):
            if not identifier:
                st.error("Please enter phone number or email")
            elif not (is_valid_email(identifier) or is_valid_phone(identifier)):
                st.error("Please enter valid 10-digit mobile or valid email")
            else:
                user = register_or_login_user(identifier, st.session_state.current_role)
                st.session_state.authenticated = True
                st.session_state.user = user
                st.success(f"Welcome {identifier}! Login successful.")
                time.sleep(0.5)
                st.rerun()

        st.markdown("---")
        st.info("Demo Mode: OTP removed for fast access. Just enter email/phone and Login.")

# AUTH CHECK
if not st.session_state.authenticated:
    show_auth_page()
    st.stop()
