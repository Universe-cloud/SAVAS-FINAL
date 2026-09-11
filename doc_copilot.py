
"""
SASVA Document Copilot - OCR + AI Checklist + PDF Generator
As per PPT: Documentation Failure -> Document Copilot
Tech: OCR (Image/PDF to Text), FPDF Generator
"""
import json
from pathlib import Path
from datetime import datetime

try:
    from fpdf import FPDF
    FPDF_AVAILABLE = True
except:
    FPDF_AVAILABLE = False

try:
    import PyPDF2
    PYPDF_AVAILABLE = True
except:
    PYPDF_AVAILABLE = False

class DocumentCopilot:
    def __init__(self):
        self.required_docs_map = {
            "Financial Support": ["Aadhaar", "PAN", "Bank Statement", "Business Proof", "Income Certificate"],
            "Employment": ["Aadhaar", "Education Certificate", "Caste Certificate", "Project Report"],
            "State Support": ["Aadhaar", "Residence Proof", "Caste Certificate", "Income Certificate", "Trade License"]
        }
    
    def extract_text_from_pdf(self, pdf_file):
        """OCR - PDF to Text"""
        if not PYPDF_AVAILABLE:
            return "PyPDF2 not available - install requirements.txt"
        try:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text[:5000]  # Limit
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"
    
    def generate_checklist(self, matched_schemes, user_profile):
        """AI Checklist generator"""
        all_docs = set()
        for item in matched_schemes:
            scheme = item['scheme'] if isinstance(item, dict) and 'scheme' in item else item
            docs = scheme.get('documents', [])
            all_docs.update(docs)
        
        checklist = []
        for doc in sorted(all_docs):
            # AI logic: check if user likely has it
            status = "Required"
            tip = ""
            if doc.lower() == "aadhaar":
                tip = "Mandatory for all schemes. Ensure mobile linked."
            elif "caste" in doc.lower():
                if user_profile.get('caste') in ['SC', 'ST', 'OBC']:
                    tip = f"Required for {user_profile.get('caste')} category benefits"
                else:
                    tip = "If applicable for special category benefits"
            elif "income" in doc.lower():
                tip = f"Your income ₹{user_profile.get('income',0):,} - get certificate from Tehsil"
            
            checklist.append({
                "document": doc,
                "status": status,
                "tip": tip,
                "verified": False
            })
        
        return checklist
    
    def generate_pdf_checklist(self, user_profile, matched_schemes, checklist, output_path="data/SASVA_Checklist.pdf"):
        """PDF Generator using FPDF2 - As per Tech Stack"""
        if not FPDF_AVAILABLE:
            return False, "FPDF2 not installed. Run pip install fpdf2"
        
        try:
            pdf = FPDF()
            pdf.add_page()
            
            # Header
            pdf.set_font("Arial", "B", 16)
            pdf.set_text_color(255, 107, 53)
            pdf.cell(0, 10, "SASVA - Document Checklist & Scheme Report", ln=True, align='C')
            
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(0,0,0)
            pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')} | SASVA Portal", ln=True, align='C')
            pdf.ln(5)
            
            # User Profile
            pdf.set_font("Arial", "B", 12)
            pdf.set_fill_color(240, 242, 246)
            pdf.cell(0, 8, " Entrepreneur Profile", ln=True, fill=True)
            pdf.set_font("Arial", "", 10)
            profile_text = f"Name: {user_profile.get('name','Entrepreneur')} | Business: {user_profile.get('business_type','')} | Category: {user_profile.get('caste','')} | State: {user_profile.get('state','')}"
            pdf.multi_cell(0, 6, profile_text)
            pdf.ln(3)
            
            # Matched Schemes
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, f" Matched Schemes ({len(matched_schemes)} found)", ln=True, fill=True)
            pdf.set_font("Arial", "", 9)
            for idx, item in enumerate(matched_schemes[:5], 1):
                scheme = item['scheme'] if isinstance(item, dict) and 'scheme' in item else item
                score = item.get('eligibility_percent', 0) if isinstance(item, dict) else 0
                pdf.multi_cell(0, 5, f"{idx}. {scheme.get('name','')} - {score}% Match | {scheme.get('loan_amount','')} | {scheme.get('ministry','')}")
                pdf.ln(1)
            pdf.ln(3)
            
            # Checklist
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 8, " Document Checklist (AI Generated)", ln=True, fill=True)
            pdf.set_font("Arial", "", 10)
            for item in checklist:
                pdf.cell(10, 6, "[ ]")
                pdf.cell(50, 6, item['document'])
                pdf.cell(0, 6, f"- {item['tip'][:60]}", ln=True)
            
            pdf.ln(5)
            pdf.set_font("Arial", "I", 8)
            pdf.multi_cell(0, 4, "Note: This checklist is AI-generated based on your profile and matched schemes. Verify with official scheme portals. For CSC assistance, contact nearest CSC center. SASVA - SASVA - Government Scheme Facilitation Portal.")
            
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            pdf.output(output_path)
            return True, output_path
        except Exception as e:
            return False, f"PDF generation failed: {str(e)}"
