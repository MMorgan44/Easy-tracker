#!/usr/bin/env python3
"""
Easy Audit V.7.0 - Streamlit Web Application
Converted from Easy Audit V.6.2.1 tkinter application
Full-featured dental auditing software with Supabase cloud sync
"""

import streamlit as st
import pandas as pd
import json
import os
import re
import hashlib
import datetime
from datetime import datetime as dt, timedelta
from typing import List, Dict, Optional
import io
import base64

# Supabase imports
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    create_client = None

# Password hashing
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

# Document generation
try:
    from docx import Document
    from docx.shared import RGBColor, Pt
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import openpyxl
    XLSX_AVAILABLE = True
except ImportError:
    XLSX_AVAILABLE = False

# ==================== CONFIGURATION ====================
SUPABASE_URL = "https://yqekjzklcomwzxkdwkga.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlxZWtqemtsY29td3p4a2R3a2dhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjE5Njk5NSwiZXhwIjoyMDc3NzcyOTk1fQ.Z5wxHzCVcqzRmmytyj6uNjUQf42RWlVoaQyyr3N456g"

# Supabase table names
USERS_TABLE = "users"
RECORDS_TABLE = "audit_records"

# Theme definitions
THEMES = {
    "Default": {"primary": "#0078d7", "bg": "#f0f0f0", "text": "#000000"},
    "Dark": {"primary": "#007acc", "bg": "#2b2b2b", "text": "#ffffff"},
    "Blue": {"primary": "#2196f3", "bg": "#e3f2fd", "text": "#01579b"},
    "Light": {"primary": "#ff9800", "bg": "#ffffff", "text": "#212121"},
    "Nord": {"primary": "#88c0d0", "bg": "#2e3440", "text": "#eceff4"},
    "Solarized": {"primary": "#268bd2", "bg": "#fdf6e3", "text": "#657b83"},
    "Monokai": {"primary": "#f92672", "bg": "#272822", "text": "#f8f8f2"}
}

# Hospital branches and doctors mapping
BRANCH_DOCTORS = {
    "Andalusia Hospital - Maadi": ["Dr. Ahmed Hassan", "Dr. Sara Ahmed", "Dr. Mohamed Ali"],
    "Andalusia Hospital - October": ["Dr. Khaled Mahmoud", "Dr. Fatma Ibrahim"],
    "Andalusia Hospital - Smouha": ["Dr. Omar Youssef", "Dr. Laila Mohamed"],
    "Cleopatra Hospital": ["Dr. Amr Saeed", "Dr. Noha Mostafa"],
    "Saudi German Hospital": ["Dr. Tarek Abdel-Rahman", "Dr. Dina Hassan"],
    "Dar Al Fouad Hospital": ["Dr. Walid Ahmed", "Dr. Mona Kamel"],
    "As-Salam International Hospital": ["Dr. Yasser Ibrahim", "Dr. Heba Sayed"]
}

INSURANCE_COMPANIES = [
    "Allianz", "AXA", "Bupa", "Cigna", "MetLife", "MEDGULF", 
    "Gulf Insurance", "Tawuniya", "SAICO", "Malath", "Walaa",
    "Solidarity", "Mednet", "United Health", "Al Rajhi Takaful"
]

SERVICE_MONTH_FILTERS = [
    "January 2024", "February 2024", "March 2024", "April 2024",
    "May 2024", "June 2024", "July 2024", "August 2024",
    "September 2024", "October 2024", "November 2024", "December 2024",
    "January 2025", "February 2025", "March 2025", "April 2025",
    "May 2025", "June 2025", "July 2025", "August 2025",
    "September 2025", "October 2025", "November 2025", "December 2025"
]

