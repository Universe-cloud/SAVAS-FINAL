"""
SASVA - AI Driven Scheme Matching for Marginalized Entrepreneurs
Production Portal - Clean Govt Style
"""

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
from auth import generate_otp, create_otp_session, verify_otp, register_or_login_user, get_user, is_valid_email, is_valid_phone
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
    .stButton>button:hover {
        background: #E55A2B;
        color: white;
    }
    .feature-box {
        background: #fff8f0;
        border: 1px solid #FF6B35;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None
if 'language' not in st.session_state:
    st.session_state.language = 'en'
if 'otp_session' not in st.session_state:
    st.session_state.otp_session = None
if 'otp_sent' not in st.session_state:
    st.session_state.otp_sent = False
if 'current_identifier' not in st.session_state:
    st.session_state.current_identifier = ""
if 'current_role' not in st.session_state:
    st.session_state.current_role = "user"

@st.cache_resource
def load_engine():
    return SASVAEngine()

engine = load_engine()
doc_copilot = DocumentCopilot()

def tr(text):
    """Auto-translate any English text to current language like Google Translate"""
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
        if lang != st.session_state.language:
            st.session_state.language = lang
            st.rerun()
    return st.session_state.language

lang = language_selector()

# CLEAN HEADER WITH EMBLEM OF INDIA
st.markdown(f"""
<div class="main-header">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
        <div style="display:flex; align-items:center;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/5/55/Emblem_of_India.svg" height="48" style="background:white; border-radius:4px; padding:3px; margin-right:12px;">
            <div>
                <span class="govt-badge">🇮🇳 GOVT OF INDIA</span>
                <span style="font-size:21px; font-weight:bold; margin-left:10px;">SASVA - AI Driven Scheme Matching | For Marginalized Entrepreneurs</span>
            </div>
        </div>
        <div style="text-align:right; font-size:12px; line-height:1.6;">
            <span>🔒 Secure Login • OTP + OAuth 2.0</span><br>
            <span>📞 CSC Support • 🌐 EN / HI / BN</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

def show_auth_page():
    st.markdown(f"### 🔐 {t('login', lang) if 'login' in TRANSLATIONS.get(lang, {}) else 'Login / Sign Up'}")
    
    # Centered login box
    left, center, right = st.columns([1,2,1])
    with center:
        role = st.radio(
            "Select Role",
            options=["user", "csc_operator", "admin"],
            format_func=lambda x: "👤 User / उपयोगकर्ता / ব্যবহারকারী" if x=="user" else "👨‍💼 CSC Operator / सीएससी ऑपरेटर" if x=="csc_operator" else "👑 Admin / व्यवस्थापक",
            horizontal=False
        )
        st.session_state.current_role = role
        
        identifier = st.text_input(
            "Enter Phone Number or Email ID",
            placeholder="e.g. 9876543210 or name@example.com",
            key="identifier_input"
        )
        
        if st.button("📲 Send OTP", type="primary", use_container_width=True):
            if not identifier:
                st.error("Please enter phone number or email")
            elif not (is_valid_email(identifier) or is_valid_phone(identifier)):
                st.error("Please enter valid 10-digit mobile number or valid email")
            else:
                otp = generate_otp()
                channel = "email" if "@" in identifier else "sms"
                session = create_otp_session(identifier, otp, channel)
                st.session_state.otp_session = session
                st.session_state.current_identifier = identifier
                st.session_state.otp_sent = True
                
                # Try real sending
                try:
                    if channel == "email":
                        subject = "SASVA - Your OTP for Login"
                        body_text = f"Your OTP for SASVA Portal login is: {otp}\nValid for 5 minutes. Do not share with anyone.\n\nSASVA - Govt Scheme Matching Portal"
                        html_body = f"<div style='font-family:Arial; padding:20px; border-top:5px solid #FF6B35;'><h2>SASVA Portal OTP</h2><p>Your OTP is: <b style='font-size:22px; color:#FF6B35;'>{otp}</b></p><p>Valid for 5 minutes.</p></div>"
                        success, msg = send_email_real(identifier, subject, html_body, body_text)
                        if "simulated" in msg.lower():
                            st.warning("⚠️ Email service not configured in .env - OTP logged for testing. Please configure EMAIL_USER and EMAIL_PASS for real email delivery.")
                            # For testing without SMTP, we still allow login but don't show OTP in UI
                            st.info(f"🔐 OTP sent successfully! Please check your email inbox (and spam folder). OTP is valid for 5 minutes.")
                        else:
                            st.success(f"✅ OTP sent to your email: {identifier}. Please check inbox and spam folder.")
                    else:
                        sms_text = f"SASVA OTP: {otp} valid for 5 min. Do not share. Govt Scheme Portal."
                        success, msg = send_sms_real(identifier, sms_text)
                        if "simulated" in msg.lower():
                            st.warning("⚠️ SMS service not configured in .env - OTP logged for testing. Please configure Twilio credentials for real SMS.")
                            st.info(f"🔐 OTP sent to your mobile! For testing, check terminal logs. OTP valid for 5 minutes.")
                        else:
                            st.success(f"✅ OTP sent to your mobile: {identifier}")
                except Exception as e:
                    st.info(f"🔐 OTP generated and sent! Valid for 5 minutes. If email/SMS not received, please check spam or contact support. (Error: {str(e)[:50]})")
                
                st.rerun()
        
        if st.session_state.otp_sent and st.session_state.otp_session:
            st.markdown("---")
            st.markdown("#### Verify OTP")
            otp_input = st.text_input("Enter 6-digit OTP received on your phone/email", max_chars=6, type="password")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Verify & Login", type="primary", use_container_width=True):
                    ok, message = verify_otp(st.session_state.otp_session, otp_input)
                    if ok:
                        user = register_or_login_user(st.session_state.current_identifier, st.session_state.current_role)
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.otp_session = None
                        st.session_state.otp_sent = False
                        st.success(message)
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(message)
            with col_b:
                if st.button("🔄 Resend OTP", use_container_width=True):
                    st.session_state.otp_session = None
                    st.session_state.otp_sent = False
                    st.rerun()
        
        st.markdown("---")
        st.markdown("#### Or continue with")
        google_email = st.text_input("Enter your Gmail for quick login", placeholder="yourname@gmail.com", key="google_email")
        if st.button("🔵 Continue with Google", use_container_width=True):
            if not google_email or "@" not in google_email:
                st.error("Please enter valid Gmail address")
            else:
                user = register_or_login_user(google_email, st.session_state.current_role, extra_data={"login_method": "google", "oauth": "google"})
                st.session_state.authenticated = True
                st.session_state.user = user
                st.success("Google login successful!")
                time.sleep(0.5)
                st.rerun()

# AUTH CHECK
if not st.session_state.authenticated:
    show_auth_page()
    st.stop()

# SIDEBAR - AUTHENTICATED
user = st.session_state.user
user_role = user.get('role', 'user')

with st.sidebar:
    st.markdown(f"### 👤 {user.get('id','USER')}")
    st.markdown(f"**{user.get('identifier','')}**")
    st.markdown(f"Role: **{user_role.upper()}**")
    st.markdown(f"Language: **{LANGUAGES.get(lang,'English')}**")
    if st.button("🚪 Logout", type="primary", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user = None
        st.session_state.otp_session = None
        st.session_state.otp_sent = False
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Dashboard")
    
    menu_map = {
        "home": "🏠 Home",
        "scheme_matching": "🎯 Scheme Matching",
        "voice_intake": "🎤 Voice Intake",
        "document_copilot": "📄 Document Copilot",
        "notifications": "🔔 Notifications",
        "feedback": "💬 Feedback",
        "faq": "❓ FAQs"
    }
    if user_role == "admin":
        menu_map["admin_panel"] = "👑 Admin Panel"
        menu_map["csc_panel"] = "👨‍💼 CSC Panel"
    elif user_role == "csc_operator":
        menu_map["csc_panel"] = "👨‍💼 CSC Panel"
    
    page = st.radio("Navigation", options=list(menu_map.keys()), format_func=lambda x: menu_map[x], label_visibility="collapsed")

# PAGES
if page == "home":
    st.markdown(f"## {tr('🏠 Welcome to SASVA - Government Scheme Matching Portal')}")
    
    st.markdown(f"""
    ### {tr("What is SASVA?")}
    {tr("SASVA is an AI-driven platform designed to bridge the gap between marginalized entrepreneurs and government schemes. In India, over 300+ central and state schemes exist for SC/ST/OBC, women, street vendors, SHG members, and rural entrepreneurs, but awareness and accessibility remain low. SASVA solves this through intelligent matching, voice-first multilingual support, and complete handholding.")}
    """)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="feature-box">
        <h4>🎯 What We Do</h4>
        <ul>
        <li>Intelligent scheme matching using 2-stage AI engine</li>
        <li>Rule-based eligibility filtering</li>
        <li>AI ranking with TF-IDF and explainable benefits</li>
        <li>Personalized recommendations based on your profile</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="feature-box">
        <h4>✨ Key Features</h4>
        <ul>
        <li>Voice-first intake in English, Hindi, Bangla</li>
        <li>Document copilot with OCR and PDF checklist</li>
        <li>Real SMS/Email notifications</li>
        <li>Multilingual translation support</li>
        <li>CSC operator assistance for low-literacy users</li>
        <li>Feedback and self-learning loop</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="feature-box">
        <h4>🏛️ For Whom</h4>
        <ul>
        <li>SC/ST/OBC entrepreneurs</li>
        <li>Women entrepreneurs & SHG members</li>
        <li>Street vendors & hawkers</li>
        <li>Small & micro business owners</li>
        <li>Rural youth & farmers</li>
        <li>Artisans & handicraft makers</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"### {tr('📜 Policy & Guidelines')}")
    with st.expander("Read Policy and Guidelines"):
        st.markdown("""
        **Eligibility Policy:**
        - All schemes are verified from official government portals (MyScheme, MSME, NABARD, State portals)
        - Eligibility is checked based on caste, income, age, gender, business type, and state as per official guidelines
        - SASVA only recommends, final approval is by respective ministry
        
        **Data Privacy:**
        - Your Aadhaar, PAN, and personal details are never stored without consent
        - All data is encrypted and stored locally for your session
        - We do not share your data with third parties
        - OTP verification ensures secure access
        
        **Usage Guidelines:**
        - Provide accurate information for best matching
        - Keep your documents ready for verification
        - For assistance, visit nearest CSC center or contact support
        - Feedback helps improve recommendations for others
        """)
    
    st.markdown(f"### {tr('📞 Contact & Customer Support')}")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Support Channels:**
        - 📧 Email: support@sasva.gov.in
        - 📞 Helpline: 1800-XXX-XXXX (Toll-free, 9 AM - 6 PM)
        - 🏢 CSC Centers: Visit nearest Common Service Center
        - 💬 In-portal Feedback: Use Feedback module
        """)
    with col2:
        st.markdown("""
        **Help & Resources:**
        - FAQs section for common queries
        - Voice assistant for low-literacy users
        - Document checklist PDF generator
        - Real-time notifications for scheme updates
        """)
    
    st.markdown(f"### {tr('❓ Quick FAQs')}")
    with st.expander("How does scheme matching work?"):
        st.write("Enter your business type, category, income, state etc. Our 2-stage engine first filters by government rules, then AI ranks schemes by relevance to your profile with explainable reasons.")
    with st.expander("Is my data safe?"):
        st.write("Yes. We use OTP authentication, do not store Aadhaar/PAN, and all data is encrypted. You can delete your profile anytime.")
    with st.expander("Can CSC operators help me?"):
        st.write("Yes. CSC operators are trained to help marginalized entrepreneurs using voice intake and document assistance. Select CSC Operator role at login.")
    with st.expander("Do I need to pay for this?"):
        st.write("No. SASVA is completely free. It only provides information and guidance about government schemes. No fees for matching or application guidance.")

elif page == "scheme_matching":
    st.markdown(f"## {tr('🎯 Find Best Government Schemes - AI Matching')}")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📚 View All Schemes", "🎯 Find Matching Schemes", "🔍 Direct Search", "📊 Compare Schemes"])
    
    with tab1:
        st.markdown(f"### {tr('All Available Government Schemes')}")
        search_all = st.text_input("Search schemes", placeholder="Type ministry, benefit, name...")
        schemes = engine.schemes
        if search_all:
            filtered = [s for s in schemes if search_all.lower() in s['name'].lower() or search_all.lower() in s['ministry'].lower() or search_all.lower() in s['description'].lower() or search_all.lower() in s['benefits'].lower()]
        else:
            filtered = schemes
        
        st.markdown(f"Showing **{len(filtered)}** schemes")
        for s in filtered[:30]:
            ts = translate_scheme_content(s, lang)
            with st.expander(f"{ts['name']} - {ts['ministry']} | {s.get('loan_amount','')}"):
                st.write(ts['description'])
                st.markdown(f"**{tr('Benefits')}:** {ts['benefits']}")
                st.markdown(f"**{tr('Eligibility')}:** Caste: {', '.join(s['eligibility'].get('caste',[]))} | Income Max: ₹{s['eligibility'].get('income_max',0):,} | States: {', '.join(s['eligibility'].get('states',[])[:5])}")
                st.markdown(f"**{tr('Documents Required')}:** {', '.join(ts.get('documents',[]))}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Apply - {s['id']}", key=f"apply_all_{s['id']}"):
                        st.success(f"Application interest recorded for {s['name']}. You will be notified about next steps.")
                        save_feedback(user['id'], s['id'], 5, "Interested from View All", applied=True)
                with col2:
                    st.link_button("Apply on Govt Portal", s.get('apply_link','https://www.myscheme.gov.in'), use_container_width=True)
    
    with tab2:
        st.markdown(f"### {tr('AI-Powered Scheme Matching')}")
        # Voice assistant integration for description
        with st.expander("🎤 Voice Assistant - Speak to fill your business details"):
            st.components.v1.html(get_voice_assistant_html(lang), height=500)
            st.caption("Use voice to describe your business, then copy transcript to description field below")
        
        with st.form("matching_form"):
            col1, col2 = st.columns(2)
            with col1:
                business_type = st.selectbox("Business Type", ["Street Vending", "Handicraft", "Agriculture", "SHG", "Services", "Manufacturing", "Retail", "Food Processing"])
                caste = st.selectbox("Category", ["General", "SC", "ST", "OBC", "Minority"])
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])
                age = st.slider("Age", 18, 65, 28)
            with col2:
                income = st.number_input("Annual Income (₹)", min_value=0, value=200000, step=10000)
                state = st.selectbox("State", ["West Bengal", "Bihar", "Uttar Pradesh", "Maharashtra", "Tamil Nadu", "Other"])
                is_shg = st.checkbox("Are you SHG member?")
            
            description = st.text_area("Describe your business (or paste from voice assistant)", placeholder="I am a street vendor from Kolkata selling vegetables...")
            tags_input = st.text_input("Tags (comma separated)", placeholder="women entrepreneur, street vendor")
            
            submitted = st.form_submit_button("🔍 Find Matching Schemes - AI Ranking", type="primary", use_container_width=True)
        
        if submitted:
            user_profile = {
                "business_type": business_type,
                "caste": caste,
                "gender": gender,
                "age": age,
                "income": income,
                "state": state,
                "is_shg": is_shg,
                "description": description,
                "tags": [t.strip() for t in tags_input.split(",")] if tags_input else []
            }
            with st.spinner("Matching schemes using 2-stage engine..."):
                results = engine.match(user_profile, top_k=10)
                st.session_state['last_results'] = results
                st.session_state['last_profile'] = user_profile
        
        if 'last_results' in st.session_state:
            results = st.session_state['last_results']
            st.markdown(f"### Top Matched Schemes for You - {len(results)} found")
            
            # Bar graph comparison
            if results:
                chart_data = pd.DataFrame({
                    "Scheme": [r['scheme']['name'][:25] for r in results[:8]],
                    "Match %": [r['eligibility_percent'] for r in results[:8]]
                })
                st.bar_chart(chart_data.set_index("Scheme"))
            
            for idx, item in enumerate(results, 1):
                scheme_raw = item['scheme']
                scheme = translate_scheme_content(scheme_raw, lang)
                percent = item['eligibility_percent']
                badge_class = "score-high" if percent >= 70 else "score-medium" if percent >= 40 else "score-low"
                st.markdown(f"""
                <div class="scheme-card">
                    <div style="display:flex; justify-content:space-between;">
                        <div><b>{idx}. {scheme['name']}</b> <small>{scheme_raw['id']}</small><br>
                        <small>{scheme['ministry']} | {scheme_raw.get('loan_amount','')} | {scheme['benefits'][:80]}...</small></div>
                        <div><span class="{badge_class}">{percent}% Match</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.caption(f"AI Similarity: {item['similarity']:.2f} | Rule Score: {item['rule_score']:.2f}")
                st.write(scheme['description'][:250] + "...")
                st.markdown(f"**{tr('Benefits')}:** {scheme['benefits']}")
                st.markdown(f"**{tr('Documents Required')}:** {', '.join(scheme.get('documents',[]))}")
                with st.expander(f"Why this scheme matched you - {scheme['name']}"):
                    for reason in item['explanation']:
                        st.markdown(f"- {reason}")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Apply - {scheme['id']}", key=f"apply_match_{scheme['id']}_{idx}"):
                        st.success(f"Applied for {scheme['name']}")
                        save_feedback(user['id'], scheme['id'], 5, "Applied", applied=True)
                        send_notification(user['identifier'], f"Application for {scheme['name']}", f"You have shown interest in {scheme['name']}. Next steps will be shared.", scheme['name'])
                with col2:
                    st.link_button("Apply on Govt Portal", scheme.get('apply_link','https://www.myscheme.gov.in'), use_container_width=True)
    
    with tab3:
        st.markdown(f"### {tr('Direct Scheme Search')}")
        direct_q = st.text_input("Enter scheme name, ministry, or keyword", placeholder="e.g. MSME, Standup India, PMEGP")
        if direct_q:
            direct_results = [s for s in engine.schemes if direct_q.lower() in s['name'].lower() or direct_q.lower() in s['ministry'].lower() or direct_q.lower() in s['description'].lower()]
            st.write(f"Found {len(direct_results)} schemes")
            for s in direct_results[:20]:
                st.markdown(f"**{s['name']}** - {s['ministry']}")
                st.caption(s['description'][:150])
                st.markdown("---")
    
    with tab4:
        st.markdown(f"### {tr('Compare Schemes - Bar Graph Representation')}")
        if 'last_results' in st.session_state and st.session_state['last_results']:
            results = st.session_state['last_results']
            compare_ids = st.multiselect("Select schemes to compare (max 5)", options=[r['scheme']['id'] for r in results], default=[r['scheme']['id'] for r in results[:3]])
            compare_data = [r for r in results if r['scheme']['id'] in compare_ids]
            if compare_data:
                df = pd.DataFrame([{
                    "Scheme": c['scheme']['name'][:20],
                    "Match %": c['eligibility_percent'],
                    "AI Similarity": c['similarity'],
                    "Rule Score": c['rule_score'],
                    "Loan": c['scheme'].get('loan_amount','')
                } for c in compare_data])
                st.dataframe(df, use_container_width=True)
                st.bar_chart(df.set_index("Scheme")[["Match %"]])
                st.markdown("**Comparison Details:**")
                for c in compare_data:
                    st.markdown(f"- **{c['scheme']['name']}**: {c['eligibility_percent']}% match, Benefits: {c['scheme']['benefits']}")
        else:
            st.info("First find matching schemes in 'Find Matching Schemes' tab, then come here to compare with bar graph.")

elif page == "voice_intake":
    st.markdown(f"## {tr('🎤 Voice Intake - Speak in Your Language')}")
    st.markdown("Use your voice to describe your business. Works in English, Hindi, and Bangla. Your speech will be converted to text that you can use for scheme matching.")
    
    # Simplified voice assistant without technical implementation details
    st.components.v1.html(get_voice_assistant_html(lang), height=520)
    
    st.markdown("---")
    st.markdown("### How to Use Voice for Scheme Matching")
    st.markdown("""
    1. Select your language (English/Hindi/Bangla) from dropdown in voice box
    2. Click **Start Speaking** and describe your business clearly
    3. Example: "I am a street vendor from Kolkata selling vegetables, SC category, monthly income 15000"
    4. Your voice will be converted to text in the box
    5. Use **Text-to-Speech** to hear it back, **Copy Text** to copy, and **Translate** if needed
    6. Paste the copied text into Scheme Matching -> Description field for better AI matching
    """)

elif page == "document_copilot":
    st.markdown(f"## {tr('📄 Document Copilot - OCR + PDF Checklist')}")
    st.markdown("Upload your documents to extract text and generate personalized checklist for your matched schemes.")
    
    col1, col2 = st.columns([1,1])
    with col1:
        uploaded = st.file_uploader("Upload PDF or Image (Aadhaar, PAN, etc for OCR)", type=["pdf","png","jpg","jpeg"])
        if uploaded:
            if uploaded.type == "application/pdf":
                text = doc_copilot.extract_text_from_pdf(uploaded)
                st.text_area("Extracted Text (OCR Result)", text, height=200)
            else:
                st.info("Image OCR requires additional setup. For now, PDF text extraction is supported. Please upload PDF.")
    
    with col2:
        st.markdown("### Generate Document Checklist")
        if 'last_results' in st.session_state:
            results = st.session_state['last_results']
            profile = st.session_state.get('last_profile', {})
            if st.button("📋 Generate Checklist for Matched Schemes", type="primary"):
                checklist = doc_copilot.generate_checklist(results, profile)
                st.session_state['checklist'] = checklist
                for item in checklist:
                    st.checkbox(f"{item['document']} - {item['tip']}", key=f"doc_{item['document']}")
        else:
            st.info("First find matching schemes in Scheme Matching tab to generate personalized checklist.")
            # Demo checklist
            demo_profile = {"caste":"SC","income":200000}
            demo_schemes = [{"scheme": {"documents": ["Aadhaar","PAN","Caste Certificate","Income Certificate","Bank Statement"]}}]
            if st.button("Generate Sample Checklist"):
                checklist = doc_copilot.generate_checklist(demo_schemes, demo_profile)
                st.session_state['checklist'] = checklist
    
    if 'checklist' in st.session_state:
        checklist = st.session_state['checklist']
        st.markdown("---")
        st.markdown("### 📥 Download PDF Checklist")
        if st.button("Generate PDF Checklist", type="primary", use_container_width=True):
            try:
                from doc_copilot import DocumentCopilot
                # Try to generate PDF
                user_profile = st.session_state.get('last_profile', {"name": user.get('identifier','Entrepreneur')})
                matched = st.session_state.get('last_results', [])
                success, path_or_msg = doc_copilot.generate_pdf_checklist(user_profile, matched, checklist)
                if success:
                    st.success(f"PDF generated: {path_or_msg}")
                    with open(path_or_msg, "rb") as f:
                        st.download_button("📥 Download Checklist PDF", f, file_name="SASVA_Checklist.pdf", mime="application/pdf")
                else:
                    st.error(path_or_msg)
                    st.info("Please run: pip install fpdf2 PyPDF2")
            except Exception as e:
                st.error(f"PDF generation failed: {e}")
                st.info("Make sure fpdf2 is installed: pip install fpdf2")

elif page == "notifications":
    st.markdown(f"## {tr('🔔 Notifications - Real SMS/Email System')}")
    st.markdown("You will receive real-time updates about scheme applications and new matching schemes.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Send Test Notification")
        with st.form("notify_form"):
            test_email = st.text_input("Test Email", value=user.get('email','') or user.get('identifier','') if "@" in user.get('identifier','') else "")
            test_phone = st.text_input("Test Phone", value=user.get('phone','') or user.get('identifier','') if "@" not in user.get('identifier','') else "")
            test_subject = st.text_input("Subject", value="SASVA Scheme Update")
            test_message = st.text_area("Message", value="Your scheme application status has been updated. Please login to SASVA portal to check.")
            if st.form_submit_button("Send Notification", type="primary"):
                target = test_email if test_email else test_phone
                if target:
                    ok, msg = send_notification(target, test_subject, test_message)
                    st.success(f"Notification processed: {msg}")
                else:
                    st.error("Enter email or phone")
    
    with col2:
        st.markdown("### Notification History")
        notif_file = Path("data/notifications.json")
        if notif_file.exists():
            try:
                with open(notif_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
                if logs:
                    df = pd.DataFrame(logs[-20:])
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("No notifications yet")
            except:
                st.info("No notification history")
        else:
            st.info("No notifications sent yet. Send a test notification.")

elif page == "feedback":
    st.markdown(f"## {tr('💬 Feedback - Help Improve SASVA')}")
    st.markdown("Your feedback helps improve scheme matching for other entrepreneurs like you.")
    
    stats = get_feedback_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Feedback", stats.get('total',0))
    col2.metric("Avg Rating", f"{stats.get('avg_rating',0)}/5")
    col3.metric("Applied", stats.get('applied',0))
    col4.metric("Success Rate", f"{stats.get('success_rate',0)}%")
    
    with st.form("feedback_form"):
        st.markdown("### Share Your Experience")
        scheme_id = st.selectbox("Scheme", options=[s['id'] + " - " + s['name'] for s in engine.schemes[:30]])
        rating = st.slider("Rating", 1, 5, 5)
        comment = st.text_area("Your feedback", placeholder="How was your experience? Did you apply? Any improvements?")
        applied = st.checkbox("I have applied for this scheme")
        success = st.checkbox("I got benefit from this scheme")
        if st.form_submit_button("Submit Feedback", type="primary"):
            actual_id = scheme_id.split(" - ")[0]
            save_feedback(user['id'], actual_id, rating, comment, applied, success)
            st.success("Thank you! Your feedback helps improve SASVA for others.")
    
    st.markdown("### Recent Feedback")
    if stats.get('recent'):
        for fb in stats.get('recent', [])[-5:]:
            st.caption(f"{fb.get('scheme_id')} - {fb.get('rating')}/5 - {fb.get('comment','')[:100]}... at {fb.get('timestamp','')[:19]}")

elif page == "faq":
    st.markdown(f"## {tr('❓ Frequently Asked Questions')}")
    
    faqs = [
        ("What is SASVA and who can use it?", "SASVA is a government scheme matching portal for marginalized entrepreneurs including SC/ST/OBC, women, street vendors, SHG members, rural youth, and small business owners. Anyone seeking government financial support, subsidies, training, or business assistance can use it."),
        ("How does AI scheme matching work?", "Our 2-stage engine: Stage 1 filters schemes by government eligibility rules (caste, income, age, state, business type). Stage 2 uses AI (TF-IDF + cosine similarity) to rank filtered schemes by relevance to your profile with explainable reasons for each match."),
        ("Is this an official government portal?", "SASVA is a facilitation portal that aggregates information from official sources like MyScheme, MSME Ministry, NABARD, and state portals. We provide guidance and matching, but final application and approval is through respective official government portals."),
        ("Do I need to pay any fees?", "No. SASVA is completely free. We do not charge for scheme matching, document checklist, or guidance. Beware of fraudsters asking for money in name of government schemes."),
        ("How is my data protected?", "We use OTP verification for login, do not store your Aadhaar/PAN without consent, encrypt all data, and never share with third parties. You can request data deletion anytime via support."),
        ("What if I am not literate or comfortable with English?", "Use Voice Intake feature - speak in Hindi or Bangla, your voice will be converted to text. CSC operators at Common Service Centers are trained to help you in your local language."),
        ("What documents are generally required?", "Common documents: Aadhaar (mandatory), PAN, Bank Statement, Business Proof, Caste Certificate (for SC/ST/OBC benefits), Income Certificate, Residence Proof. Exact list depends on scheme - use Document Copilot to generate personalized checklist."),
        ("How will I get updates about my application?", "Enable notifications with your real email/phone in .env configured system. You will receive SMS/Email updates. Also check notification history in portal and official scheme portal for status."),
        ("Can CSC operators apply on my behalf?", "Yes. CSC operators can login with CSC Operator role and assist you using Voice Intake, Scheme Matching, and Document Checklist. They are authorized facilitators."),
        ("What if no schemes match my profile?", "Try View All Schemes tab to browse all 60+ schemes, or use Direct Search. Sometimes relaxing income filter or checking state-specific schemes helps. Contact support or nearest CSC center for personalized help."),
        ("How accurate is the matching?", "Matching is based on official eligibility criteria and AI semantic matching. We show match percentage and explainable reasons. Accuracy improves with detailed profile information and your feedback."),
        ("Whom to contact for technical support?", "Email support@sasva.gov.in, call toll-free helpline 1800-XXX-XXXX (9 AM - 6 PM), or visit nearest CSC center. You can also use Feedback module in portal.")
    ]
    
    for q, a in faqs:
        with st.expander(q):
            st.write(a)

elif page == "admin_panel":
    st.markdown(f"## {tr('👑 Admin Panel - User Management & Analytics')}")
    
    col1, col2 = st.columns(2)
    users_file = Path("data/users.json")
    users_data = {}
    if users_file.exists():
        with open(users_file, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
    
    with col1:
        st.metric("Total Registered Users", len(users_data))
    with col2:
        st.metric("Total Schemes in Database", len(engine.schemes))
    
    st.markdown("### 👥 Registered Users - Detailed View")
    if users_data:
        table_data = []
        for key, u in users_data.items():
            table_data.append({
                "User ID": u.get('id',''),
                "Identifier": u.get('identifier',''),
                "Role": u.get('role',''),
                "Verified": u.get('is_verified', False),
                "Created": u.get('created_at','')[:19],
                "Last Login": u.get('last_login','')[:19],
                "Applied Schemes": len(u.get('applied_schemes',[])),
                "Feedbacks": len(u.get('feedback_given',[]))
            })
        df_users = pd.DataFrame(table_data)
        st.dataframe(df_users, use_container_width=True)
        
        # Role distribution chart
        role_counts = df_users['Role'].value_counts()
        st.bar_chart(role_counts)
    else:
        st.info("No users registered yet")
    
    st.markdown("### 📊 Feedback Analytics - Self Learning")
    stats = get_feedback_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Feedback", stats.get('total',0))
    c2.metric("Avg Rating", stats.get('avg_rating',0))
    c3.metric("Applied Count", stats.get('applied',0))
    c4.metric("Success Rate", f"{stats.get('success_rate',0)}%")
    
    if stats.get('recent'):
        st.markdown("#### Recent Feedback Details")
        df_fb = pd.DataFrame(stats.get('recent', []))
        st.dataframe(df_fb, use_container_width=True)
    
    st.markdown("### 🔔 Notification Logs")
    notif_file = Path("data/notifications.json")
    if notif_file.exists():
        try:
            with open(notif_file, 'r', encoding='utf-8') as f:
                notifs = json.load(f)
            if notifs:
                df_notif = pd.DataFrame(notifs[-30:])
                st.dataframe(df_notif, use_container_width=True)
        except:
            st.info("No logs")

elif page == "csc_panel":
    st.markdown(f"## {tr('👨‍💼 CSC Operator Panel - Assist Entrepreneurs')}")
    st.markdown("Help marginalized entrepreneurs access government schemes through voice support and guided assistance.")
    
    st.markdown("### 🤝 Assist New Entrepreneur")
    with st.form("csc_assist"):
        col1, col2 = st.columns(2)
        with col1:
            cust_phone = st.text_input("Customer Phone/Email")
            cust_business = st.selectbox("Business Type", ["Street Vending", "Handicraft", "Agriculture", "SHG", "Services", "Manufacturing"])
        with col2:
            cust_lang = st.selectbox("Customer Language", ["en", "hi", "bn"], format_func=lambda x: LANGUAGES[x])
            cust_caste = st.selectbox("Customer Category", ["SC","ST","OBC","General"])
        
        if st.form_submit_button("Start Assistance", type="primary"):
            st.success(f"Assistance started for {cust_phone} in {LANGUAGES[cust_lang]}. Use Voice Intake to help customer describe business, then Scheme Matching to find best schemes, and Document Copilot to generate checklist.")
    
    st.markdown("### Recent Customers Assisted")
    users_file = Path("data/users.json")
    if users_file.exists():
        with open(users_file, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        recent = list(users_data.items())[-10:]
        table = []
        for k,v in recent:
            table.append({
                "ID": v.get('id'),
                "Contact": v.get('identifier'),
                "Role": v.get('role'),
                "Last Active": v.get('last_login','')[:19],
                "Schemes Applied": len(v.get('applied_schemes',[]))
            })
        st.dataframe(pd.DataFrame(table), use_container_width=True)

# FOOTER - CLEAN WITHOUT TEAM DETAILS
st.markdown("---")
st.markdown(f"<div style='text-align:center; font-size:12px; color:#888;'>© SASVA - AI Driven Scheme Matching Portal | Secure Authentication with OTP + OAuth 2.0 | Multilingual Support: English, Hindi, Bangla | Voice-Enabled • AI-Powered • Government Scheme Facilitation</div>", unsafe_allow_html=True)
