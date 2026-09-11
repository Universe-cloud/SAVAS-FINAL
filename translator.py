
"""
SASVA Translation Service - REAL Auto Translation like Google Translate
- Only 3 languages: English, Hindi, Bengali
- Uses deep-translator (GoogleTranslator) for full UI auto-translation
- Manual high-quality translations for common keys + auto fallback for everything else
- Caches translations to avoid repeated API calls
"""

LANGUAGES = {
    "en": "English",
    "hi": "हिन्दी",
    "bn": "বাংলা"
}

# High-quality manual translations for critical govt portal keys
TRANSLATIONS = {
    "en": {
        "app_title": "SASVA - AI Driven Scheme Matching",
        "tagline": "For Marginalized Entrepreneurs",
        "home": "Home",
        "about": "About Us",
        "login": "Login / Sign Up",
        "logout": "Logout",
        "dashboard": "Dashboard",
        "scheme_matching": "Scheme Matching",
        "voice_intake": "Voice Intake",
        "doc_copilot": "Document Copilot",
        "notifications": "Notifications",
        "feedback": "Feedback",
        "admin_panel": "Admin Panel",
        "csc_panel": "CSC Operator Panel",
        "faq": "FAQs",
        "welcome": "Welcome to SASVA",
        "welcome_desc": "AI-driven scheme matching platform for SC/ST/OBC, Women, Street Vendors, SHG members and marginalized entrepreneurs. Voice-first, multilingual (English/Hindi/Bangla), with real OTP authentication.",
        "enter_phone_email": "Enter Phone Number or Email ID",
        "send_otp": "Send OTP",
        "verify_otp": "Verify OTP",
        "otp_sent": "OTP sent to",
        "role": "Select Role",
        "admin": "Admin",
        "csc_operator": "CSC Operator",
        "user": "User",
        "login_with_google": "Continue with Google",
        "govt_portal_auth": "Login / Sign Up",
        "phone_email_placeholder": "e.g. 9876543210 or name@example.com",
        "otp_placeholder": "Enter 6-digit OTP",
        "scheme_finder": "Find Best Government Schemes",
        "business_type": "Business Type",
        "caste_category": "Category",
        "gender": "Gender",
        "income": "Annual Income",
        "age": "Age",
        "state": "State",
        "description": "Briefly describe your business",
        "find_schemes": "Find Matching Schemes",
        "matched_schemes": "Top Matched Schemes for You",
        "eligibility": "Eligibility",
        "benefits": "Benefits",
        "documents": "Documents Required",
        "apply": "Apply Now",
        "why_matched": "Why this scheme matched you",
        "voice_assistant": "Voice Assistant - Speak in English/Hindi/Bangla",
        "start_speaking": "Start Speaking",
        "stop_speaking": "Stop",
        "speak_result": "You said",
        "tts": "Listen",
        "footer": "SASVA - Government Scheme Matching Portal",
    },
    "hi": {
        "app_title": "SASVA - एआई संचालित योजना मिलान",
        "tagline": "हाशिए पर रहने वाले उद्यमियों के लिए",
        "home": "होम",
        "about": "हमारे बारे में",
        "login": "लॉगिन / साइन अप",
        "logout": "लॉगआउट",
        "dashboard": "डैशबोर्ड",
        "scheme_matching": "योजना मिलान",
        "voice_intake": "वॉयस इनपुट",
        "doc_copilot": "दस्तावेज़ सहायक",
        "notifications": "सूचनाएं",
        "feedback": "प्रतिक्रिया",
        "admin_panel": "एडमिन पैनल",
        "csc_panel": "सीएससी ऑपरेटर पैनल",
        "faq": "सामान्य प्रश्न",
        "welcome": "SASVA में आपका स्वागत है",
        "enter_phone_email": "फोन नंबर या ईमेल आईडी दर्ज करें",
        "send_otp": "ओटीपी भेजें",
        "verify_otp": "ओटीपी सत्यापित करें",
        "role": "भूमिका चुनें",
        "admin": "एडमिन",
        "csc_operator": "सीएससी ऑपरेटर",
        "user": "उपयोगकर्ता",
        "login_with_google": "Google के साथ जारी रखें",
        "govt_portal_auth": "लॉगिन / साइन अप",
    },
    "bn": {
        "app_title": "SASVA - AI চালিত প্রকল্প ম্যাচিং",
        "tagline": "প্রান্তিক উদ্যোক্তাদের জন্য",
        "home": "হোম",
        "about": "আমাদের সম্পর্কে",
        "login": "লগইন / সাইন আপ",
        "logout": "লগআউট",
        "dashboard": "ড্যাশবোর্ড",
        "scheme_matching": "প্রকল্প ম্যাচিং",
        "voice_intake": "ভয়েস ইনপুট",
        "doc_copilot": "ডকুমেন্ট সহকারী",
        "notifications": "বিজ্ঞপ্তি",
        "feedback": "মতামত",
        "admin_panel": "অ্যাডমিন প্যানেল",
        "csc_panel": "CSC অপারেটর প্যানেল",
        "faq": "প্রশ্নোত্তর",
        "welcome": "SASVA তে আপনাকে স্বাগতম",
        "enter_phone_email": "ফোন নম্বর বা ইমেল আইডি লিখুন",
        "send_otp": "OTP পাঠান",
        "verify_otp": "OTP যাচাই করুন",
        "role": "ভূমিকা নির্বাচন করুন",
        "admin": "অ্যাডমিন",
        "csc_operator": "CSC অপারেটর",
        "user": "ব্যবহারকারী",
        "login_with_google": "Google দিয়ে চালিয়ে যান",
        "govt_portal_auth": "লগইন / সাইন আপ",
    }
}