# ==================== DENTAL CODES DATABASE ====================
DENTAL_CODES = {
    "011": {"description": "Comprehensive oral examination", "category": "diagnostic"},
    "012": {"description": "Periodic oral examination", "category": "diagnostic"},
    "013": {"description": "Oral examination - limited", "category": "diagnostic"},
    "014": {"description": "Consultation - specialist", "category": "diagnostic"},
    "015": {"description": "Consultation - special purpose", "category": "diagnostic"},
    "018": {"description": "Written report", "category": "diagnostic"},
    "019": {"description": "Letter of referral", "category": "diagnostic"},
    "022": {"description": "Intraoral periapical or bitewing radiograph - per exposure", "category": "diagnostic"},
    "025": {"description": "Panoramic radiograph", "category": "diagnostic"},
    "037": {"description": "Cephalometric radiograph", "category": "diagnostic"},
    "047": {"description": "Hand / Wrist radiograph", "category": "diagnostic"},
    "061": {"description": "Pulp testing - per visit", "category": "diagnostic"},
    "071": {"description": "Diagnostic model - per arch", "category": "diagnostic"},
    "072": {"description": "Photographic records", "category": "diagnostic"},
    "111": {"description": "Removal of plaque and/or stain - per visit", "category": "preventive"},
    "114": {"description": "Removal of calculus - per visit", "category": "preventive"},
    "115": {"description": "Removal of calculus - subsequent visit", "category": "preventive"},
    "118": {"description": "Fluoride treatment - per application", "category": "preventive"},
    "119": {"description": "Desensitising procedure - per visit", "category": "preventive"},
    "121": {"description": "Fissure and/or tooth surface sealing - per tooth", "category": "preventive"},
    "131": {"description": "Dietary advice", "category": "preventive"},
    "141": {"description": "Oral hygiene instruction", "category": "preventive"},
    "161": {"description": "Mouthguard", "category": "preventive"},
    "213": {"description": "Treatment of acute periodontal infection - per visit", "category": "periodontics"},
    "221": {"description": "Clinical periodontal analysis and recording", "category": "periodontics"},
    "222": {"description": "Periodontal debridement - per tooth", "category": "periodontics"},
    "223": {"description": "Root planing & subgingival curettage - per tooth", "category": "periodontics"},
    "232": {"description": "Gingivectomy - per tooth", "category": "periodontics"},
    "250": {"description": "Active non-surgical periodontal therapy - per tooth", "category": "periodontics"},
    "311": {"description": "Removal of a tooth or part(s) thereof", "category": "oral_surgery"},
    "314": {"description": "Sectional removal of a tooth", "category": "oral_surgery"},
    "322": {"description": "Surgical removal of a tooth or tooth fragment not requiring bone removal", "category": "oral_surgery"},
    "323": {"description": "Surgical removal of a tooth or tooth fragment requiring bone removal", "category": "oral_surgery"},
    "324": {"description": "Surgical removal of a tooth or tooth fragment requiring bone removal and tooth division", "category": "oral_surgery"},
    "386": {"description": "Splinting - direct, per tooth bonded", "category": "oral_surgery"},
    "391": {"description": "Surgical repositioning of teeth", "category": "oral_surgery"},
    "411": {"description": "Direct pulp capping", "category": "endodontics"},
    "414": {"description": "Pulpotomy", "category": "endodontics"},
    "415": {"description": "Complete chemo-mechanical preparation of root canal - one canal", "category": "endodontics"},
    "416": {"description": "Complete chemo-mechanical preparation of root canal - each additional canal", "category": "endodontics"},
    "417": {"description": "Root canal obturation - one canal", "category": "endodontics"},
    "418": {"description": "Root canal obturation - each additional canal", "category": "endodontics"},
    "419": {"description": "Extirpation of pulp or debridement of root canal(s) - emergency or palliative", "category": "endodontics"},
    "451": {"description": "Removal of root filling", "category": "endodontics"},
    "455": {"description": "Additional visit for irrigation and/or dressing of root canal system", "category": "endodontics"},
    "511": {"description": "Metallic restoration - one surface - direct", "category": "restorative"},
    "512": {"description": "Metallic restoration - two surfaces - direct", "category": "restorative"},
    "513": {"description": "Metallic restoration - three surfaces - direct", "category": "restorative"},
    "514": {"description": "Metallic restoration - four surfaces - direct", "category": "restorative"},
    "515": {"description": "Metallic restoration - five surfaces - direct", "category": "restorative"},
    "521": {"description": "Adhesive restoration - one surface - anterior tooth - direct", "category": "restorative"},
    "522": {"description": "Adhesive restoration - two surfaces - anterior tooth - direct", "category": "restorative"},
    "523": {"description": "Adhesive restoration - three surfaces - anterior tooth - direct", "category": "restorative"},
    "524": {"description": "Adhesive restoration - four surfaces - anterior tooth - direct", "category": "restorative"},
    "525": {"description": "Adhesive restoration - five surfaces - anterior tooth - direct", "category": "restorative"},
    "526": {"description": "Adhesive restoration - veneer - anterior tooth - direct", "category": "restorative"},
    "531": {"description": "Adhesive restoration - one surface - posterior tooth - direct", "category": "restorative"},
    "532": {"description": "Adhesive restoration - two surfaces - posterior tooth - direct", "category": "restorative"},
    "533": {"description": "Adhesive restoration - three surfaces - posterior tooth - direct", "category": "restorative"},
    "534": {"description": "Adhesive restoration - four surfaces - posterior tooth - direct", "category": "restorative"},
    "535": {"description": "Adhesive restoration - five surfaces - posterior tooth - direct", "category": "restorative"},
    "611": {"description": "Full crown - acrylic resin - indirect", "category": "prosthodontics"},
    "613": {"description": "Full crown - non-metallic - indirect", "category": "prosthodontics"},
    "615": {"description": "Full crown - veneered - indirect", "category": "prosthodontics"},
    "618": {"description": "Full crown - metallic - indirect", "category": "prosthodontics"},
    "625": {"description": "Core for crown including post - indirect", "category": "prosthodontics"},
    "627": {"description": "Preliminary restoration for crown - direct", "category": "prosthodontics"},
    "631": {"description": "Provisional crown - per tooth", "category": "prosthodontics"},
    "632": {"description": "Provisional bridge pontic - per pontic", "category": "prosthodontics"},
    "643": {"description": "Bridge pontic - indirect - per pontic", "category": "prosthodontics"},
    "651": {"description": "Recementing crown or veneer", "category": "prosthodontics"},
    "711": {"description": "Complete maxillary denture", "category": "dentures"},
    "712": {"description": "Complete mandibular denture", "category": "dentures"},
    "721": {"description": "Partial maxillary denture - resin base", "category": "dentures"},
    "722": {"description": "Partial mandibular denture - resin base", "category": "dentures"},
    "727": {"description": "Partial maxillary denture - cast metal framework", "category": "dentures"},
    "728": {"description": "Partial mandibular denture - cast metal framework", "category": "dentures"},
    "741": {"description": "Adjustment of a denture", "category": "dentures"},
    "821": {"description": "Active removable appliance therapy", "category": "orthodontics"},
    "823": {"description": "Functional orthopaedic appliance", "category": "orthodontics"},
    "825": {"description": "Sequential Plastic Aligners Per Arch", "category": "orthodontics"},
    "831": {"description": "Full Arch Banding per arch", "category": "orthodontics"},
    "881": {"description": "Complete course of orthodontic treatment", "category": "orthodontics"},
    "911": {"description": "Palliative care", "category": "general"},
    "941": {"description": "Local Anaesthesia", "category": "anaesthesia"},
    "DF019": {"description": "ROOT CANAL TREATMENT FOR MOLAR TOOTH", "category": "endodontics"},
    "DY004": {"description": "PANORAMIC RADIOGRAPH", "category": "diagnostic"},
    "DG004": {"description": "GUM TREATMENT (FULL MOUTH)", "category": "periodontics"},
    "DF016": {"description": "ROOT CANAL TREATMENT FOR PREMOLAR TOOTH", "category": "endodontics"},
    "DE001": {"description": "NORMAL EXTRACTION", "category": "oral_surgery"},
    "DE002": {"description": "COMPLICATED EXTRACTION", "category": "oral_surgery"},
    "DE003": {"description": "WISDOM TOOTH EXTRACTION", "category": "oral_surgery"},
    "DE004": {"description": "SURGICAL EXTRACTION", "category": "oral_surgery"},
    "DB001": {"description": "TEMPORARY CROWN", "category": "prosthodontics"},
    "DB006": {"description": "FULL CERAMIC CROWN (IMPRESS)", "category": "prosthodontics"},
    "DB027": {"description": "ZIRCON CROWN", "category": "prosthodontics"},
    "DB033N": {"description": "EMAX CROWN", "category": "prosthodontics"},
    "DB034N": {"description": "EMAX VENEER", "category": "prosthodontics"},
    "DB043N": {"description": "COMPOSITE FILLING 1 SURFACE", "category": "restorative"},
    "DB044N": {"description": "COMPOSITE FILLING 2 SURFACE", "category": "restorative"},
    "DB045N": {"description": "COMPOSITE FILLING 3 SURFACE", "category": "restorative"},
}

# ==================== SUPABASE CLIENT INITIALIZATION ====================
@st.cache_resource
def get_supabase_client():
    """Initialize and return Supabase client"""
    if not SUPABASE_AVAILABLE or not create_client:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        return None

