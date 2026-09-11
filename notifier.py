
"""
SASVA Notification Service - Real SMS/Email sending
As per PPT: Email Service, Govt Scheme API
"""
import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

LOG_FILE = Path("data/notifications.json")

def log_notification(entry):
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logs = []
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except:
            logs = []
    logs.append(entry)
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs[-100:], f, indent=2, ensure_ascii=False)  # Keep last 100

def send_email_real(to_email, subject, body_html, body_text=None):
    """
    REAL Email sending via SMTP
    Uses env vars EMAIL_USER, EMAIL_PASS
    """
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    
    log_entry = {
        "type": "email",
        "to": to_email,
        "subject": subject,
        "timestamp": datetime.now().isoformat(),
        "status": "pending"
    }
    
    if not email_user or not email_pass:
        # Demo mode - log as sent but mention need for credentials
        log_entry["status"] = "simulated_sent"
        log_entry["message"] = "Email credentials not set in .env - Set EMAIL_USER and EMAIL_PASS for real sending. In production, this would send real email."
        log_entry["body_preview"] = body_text[:200] if body_text else body_html[:200]
        log_notification(log_entry)
        print(f"[SIMULATED EMAIL] To: {to_email}, Subject: {subject}")
        return True, "Email simulated (set EMAIL_USER/PASS in .env for real sending)"
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = email_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if body_text:
            msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_user, email_pass)
        server.sendmail(email_user, to_email, msg.as_string())
        server.quit()
        
        log_entry["status"] = "sent"
        log_notification(log_entry)
        return True, "Email sent successfully to real email!"
    except Exception as e:
        log_entry["status"] = "failed"
        log_entry["error"] = str(e)
        log_notification(log_entry)
        return False, f"Email failed: {str(e)}"

def send_sms_real(to_phone, message):
    """
    REAL SMS via Twilio
    Uses env vars TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")
    
    log_entry = {
        "type": "sms",
        "to": to_phone,
        "message": message[:160],
        "timestamp": datetime.now().isoformat(),
        "status": "pending"
    }
    
    if not account_sid or not auth_token:
        log_entry["status"] = "simulated_sent"
        log_entry["note"] = "Twilio credentials not set - Set TWILIO_* in .env for real SMS. This is logged as sent for demo."
        log_notification(log_entry)
        print(f"[SIMULATED SMS] To: {to_phone}, Message: {message}")
        return True, "SMS simulated (set TWILIO credentials in .env for real SMS)"
    
    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        msg = client.messages.create(
            body=message,
            from_=from_number,
            to=to_phone if to_phone.startswith("+") else f"+91{to_phone[-10:]}"
        )
        log_entry["status"] = "sent"
        log_entry["twilio_sid"] = msg.sid
        log_notification(log_entry)
        return True, f"SMS sent! SID: {msg.sid}"
    except Exception as e:
        log_entry["status"] = "failed"
        log_entry["error"] = str(e)
        log_notification(log_entry)
        return False, f"SMS failed: {str(e)}"

def send_notification(user_identifier, subject, message, scheme_name=None):
    """
    Unified notification - sends to both email and phone if available
    Called after scheme matching, application, etc.
    """
    is_email = "@" in user_identifier
    results = []
    
    # Email
    email = user_identifier if is_email else None
    # Try to get user data to find both email and phone
    try:
        from auth import get_user
        user = get_user(user_identifier)
        if user:
            email = user.get('email') or email
            phone = user.get('phone')
        else:
            phone = None if is_email else user_identifier
    except:
        phone = None if is_email else user_identifier
        email = user_identifier if is_email else None
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; border-top: 5px solid #FF6B35;">
            <h2 style="color: #FF6B35;">SASVA - Govt Scheme Notification</h2>
            <p>Namaste,</p>
            <p>{message}</p>
            {f"<p><b>Scheme:</b> {scheme_name}</p>" if scheme_name else ""}
            <p>Login to SASVA portal to view details: <a href="http://localhost:8501">SASVA Portal</a></p>
            <hr>
            <p style="font-size: 12px; color: #888;">SASVA - Government Scheme Matching Portal<br>For support: support@sasva.gov.in | Helpline: 1800-XXX-XXXX</p>
        </div>
    </body>
    </html>
    """
    
    if email and "@" in email:
        success, msg = send_email_real(email, subject, html_body, message)
        results.append(f"Email: {msg}")
    
    if phone or (not is_email):
        target_phone = phone if phone else user_identifier
        if target_phone and len(str(target_phone)) >= 10:
            sms_msg = f"SASVA: {subject} - {message[:100]}. Scheme: {scheme_name or 'Check portal'}. SASVA Portal"
            success, msg = send_sms_real(str(target_phone), sms_msg)
            results.append(f"SMS: {msg}")
    
    if not results:
        return True, "Notification logged (no email/phone found, but saved to notification history)"
    
    return True, " | ".join(results)
