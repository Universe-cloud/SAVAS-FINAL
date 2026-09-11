# SASVA - Production Portal (Clean Version)

## Fixed Issues - Phase 1,2,3

### Phase 1 - Login:
- Removed PS ID, Team ID, Theme, SIH 2026 from header
- Clean header with Emblem of India image
- Only "Login / Sign Up" heading
- Removed blue info box and right side features list
- Added User role along with CSC Operator and Admin
- Real OTP sending via SMTP/Twilio (if .env configured), no demo OTP displayed
- Google login working via Gmail input (OAuth ready with GOOGLE_CLIENT_ID)
- Removed Demo Mode text and OTP session detail box

### Phase 2 - All Pages:
- Home: Clean portal description, features, policy, contact, support, quick FAQs - removed challenges table, system flow, tech stack, grey team text
- Scheme Matching: View All Schemes, Find Matching, Direct Search, Compare with bar graph, removed grey team details
- Voice Intake: Clean voice assistant, removed technical implementation box
- Document Copilot: Fixed PDF generation (fpdf2), removed feature list and grey text
- Notifications: Removed (Fixed) and previous bug line, removed setup code display, real sending via .env
- Feedback: Removed "as per ppt" line
- About Us: Removed whole option
- Admin Panel: Removed "not fake UI", changed to tally table format with bar chart, removed grey team text
- CSC Panel: Removed "same login system" texts, blue box, grey text - clean assist flow
- FAQ: Added new FAQ page with 12 questions

### How to Setup Real OTP:

1. Copy .env.example to .env
2. For Email OTP:
   - Go to myaccount.google.com -> Security -> 2FA -> App Passwords -> Create app password for Mail
   - Put Gmail and app password in .env as EMAIL_USER and EMAIL_PASS
3. For SMS OTP:
   - Create account at twilio.com, get Account SID, Auth Token, and phone number
   - Put in .env
4. For Google Login:
   - Go to console.cloud.google.com -> Create OAuth 2.0 Client ID
   - Add http://localhost:8501 as redirect URI
   - Put client ID/secret in .env

Without .env, system works in test mode: OTP is logged to terminal and notification history, but not displayed in UI for security. For testing, check data/notifications.json or terminal logs.

### Run:
```
pip install -r requirements_simple.txt
streamlit run app.py
```
Open http://localhost:8501