# ==================== UTILITY FUNCTIONS ====================
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    if BCRYPT_AVAILABLE:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    if BCRYPT_AVAILABLE:
        try:
            return bcrypt.checkpw(password.encode(), hashed.encode())
        except:
            return hashlib.sha256(password.encode()).hexdigest() == hashed
    return hashlib.sha256(password.encode()).hexdigest() == hashed

def format_date(date_str):
    """Format date string to DD/MM/YYYY"""
    if not date_str or not isinstance(date_str, str):
        return ""
    date_str = date_str.strip()
    formats = ["%d/%m/%Y", "%Y-%m-%d", "%m/%d/%Y"]
    for fmt in formats:
        try:
            dt_obj = datetime.datetime.strptime(date_str, fmt)
            return dt_obj.strftime("%d/%m/%Y")
        except:
            continue
    return date_str

def generate_record_signature(record: dict) -> str:
    """Generate unique signature for a record"""
    mrn = str(record.get('MRN', '')).strip()
    service_date = str(record.get('Service Date', '')).strip()
    charged = str(record.get('Charged Services', '')).strip()
    approved = str(record.get('Approved Services', '')).strip()
    canonical = f"{mrn}|{service_date}|{charged}|{approved}"
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def parse_services(services_text: str) -> List[Dict]:
    """Parse services text into structured format"""
    if not services_text:
        return []
    services = []
    lines = services_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Parse format: "CODE: Description (Count: N) [Teeth: X,Y,Z]"
        code_match = re.match(r'^([A-Za-z0-9]+):\s*(.+?)(?:\s*\(Count:\s*(\d+)\))?(?:\s*\[Teeth:\s*(.+?)\])?$', line)
        if code_match:
            code = code_match.group(1).upper()
            desc = code_match.group(2).strip()
            count = int(code_match.group(3)) if code_match.group(3) else 1
            teeth = code_match.group(4) if code_match.group(4) else ""
            services.append({
                "code": code,
                "description": desc,
                "count": count,
                "teeth": teeth
            })
        else:
            # Try simpler format
            simple_match = re.match(r'^([A-Za-z0-9]+):\s*(.+)$', line)
            if simple_match:
                services.append({
                    "code": simple_match.group(1).upper(),
                    "description": simple_match.group(2).strip(),
                    "count": 1,
                    "teeth": ""
                })
    return services

def format_services_display(services_text: str) -> str:
    """Format services for display"""
    services = parse_services(services_text)
    if not services:
        return services_text
    formatted = []
    for s in services:
        line = f"**{s['code']}**: {s['description']} (Count: {s['count']})"
        if s['teeth']:
            line += f" [Teeth: {s['teeth']}]"
        formatted.append(line)
    return '\n'.join(formatted)

def get_auto_discrepancies(record: dict) -> List[str]:
    """Get auto-detected discrepancies for a record"""
    discrepancies = []
    if record.get("The services performed", "").strip().lower() == "no":
        discrepancies.append("⚠️ Services differ between Invoice and Attending's note!")
    if record.get("The services performed", "").strip().lower() == "no input":
        discrepancies.append("⚠️ No input in the attending's note")
    if record.get("Approved", "").strip().lower() == "no":
        discrepancies.append("⚠️ Services differ between Invoice and Approval!")
    service_date = record.get("Service Date", "").strip()
    invoice_date = record.get("Invoice Date", "").strip()
    if service_date and invoice_date and service_date != invoice_date:
        discrepancies.append("⚠️ Service date is different from Invoice date")
    return discrepancies

# ==================== DATABASE FUNCTIONS ====================
def load_users_from_supabase():
    """Load users from Supabase"""
    client = get_supabase_client()
    if not client:
        return get_default_users()
    try:
        response = client.table(USERS_TABLE).select("*").execute()
        if response.data:
            users = {}
            for user in response.data:
                users[user['username']] = user
            return {"users": users}
    except Exception as e:
        st.warning(f"Could not load users from cloud: {e}")
    return get_default_users()

def get_default_users():
    """Return default users dict"""
    return {
        "users": {
            "mmorgan": {
                "password_hash": hash_password("1234"),
                "first_name": "Mohamed",
                "last_name": "Morgan",
                "email": "mohamedmorgan@gmx.co.uk",
                "is_master": True,
                "setup_complete": True,
                "created_date": dt.now().isoformat(),
                "trial_end_date": None,
                "excel_export_name": "Mohamed S. Morgan"
            }
        }
    }

def save_user_to_supabase(username: str, user_data: dict):
    """Save user to Supabase"""
    client = get_supabase_client()
    if not client:
        return False
    try:
        user_data['username'] = username
        # Check if user exists
        existing = client.table(USERS_TABLE).select("*").eq("username", username).execute()
        if existing.data:
            client.table(USERS_TABLE).update(user_data).eq("username", username).execute()
        else:
            client.table(USERS_TABLE).insert(user_data).execute()
        return True
    except Exception as e:
        st.error(f"Failed to save user: {e}")
        return False

def load_records_from_supabase(username: str = None):
    """Load audit records from Supabase"""
    client = get_supabase_client()
    if not client:
        return []
    try:
        table_name = f"audit_records_{username}" if username else RECORDS_TABLE
        response = client.table(table_name).select("*").execute()
        if response.data:
            return response.data
    except Exception as e:
        # Try main table
        try:
            response = client.table(RECORDS_TABLE).select("*").execute()
            if response.data:
                return response.data
        except:
            pass
    return []

def save_record_to_supabase(record: dict, username: str = None):
    """Save a single record to Supabase"""
    client = get_supabase_client()
    if not client:
        return False
    try:
        table_name = f"audit_records_{username}" if username else RECORDS_TABLE
        # Remove local-only fields
        record_to_save = {k: v for k, v in record.items() if k not in ['idx', 'local_id', 'id']}
        
        # Check if record exists (by MRN and Service Date)
        mrn = record_to_save.get('MRN', '')
        service_date = record_to_save.get('Service Date', '')
        
        if mrn and service_date:
            existing = client.table(table_name).select("*").eq("MRN", mrn).eq("Service Date", service_date).execute()
            if existing.data:
                client.table(table_name).update(record_to_save).eq("MRN", mrn).eq("Service Date", service_date).execute()
                return True
        
        client.table(table_name).insert(record_to_save).execute()
        return True
    except Exception as e:
        st.error(f"Failed to save record: {e}")
        return False