_translation_cache = {}

def translate_text(text, target_lang):
    """Real auto-translation like Google Translate - translates any English text to Hindi/Bangla"""
    if not text or not isinstance(text, str):
        return text
    text = text.strip()
    if not text:
        return text
    if target_lang == "en":
        return text
    
    cache_key = f"{target_lang}::{text}"
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]
    
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source='en', target=target_lang).translate(text)
        if translated and translated.strip() and translated.strip().lower() != text.lower():
            _translation_cache[cache_key] = translated
            return translated
    except Exception as e:
        pass
    
    try:
        from deep_translator import MyMemoryTranslator
        tgt = 'hi-IN' if target_lang=='hi' else 'bn-BD'
        translated = MyMemoryTranslator(source='en-US', target=tgt).translate(text)
        if translated and translated.strip():
            _translation_cache[cache_key] = translated
            return translated
    except:
        pass
    
    _translation_cache[cache_key] = text
    return text

def t(key, lang="en"):
    """Main translation function - manual first, then auto-translate English fallback"""
    if lang not in LANGUAGES:
        lang = "en"
    if lang in TRANSLATIONS and key in TRANSLATIONS[lang]:
        return TRANSLATIONS[lang][key]
    en_text = TRANSLATIONS.get("en", {}).get(key, key)
    if lang == "en":
        return en_text
    return translate_text(en_text, lang)

def auto_translate(text, lang="en"):
    """Translate any dynamic English text to Hindi/Bangla - like Google Website Translate"""
    if lang == "en":
        return text
    return translate_text(text, lang)

def get_languages():
    return LANGUAGES

def translate_scheme_content(scheme, lang):
    """Auto-translate scheme name, description, benefits, documents"""
    if lang == "en":
        return scheme
    translated = scheme.copy()
    translated['name'] = translate_text(scheme.get('name',''), lang)
    translated['description'] = translate_text(scheme.get('description',''), lang)
    translated['benefits'] = translate_text(scheme.get('benefits',''), lang)
    translated['ministry'] = translate_text(scheme.get('ministry',''), lang)
    docs = scheme.get('documents', [])
    translated['documents'] = [translate_text(d, lang) for d in docs]
    return translated