def delete_record_from_supabase(mrn: str, service_date: str, username: str = None):
    """Delete a record from Supabase"""
    client = get_supabase_client()
    if not client:
        return False
    try:
        table_name = f"audit_records_{username}" if username else RECORDS_TABLE
        client.table(table_name).delete().eq("MRN", mrn).eq("Service Date", service_date).execute()
        return True
    except Exception as e:
        st.error(f"Failed to delete record: {e}")
        return False

# ==================== EXPORT FUNCTIONS ====================
def export_to_excel(records: List[Dict], export_name: str = "Easy Audit Export") -> bytes:
    """Export records to Excel format"""
    if not records:
        return None
    
    # Define columns for Excel export
    columns = [
        "Hospital", "Doctor", "Patient", "MRN", "Insurance",
        "Audit Date", "Service Date", "Invoice Date", "Approval Date",
        "Charged Services", "Approved Services", "Attending Note",
        "Discrepancy", "Discrepancy Details", "The services performed",
        "Approved", "Created By", "Created Date"
    ]
    
    rows = []
    for rec in records:
        row = {col: rec.get(col, "") for col in columns}
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Audit Records')
    output.seek(0)
    return output.getvalue()

def export_to_docx(records: List[Dict]) -> bytes:
    """Export records to Word document"""
    if not DOCX_AVAILABLE or not records:
        return None
    
    doc = Document()
    doc.add_heading('Easy Audit Records', 0)
    doc.add_paragraph(f'Generated on: {dt.now().strftime("%d/%m/%Y %H:%M")}')
    doc.add_paragraph(f'Total Records: {len(records)}')
    doc.add_paragraph('')
    
    for idx, rec in enumerate(records, 1):
        doc.add_heading(f'Record #{idx}', level=1)
        
        # Patient Information
        doc.add_heading('Patient Information', level=2)
        table = doc.add_table(rows=5, cols=2)
        table.style = 'Table Grid'
        
        fields = [
            ("Hospital", rec.get("Hospital", "")),
            ("Doctor", rec.get("Doctor", "")),
            ("Patient", rec.get("Patient", "")),
            ("MRN", rec.get("MRN", "")),
            ("Insurance", rec.get("Insurance", ""))
        ]
        
        for i, (label, value) in enumerate(fields):
            table.rows[i].cells[0].text = label
            table.rows[i].cells[1].text = str(value)
        
        doc.add_paragraph('')
        
        # Dates
        doc.add_heading('Dates', level=2)
        dates_para = doc.add_paragraph()
        dates_para.add_run(f"Audit Date: {rec.get('Audit Date', '')}\n")
        dates_para.add_run(f"Service Date: {rec.get('Service Date', '')}\n")
        dates_para.add_run(f"Invoice Date: {rec.get('Invoice Date', '')}\n")
        dates_para.add_run(f"Approval Date: {rec.get('Approval Date', '')}")
        
        # Services
        doc.add_heading('Services', level=2)
        charged_para = doc.add_paragraph()
        charged_para.add_run("Charged Services:\n").bold = True
        charged_para.add_run(rec.get("Charged Services", ""))
        
        approved_para = doc.add_paragraph()
        approved_para.add_run("Approved Services:\n").bold = True
        approved_para.add_run(rec.get("Approved Services", ""))
        
        # Discrepancy
        if rec.get("Discrepancy") == "Yes":
            disc_para = doc.add_paragraph()
            disc_para.add_run("Discrepancy Details:\n").bold = True
            run = disc_para.add_run(rec.get("Discrepancy Details", ""))
            run.font.color.rgb = RGBColor(255, 0, 0)
        
        doc.add_page_break()
    
    output = io.BytesIO()
    doc.save(output)
    output.seek(0)
    return output.getvalue()

# ==================== SESSION STATE INITIALIZATION ====================
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'authenticated': False,
        'current_user': None,
        'records': [],
        'selected_record_index': None,
        'theme': 'Default',
        'page': 'login',
        'editing_record': None,
        'search_results': [],
        'show_settings': False,
        'users_db': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ==================== AUTHENTICATION ====================
def login_page():
    """Render login page"""
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 16px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    .login-header {
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    }
    .login-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .login-header p {
        opacity: 0.9;
    }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; padding: 2rem 0;">
            <h1 style="color: #667eea; font-size: 3rem; margin-bottom: 0;">🦷 Easy Audit</h1>
            <p style="color: #666; font-size: 1.2rem;">Dental Auditing Software</p>
            <p style="color: #999;">Version 7.0 - Streamlit Edition</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")
            
            col_login, col_create = st.columns(2)
            with col_login:
                login_btn = st.form_submit_button("🚀 Login", use_container_width=True, type="primary")
            with col_create:
                create_btn = st.form_submit_button("➕ Create Account", use_container_width=True)
            
            if login_btn and username and password:
                authenticate_user(username, password)
            
            if create_btn:
                st.session_state.show_create_user = True
        
        if st.session_state.get('show_create_user', False):
            create_user_form()

def authenticate_user(username: str, password: str):
    """Authenticate user credentials"""
    users_db = load_users_from_supabase()
    
    if username in users_db.get('users', {}):
        user = users_db['users'][username]
        if verify_password(password, user.get('password_hash', '')):
            # Check trial expiration
            trial_end = user.get('trial_end_date')
            if trial_end and not user.get('is_master', False):
                try:
                    end_date = dt.fromisoformat(trial_end)
                    if dt.now() > end_date:
                        st.error("⚠️ Your trial has expired. Please contact support.")
                        return
                except:
                    pass
            
            st.session_state.authenticated = True
            st.session_state.current_user = {
                'username': username,
                'full_name': f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                'email': user.get('email', ''),
                'is_master': user.get('is_master', False),
                'excel_export_name': user.get('excel_export_name', username),
                'trial_end_date': user.get('trial_end_date')
            }
            st.session_state.users_db = users_db
            st.session_state.page = 'main'
            
            # Load records
            st.session_state.records = load_records_from_supabase(username)
            
            st.success(f"✅ Welcome back, {st.session_state.current_user['full_name']}!")
            st.rerun()
        else:
            st.error("❌ Invalid password")
    else:
        st.error("❌ Username not found")

def create_user_form():
    """Render create user form"""
    st.markdown("---")
    st.subheader("Create New Account")
    
    with st.form("create_user_form"):
        admin_pwd = st.text_input("🔐 Admin Password (required)", type="password")
        new_username = st.text_input("Username", placeholder="No spaces allowed")
        first_name = st.text_input("First Name")
        last_name = st.text_input("Last Name")
        email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        trial_days = st.selectbox("Trial Period", ["10 days", "15 days", "30 days", "Unlimited"])
        
        if st.form_submit_button("Create Account", type="primary"):
            # Verify admin password
            users_db = load_users_from_supabase()
            master_user = users_db.get('users', {}).get('mmorgan')
            
            if not master_user or not verify_password(admin_pwd, master_user.get('password_hash', '')):
                st.error("❌ Invalid admin password")
                return
            
            if ' ' in new_username:
                st.error("❌ Username cannot contain spaces")
                return
            
            if new_password != confirm_password:
                st.error("❌ Passwords do not match")
                return
            
            if len(new_password) < 4:
                st.error("❌ Password must be at least 4 characters")
                return
            
            if new_username in users_db.get('users', {}):
                st.error("❌ Username already exists")
                return
            
            # Calculate trial end date
            trial_end = None
            if trial_days != "Unlimited":
                days = int(trial_days.split()[0])
                trial_end = (dt.now() + timedelta(days=days)).isoformat()
            
            new_user = {
                'password_hash': hash_password(new_password),
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'is_master': False,
                'setup_complete': True,
                'created_date': dt.now().isoformat(),
                'trial_end_date': trial_end,
                'excel_export_name': f"{first_name} {last_name}".strip()
            }
            
            if save_user_to_supabase(new_username, new_user):
                st.success(f"✅ Account created for {new_username}")
                st.session_state.show_create_user = False
                st.rerun()

def logout():
    """Logout user"""
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.records = []
    st.session_state.page = 'login'
    st.rerun()

# ==================== MAIN APPLICATION ====================
def main_app():
    """Main application interface"""
    # Header
    render_header()
    
    # Navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Data Entry", 
        "💾 Saved Records", 
        "🔍 Search", 
        "📚 ADA Codes"
    ])
    
    with tab1:
        data_entry_tab()
    
    with tab2:
        saved_records_tab()
    
    with tab3:
        search_tab()
    
    with tab4:
        ada_codes_tab()

def render_header():
    """Render application header"""
    col1, col2, col3 = st.columns([2, 4, 2])
    
    with col1:
        user = st.session_state.current_user
        st.markdown(f"""
        <div style="padding: 0.5rem; background: linear-gradient(90deg, #667eea, #764ba2); 
                    border-radius: 8px; color: white;">
            <p style="margin: 0; font-weight: bold;">👋 Hello, {user['full_name']}</p>
            <p style="margin: 0; font-size: 0.8rem; opacity: 0.9;">
                {'👑 Master Admin' if user['is_master'] else '👤 User'}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="text-align: center;">
            <h2 style="margin: 0; color: #667eea;">🦷 Easy Audit</h2>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">Dental Auditing Software</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        col_settings, col_logout = st.columns(2)
        with col_settings:
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state.show_settings = True
        with col_logout:
            if st.button("🚪 Logout", use_container_width=True):
                logout()
    
    # Trial status
    user = st.session_state.current_user
    if user.get('trial_end_date'):
        try:
            end_date = dt.fromisoformat(user['trial_end_date'])
            days_remaining = (end_date - dt.now()).days
            if days_remaining > 0:
                st.warning(f"⏰ Trial: {days_remaining} days remaining")
            else:
                st.error("⚠️ Trial expired - please contact support")
        except:
            pass
    
    st.markdown("---")
    
    # Settings modal
    if st.session_state.get('show_settings', False):
        settings_dialog()

def settings_dialog():
    """Render settings dialog"""
    with st.expander("⚙️ Settings", expanded=True):
        st.subheader("User Settings")
        
        user = st.session_state.current_user
        
        col1, col2 = st.columns(2)
        with col1:
            new_first_name = st.text_input("First Name", value=user.get('full_name', '').split()[0] if user.get('full_name') else '')
            new_email = st.text_input("Email", value=user.get('email', ''))
        
        with col2:
            new_last_name = st.text_input("Last Name", value=user.get('full_name', '').split()[-1] if len(user.get('full_name', '').split()) > 1 else '')
            excel_name = st.text_input("Excel Export Name", value=user.get('excel_export_name', ''))
        
        st.markdown("---")
        st.subheader("Change Password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        st.markdown("---")
        st.subheader("Theme")
        theme = st.selectbox("Select Theme", list(THEMES.keys()), index=list(THEMES.keys()).index(st.session_state.theme))
        
        col_save, col_close = st.columns(2)
        with col_save:
            if st.button("💾 Save Settings", type="primary", use_container_width=True):
                if new_password and new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    # Update user data
                    users_db = st.session_state.users_db
                    username = st.session_state.current_user['username']
                    
                    if username in users_db.get('users', {}):
                        user_data = users_db['users'][username]
                        user_data['first_name'] = new_first_name
                        user_data['last_name'] = new_last_name
                        user_data['email'] = new_email
                        user_data['excel_export_name'] = excel_name
                        
                        if new_password:
                            user_data['password_hash'] = hash_password(new_password)
                        
                        save_user_to_supabase(username, user_data)
                        
                        st.session_state.current_user['full_name'] = f"{new_first_name} {new_last_name}"
                        st.session_state.current_user['email'] = new_email
                        st.session_state.current_user['excel_export_name'] = excel_name
                        st.session_state.theme = theme
                        
                        st.success("✅ Settings saved!")
                        st.session_state.show_settings = False
                        st.rerun()
        
        with col_close:
            if st.button("❌ Close", use_container_width=True):
                st.session_state.show_settings = False
                st.rerun()

# ==================== DATA ENTRY TAB ====================
def data_entry_tab():
    """Render data entry form"""
    st.subheader("📝 New Audit Record")
    
    # Patient Information
    with st.expander("👤 Patient Information", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            hospital = st.selectbox("🏥 Hospital Branch", [""] + list(BRANCH_DOCTORS.keys()), key="hospital_select")
            mrn = st.text_input("🔢 MRN (Medical Record Number)", key="mrn_input")
        
        with col2:
            # Filter doctors based on hospital
            doctors = BRANCH_DOCTORS.get(hospital, []) if hospital else []
            all_doctors = list(set([d for docs in BRANCH_DOCTORS.values() for d in docs]))
            doctor = st.selectbox("👨‍⚕️ Doctor", [""] + (doctors if doctors else all_doctors), key="doctor_select")
            patient = st.text_input("👤 Patient Name", key="patient_input")
        
        with col3:
            insurance = st.selectbox("🏢 Insurance Company", [""] + INSURANCE_COMPANIES, key="insurance_select")
    
    # Dates
    with st.expander("📅 Dates", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            audit_date = st.date_input("📅 Audit Date", value=datetime.date.today(), key="audit_date")
        with col2:
            service_date = st.date_input("📅 Service Date", value=datetime.date.today(), key="service_date")
        with col3:
            invoice_date = st.date_input("📅 Invoice Date", value=datetime.date.today(), key="invoice_date")
        with col4:
            approval_date = st.date_input("📅 Approval Date", value=datetime.date.today(), key="approval_date")
    
    # Services
    with st.expander("🦷 Services", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Charged Services (Invoice)**")
            charged_services = st.text_area(
                "Enter services (one per line)",
                height=150,
                key="charged_services",
                help="Format: CODE: Description (Count: N) [Teeth: X,Y,Z]"
            )
            
            # Quick add dental code
            st.markdown("**Quick Add Code:**")
            code_col1, code_col2, code_col3 = st.columns([2, 1, 1])
            with code_col1:
                selected_code = st.selectbox("Select Code", [""] + list(DENTAL_CODES.keys()), key="quick_code")
            with code_col2:
                code_count = st.number_input("Count", min_value=1, value=1, key="code_count")
            with code_col3:
                if st.button("➕ Add", key="add_charged"):
                    if selected_code:
                        desc = DENTAL_CODES.get(selected_code, {}).get('description', '')
                        new_line = f"{selected_code}: {desc} (Count: {code_count})"
                        current = st.session_state.get('charged_services', '')
                        st.session_state.charged_services = f"{current}\n{new_line}".strip()
                        st.rerun()
        
        with col2:
            st.markdown("**Approved Services**")
            approved_services = st.text_area(
                "Enter approved services",
                height=150,
                key="approved_services"
            )
            
            # Copy from charged
            if st.button("📋 Copy from Charged", key="copy_charged"):
                st.session_state.approved_services = st.session_state.get('charged_services', '')
                st.rerun()
    
    # Clinical Notes
    with st.expander("📝 Clinical Notes", expanded=True):
        attending_note = st.text_area("Attending Note", height=100, key="attending_note")
        
        col1, col2 = st.columns(2)
        with col1:
            service_performed = st.selectbox(
                "Services Performed as per Attending Note?",
                ["Yes", "No", "No Input"],
                key="service_performed"
            )
        with col2:
            approved = st.selectbox(
                "Approved as per Approval?",
                ["Yes", "No"],
                key="approved"
            )
    
    # Discrepancy
    with st.expander("⚠️ Discrepancy", expanded=True):
        col1, col2 = st.columns([1, 3])
        with col1:
            has_discrepancy = st.radio("Discrepancy?", ["No", "Yes"], key="has_discrepancy", horizontal=True)
        with col2:
            if has_discrepancy == "Yes":
                discrepancy_details = st.text_input("Discrepancy Details", key="discrepancy_details")
            else:
                discrepancy_details = ""
    
    # Action Buttons
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 Save Record", type="primary", use_container_width=True):
            save_current_record()
    
    with col2:
        if st.button("🔄 Reset Form", use_container_width=True):
            reset_form()
    
    with col3:
        if st.button("➡️ Next Day", use_container_width=True):
            # Increment all dates by one day
            st.session_state.audit_date = st.session_state.audit_date + timedelta(days=1)
            st.session_state.service_date = st.session_state.service_date + timedelta(days=1)
            st.session_state.invoice_date = st.session_state.invoice_date + timedelta(days=1)
            st.session_state.approval_date = st.session_state.approval_date + timedelta(days=1)
            st.rerun()
    
    with col4:
        st.metric("Total Records", len(st.session_state.records))

def save_current_record():
    """Save the current form as a record"""
    # Validation
    if not st.session_state.get('hospital_select'):
        st.error("❌ Hospital Branch is required")
        return
    if not st.session_state.get('doctor_select'):
        st.error("❌ Doctor is required")
        return
    if not st.session_state.get('mrn_input'):
        st.error("❌ MRN is required")
        return
    
    record = {
        "Hospital": st.session_state.hospital_select,
        "Doctor": st.session_state.doctor_select,
        "Patient": st.session_state.patient_input,
        "MRN": st.session_state.mrn_input,
        "Insurance": st.session_state.insurance_select,
        "Audit Date": st.session_state.audit_date.strftime("%d/%m/%Y"),
        "Service Date": st.session_state.service_date.strftime("%d/%m/%Y"),
        "Invoice Date": st.session_state.invoice_date.strftime("%d/%m/%Y"),
        "Approval Date": st.session_state.approval_date.strftime("%d/%m/%Y"),
        "Charged Services": st.session_state.charged_services,
        "Approved Services": st.session_state.approved_services,
        "Attending Note": st.session_state.attending_note,
        "The services performed": st.session_state.service_performed,
        "Approved": st.session_state.approved,
        "Discrepancy": st.session_state.has_discrepancy,
        "Discrepancy Details": st.session_state.get('discrepancy_details', ''),
        "Created By": st.session_state.current_user['excel_export_name'],
        "Created Date": dt.now().strftime("%d/%m/%Y %H:%M")
    }
    
    # Check if editing
    if st.session_state.editing_record is not None:
        st.session_state.records[st.session_state.editing_record] = record
        st.session_state.editing_record = None
        st.success("✅ Record updated successfully!")
    else:
        st.session_state.records.append(record)
        st.success("✅ Record saved successfully!")
    
    # Sync to cloud
    username = st.session_state.current_user['username']
    if save_record_to_supabase(record, username):
        st.info("☁️ Synced to cloud")
    
    reset_form()
    st.rerun()

def reset_form():
    """Reset form fields"""
    keys_to_reset = [
        'hospital_select', 'doctor_select', 'patient_input', 'mrn_input',
        'insurance_select', 'charged_services', 'approved_services',
        'attending_note', 'discrepancy_details'
    ]
    for key in keys_to_reset:
        if key in st.session_state:
            if key.endswith('_select'):
                st.session_state[key] = ""
            else:
                st.session_state[key] = ""

# ==================== SAVED RECORDS TAB ====================
def saved_records_tab():
    """Render saved records table"""
    st.subheader("💾 Saved Records")
    
    records = st.session_state.records
    
    if not records:
        st.info("📭 No records saved yet. Start by adding a new audit record.")
        return
    
    # Filters
    with st.expander("🔍 Filters", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            filter_hospital = st.selectbox(
                "Hospital",
                ["All"] + list(set(r.get('Hospital', '') for r in records if r.get('Hospital'))),
                key="filter_hospital"
            )
        with col2:
            filter_doctor = st.selectbox(
                "Doctor",
                ["All"] + list(set(r.get('Doctor', '') for r in records if r.get('Doctor'))),
                key="filter_doctor"
            )
        with col3:
            filter_discrepancy = st.selectbox(
                "Discrepancy",
                ["All", "Yes", "No"],
                key="filter_discrepancy"
            )
        with col4:
            filter_mrn = st.text_input("MRN", key="filter_mrn")
    
    # Apply filters
    filtered_records = records.copy()
    if filter_hospital != "All":
        filtered_records = [r for r in filtered_records if r.get('Hospital') == filter_hospital]
    if filter_doctor != "All":
        filtered_records = [r for r in filtered_records if r.get('Doctor') == filter_doctor]
    if filter_discrepancy != "All":
        filtered_records = [r for r in filtered_records if r.get('Discrepancy') == filter_discrepancy]
    if filter_mrn:
        filtered_records = [r for r in filtered_records if filter_mrn.lower() in r.get('MRN', '').lower()]
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Records", len(filtered_records))
    with col2:
        disc_yes = len([r for r in filtered_records if r.get('Discrepancy') == 'Yes'])
        st.metric("With Discrepancy", disc_yes, delta=None)
    with col3:
        disc_no = len([r for r in filtered_records if r.get('Discrepancy') != 'Yes'])
        st.metric("No Discrepancy", disc_no)
    with col4:
        unique_patients = len(set(r.get('MRN', '') for r in filtered_records))
        st.metric("Unique Patients", unique_patients)
    
    # Convert to DataFrame for display
    if filtered_records:
        df = pd.DataFrame(filtered_records)
        display_columns = ['Hospital', 'Doctor', 'Patient', 'MRN', 'Service Date', 'Discrepancy']
        display_df = df[[c for c in display_columns if c in df.columns]]
        
        # Selectable dataframe
        st.markdown("### Records")
        
        # Add selection column
        selected_indices = st.multiselect(
            "Select records to manage",
            options=range(len(filtered_records)),
            format_func=lambda i: f"{filtered_records[i].get('MRN', 'N/A')} - {filtered_records[i].get('Patient', 'N/A')} ({filtered_records[i].get('Service Date', 'N/A')})"
        )
        
        # Display as table
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Action buttons
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if st.button("✏️ Edit Selected", disabled=len(selected_indices) != 1):
                if selected_indices:
                    edit_record(selected_indices[0])
        
        with col2:
            if st.button("👁️ View Details", disabled=len(selected_indices) != 1):
                if selected_indices:
                    view_record_details(filtered_records[selected_indices[0]])
        
        with col3:
            if st.button("📋 Duplicate", disabled=len(selected_indices) != 1):
                if selected_indices:
                    duplicate_record(selected_indices[0])
        
        with col4:
            if st.button("🗑️ Delete Selected", disabled=len(selected_indices) == 0):
                if selected_indices:
                    delete_selected_records(selected_indices)
        
        with col5:
            if st.button("☁️ Sync to Cloud"):
                sync_all_to_cloud()
        
        # Export options
        st.markdown("---")
        st.subheader("📤 Export Options")
        
        export_col1, export_col2, export_col3 = st.columns(3)
        
        with export_col1:
            if XLSX_AVAILABLE:
                excel_data = export_to_excel(filtered_records)
                if excel_data:
                    st.download_button(
                        "📊 Download Excel",
                        data=excel_data,
                        file_name=f"Easy_Audit_Export_{dt.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        
        with export_col2:
            if DOCX_AVAILABLE:
                docx_data = export_to_docx(filtered_records)
                if docx_data:
                    st.download_button(
                        "📄 Download Word",
                        data=docx_data,
                        file_name=f"Easy_Audit_Report_{dt.now().strftime('%Y%m%d_%H%M%S')}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
        
        with export_col3:
            json_data = json.dumps(filtered_records, indent=2)
            st.download_button(
                "📋 Download JSON",
                data=json_data,
                file_name=f"Easy_Audit_Backup_{dt.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )

def edit_record(index: int):
    """Load record into form for editing"""
    record = st.session_state.records[index]
    st.session_state.editing_record = index
    
    # Populate form fields
    st.session_state.hospital_select = record.get('Hospital', '')
    st.session_state.doctor_select = record.get('Doctor', '')
    st.session_state.patient_input = record.get('Patient', '')
    st.session_state.mrn_input = record.get('MRN', '')
    st.session_state.insurance_select = record.get('Insurance', '')
    st.session_state.charged_services = record.get('Charged Services', '')
    st.session_state.approved_services = record.get('Approved Services', '')
    st.session_state.attending_note = record.get('Attending Note', '')
    st.session_state.has_discrepancy = record.get('Discrepancy', 'No')
    st.session_state.discrepancy_details = record.get('Discrepancy Details', '')
    
    st.info("📝 Record loaded for editing. Go to Data Entry tab to modify.")
    st.rerun()

def view_record_details(record: dict):
    """Display detailed view of a record"""
    st.markdown("---")
    st.subheader(f"📋 Record Details - {record.get('Patient', 'N/A')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Patient Information**")
        st.write(f"🏥 Hospital: {record.get('Hospital', 'N/A')}")
        st.write(f"👨‍⚕️ Doctor: {record.get('Doctor', 'N/A')}")
        st.write(f"👤 Patient: {record.get('Patient', 'N/A')}")
        st.write(f"🔢 MRN: {record.get('MRN', 'N/A')}")
        st.write(f"🏢 Insurance: {record.get('Insurance', 'N/A')}")
    
    with col2:
        st.markdown("**Dates**")
        st.write(f"📅 Audit Date: {record.get('Audit Date', 'N/A')}")
        st.write(f"📅 Service Date: {record.get('Service Date', 'N/A')}")
        st.write(f"📅 Invoice Date: {record.get('Invoice Date', 'N/A')}")
        st.write(f"📅 Approval Date: {record.get('Approval Date', 'N/A')}")
    
    st.markdown("---")
    st.markdown("**Services**")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("*Charged Services:*")
        st.text(record.get('Charged Services', 'None'))
    with col2:
        st.markdown("*Approved Services:*")
        st.text(record.get('Approved Services', 'None'))
    
    st.markdown("---")
    st.markdown("**Clinical Notes**")
    st.text(record.get('Attending Note', 'None'))
    
    # Discrepancy
    if record.get('Discrepancy') == 'Yes':
        st.error(f"⚠️ Discrepancy: {record.get('Discrepancy Details', 'Yes')}")
    else:
        st.success("✅ No discrepancy")
    
    # Auto-detected discrepancies
    auto_disc = get_auto_discrepancies(record)
    if auto_disc:
        st.warning("**Auto-Detected Issues:**")
        for d in auto_disc:
            st.write(d)

def duplicate_record(index: int):
    """Duplicate a record"""
    record = st.session_state.records[index].copy()
    record['Created Date'] = dt.now().strftime("%d/%m/%Y %H:%M")
    st.session_state.records.append(record)
    st.success("✅ Record duplicated")
    st.rerun()

def delete_selected_records(indices: List[int]):
    """Delete selected records"""
    # Sort indices in reverse to delete from end first
    for index in sorted(indices, reverse=True):
        record = st.session_state.records[index]
        # Delete from cloud
        username = st.session_state.current_user['username']
        delete_record_from_supabase(
            record.get('MRN', ''),
            record.get('Service Date', ''),
            username
        )
        # Delete locally
        del st.session_state.records[index]
    
    st.success(f"✅ Deleted {len(indices)} record(s)")
    st.rerun()

def sync_all_to_cloud():
    """Sync all records to cloud"""
    username = st.session_state.current_user['username']
    success_count = 0
    
    progress = st.progress(0)
    for i, record in enumerate(st.session_state.records):
        if save_record_to_supabase(record, username):
            success_count += 1
        progress.progress((i + 1) / len(st.session_state.records))
    
    st.success(f"☁️ Synced {success_count}/{len(st.session_state.records)} records to cloud")

# ==================== SEARCH TAB ====================
def search_tab():
    """Render search interface"""
    st.subheader("🔍 Search Records")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_doctor = st.text_input("Doctor Name", key="search_doctor")
    with col2:
        search_patient = st.text_input("Patient Name", key="search_patient")
    with col3:
        search_mrn = st.text_input("MRN", key="search_mrn")
    with col4:
        search_hospital = st.selectbox(
            "Hospital",
            ["All"] + list(BRANCH_DOCTORS.keys()),
            key="search_hospital"
        )
    
    col1, col2, col3 = st.columns(3)
    with col1:
        search_date_type = st.selectbox("Date Type", ["Audit Date", "Service Date", "Invoice Date"])
    with col2:
        search_date = st.date_input("Search Date", value=None, key="search_date")
    with col3:
        search_discrepancy = st.selectbox("Discrepancy Filter", ["All", "Yes", "No"], key="search_disc")
    
    if st.button("🔍 Search", type="primary"):
        results = st.session_state.records.copy()
        
        if search_doctor:
            results = [r for r in results if search_doctor.lower() in r.get('Doctor', '').lower()]
        if search_patient:
            results = [r for r in results if search_patient.lower() in r.get('Patient', '').lower()]
        if search_mrn:
            results = [r for r in results if search_mrn.lower() in r.get('MRN', '').lower()]
        if search_hospital != "All":
            results = [r for r in results if r.get('Hospital') == search_hospital]
        if search_date:
            date_str = search_date.strftime("%d/%m/%Y")
            results = [r for r in results if r.get(search_date_type) == date_str]
        if search_discrepancy != "All":
            results = [r for r in results if r.get('Discrepancy') == search_discrepancy]
        
        st.session_state.search_results = results
    
    # Display results
    if st.session_state.search_results:
        st.markdown("---")
        st.subheader(f"Found {len(st.session_state.search_results)} records")
        
        col1, col2 = st.columns(2)
        with col1:
            disc_yes = len([r for r in st.session_state.search_results if r.get('Discrepancy') == 'Yes'])
            st.metric("With Discrepancy", disc_yes)
        with col2:
            disc_no = len(st.session_state.search_results) - disc_yes
            st.metric("No Discrepancy", disc_no)
        
        df = pd.DataFrame(st.session_state.search_results)
        display_columns = ['Hospital', 'Doctor', 'Patient', 'MRN', 'Service Date', 'Discrepancy']
        display_df = df[[c for c in display_columns if c in df.columns]]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Export search results
        if st.button("📤 Export Search Results"):
            excel_data = export_to_excel(st.session_state.search_results)
            if excel_data:
                st.download_button(
                    "📊 Download Excel",
                    data=excel_data,
                    file_name=f"Search_Results_{dt.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    elif st.session_state.search_results is not None and len(st.session_state.search_results) == 0:
        st.info("No records found matching your criteria.")

# ==================== ADA CODES TAB ====================
def ada_codes_tab():
    """Render ADA codes reference"""
    st.subheader("📚 ADA/Dental Codes Reference")
    
    search_code = st.text_input("🔍 Search Code or Description", key="ada_search")
    
    # Filter codes
    if search_code:
        filtered_codes = {
            code: info for code, info in DENTAL_CODES.items()
            if search_code.upper() in code.upper() or search_code.lower() in info['description'].lower()
        }
    else:
        filtered_codes = DENTAL_CODES
    
    # Group by category
    categories = {}
    for code, info in filtered_codes.items():
        cat = info.get('category', 'other')
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((code, info))
    
    # Display by category
    for category, codes in sorted(categories.items()):
        with st.expander(f"📁 {category.replace('_', ' ').title()} ({len(codes)} codes)", expanded=bool(search_code)):
            for code, info in sorted(codes, key=lambda x: x[0]):
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.code(code)
                with col2:
                    st.write(info['description'])
    
    st.markdown("---")
    st.info("""
    **Reference Notes:**
    - Codes follow ADA (American Dental Association) and Australian dental coding standards
    - Always verify codes with your local insurance requirements
    - Some codes may have regional variations
    """)

# ==================== MAIN ENTRY POINT ====================
def main():
    """Main application entry point"""
    st.set_page_config(
        page_title="Easy Audit - Dental Auditing",
        page_icon="🦷",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for modern look
    st.markdown("""
    <style>
    /* Main app styling */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%);
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: #2c3e50;
    }
    
    /* Button styling */
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Card styling */
    .stExpander {
        background: white;
        border-radius: 12px;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }
    
    /* Input styling */
    .stTextInput>div>div>input,
    .stSelectbox>div>div>select,
    .stTextArea>div>div>textarea {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #667eea;
    }
    
    /* DataFrame styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Success/Error message styling */
    .stSuccess, .stError, .stWarning, .stInfo {
        border-radius: 8px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    init_session_state()
    
    # Route to appropriate page
    if not st.session_state.authenticated:
        login_page()
    else:
        main_app()

if __name__ == "__main__":
    main()
