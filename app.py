"""
Easy Tracking Pro - Streamlit Edition
A modern, professional dental auditing application with AI-powered analysis.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import re
import requests
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
from urllib.parse import quote

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Easy Tracking Pro",
    page_icon="🦷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== SUPABASE CONFIG ====================
SUPABASE_URL = "https://yqekjzklcomwzxkdwkga.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlxZWtqemtsY29td3p4a2R3a2dhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjE5Njk5NSwiZXhwIjoyMDc3NzcyOTk1fQ.Z5wxHzCVcqzRmmytyj6uNjUQf42RWlVoaQyyr3N456g"

# ==================== CEREBRAS CONFIG ====================
CEREBRAS_API_KEY = "csk-x4w2dyw62kdhdpcwcpt644mc8mk6mp9nwkn9rerhwd2x5v34"
CEREBRAS_API_BASE_URL = "https://api.cerebras.ai/v1"

CEREBRAS_CLOUD_MODELS = ["llama-3.3-70b", "llama3.1-8b", "qwen-3-32b"]
OLLAMA_LOCAL_MODELS = ["llama3.2:latest", "llama3.1:latest", "mistral:latest", "qwen2.5:latest"]

# ==================== SEVERITY RULES ====================
DISCREPANCY_SEVERITY_RULES = {
    "missing tooth number": "MILD", "missing attending note": "MODERATE", "uncharged service": "SEVERE",
    "unclear notes": "MILD", "wrong quantity": "SEVERE", "wrong code": "SEVERE",
    "done by different operator": "MODERATE", "missing code in attending notes": "SEVERE",
    "wrong tooth number": "SEVERE", "wrong code of service": "SEVERE", "wrong number of services": "MODERATE",
    "rejected approval": "SEVERE", "missing pdf": "MILD", "approved for different operator": "MODERATE",
    "expired approval": "SEVERE", "service approved for wrong patient": "SEVERE", "retrograde approval": "SEVERE",
    "missing radiograph": "SEVERE", "missing pan": "SEVERE", "missing pa": "SEVERE",
    "wrong patient": "MODERATE", "wrong date": "MODERATE", "wrong tooth": "SEVERE",
    "unclear radiograph": "MILD", "unnecessary cbct": "MODERATE", "wrong code consent": "SEVERE",
    "wrong tooth consent": "SEVERE", "missing signature": "SEVERE", "date after procedure": "SEVERE",
    "expired consent": "SEVERE", "missing consent pdf": "SEVERE", "expired": "SEVERE",
    "incompatible": "MILD", "missing nurse assessment": "MILD",
}


# ==================== HELPER FUNCTIONS ====================
def get_record_field(record: Dict, *names, default: str = "") -> str:
    """Return first non-empty value for any of the provided column name variants."""
    if not isinstance(record, dict):
        return default
    for n in names:
        if not n:
            continue
        val = record.get(n) or record.get(str(n).lower()) or record.get(str(n).title())
        if val is None:
            val = record.get(str(n).replace(' ', '_')) or record.get(str(n).replace(' ', '_').lower())
        if val is not None:
            s = str(val).strip()
            if s and s.lower() not in ("none", "nan", "null"):
                return s
    return default


def get_severity_from_discrepancy(discrepancy_text: str) -> str:
    if not discrepancy_text:
        return "MODERATE"
    disc_lower = discrepancy_text.lower().strip()
    for rule_key, severity in DISCREPANCY_SEVERITY_RULES.items():
        if rule_key in disc_lower:
            return severity
    if any(kw in disc_lower for kw in ['uncharged', 'missing code', 'wrong code', 'wrong quantity', 
                                        'rejected', 'expired', 'wrong patient', 'missing signature']):
        return "SEVERE"
    elif any(kw in disc_lower for kw in ['different operator', 'wrong number', 'wrong date']):
        return "MODERATE"
    return "MODERATE"


def get_severity_badge_html(severity: str) -> str:
    colors = {"SEVERE": ("badge-danger", "🔴"), "MODERATE": ("badge-warning", "🟡"), "MILD": ("badge-info", "🔵")}
    badge_class, icon = colors.get(severity.upper(), ("badge-info", "⚪"))
    return f'<span class="badge {badge_class}">{icon} {severity}</span>'


def has_discrepancy(record: Dict) -> bool:
    disc = get_record_field(record, 'Discrepancy', 'discrepancy', default='')
    return disc.lower() not in ['', 'no', 'none', 'nil', 'null']


# ==================== SUPABASE CLIENT ====================
class SupabaseClient:
    def __init__(self):
        self.url = SUPABASE_URL
        self.key = SUPABASE_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
    
    def test_connection(self) -> Dict:
        try:
            response = requests.get(f"{self.url}/rest/v1/", headers={"apikey": self.key}, timeout=10)
            return {"success": response.status_code in [200, 404], "status_code": response.status_code}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def fetch_easy_analysis_records(self, table_name: str = "Easy Tracker", discrepancy_only: bool = False) -> List[Dict]:
        """Fetch records from Easy Tracker table"""
        try:
            safe_table = quote(table_name, safe='')
            url = f"{self.url}/rest/v1/{safe_table}?select=*"
            
            headers = self.headers.copy()
            headers['Range'] = '0-999'
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code in [200, 206]:
                records = response.json()
                if discrepancy_only:
                    records = [r for r in records if has_discrepancy(r)]
                return records
            else:
                st.error(f"Error {response.status_code}: {response.text[:200]}")
                return []
        except Exception as e:
            st.error(f"Fetch error: {e}")
            return []
    
    def get_available_tables(self) -> List[str]:
        tables_to_try = ["Easy Tracker", "easy_tracker", "easy_analysis", "audit_records_mmorgan"]
        available = []
        for table in tables_to_try:
            try:
                safe_table = quote(table, safe='')
                response = requests.get(
                    f"{self.url}/rest/v1/{safe_table}?select=*&limit=1",
                    headers=self.headers, timeout=10
                )
                if response.status_code in [200, 206]:
                    available.append(table)
            except:
                pass
        return available


# ==================== AI ANALYZER ====================
class AIAnalyzer:
    def __init__(self, model: str = "llama-3.3-70b", use_cerebras: bool = True):
        self.model = model
        self.use_cerebras = use_cerebras
    
    def set_model(self, model: str, use_cerebras: bool):
        self.model = model.replace(" (Cerebras Cloud)", "").strip()
        self.use_cerebras = use_cerebras
    
    def test_connection(self) -> Dict:
        try:
            if self.use_cerebras:
                headers = {"Authorization": f"Bearer {CEREBRAS_API_KEY}", "Content-Type": "application/json"}
                response = requests.get(f"{CEREBRAS_API_BASE_URL}/models", headers=headers, timeout=10)
                return {"success": response.status_code == 200, "message": "Cerebras OK" if response.status_code == 200 else "Error"}
            else:
                response = requests.get('http://localhost:11434/api/tags', timeout=5)
                return {"success": response.status_code == 200, "message": "Ollama OK"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    def _call_api(self, prompt: str, temperature: float = 0.3, max_tokens: int = 4096) -> str:
        try:
            if self.use_cerebras:
                headers = {"Authorization": f"Bearer {CEREBRAS_API_KEY}", "Content-Type": "application/json"}
                data = {"model": self.model, "messages": [{"role": "user", "content": prompt}], 
                        "temperature": temperature, "max_tokens": max_tokens}
                response = requests.post(f"{CEREBRAS_API_BASE_URL}/chat/completions", 
                                        headers=headers, json=data, timeout=120)
                if response.status_code == 200:
                    return response.json()['choices'][0]['message']['content']
                return f"API Error: {response.status_code}"
            else:
                response = requests.post('http://localhost:11434/api/generate',
                    json={"model": self.model, "prompt": prompt, "stream": False,
                          "options": {"temperature": temperature}}, timeout=300)
                if response.status_code == 200:
                    return response.json().get('response', '').strip()
                return f"Ollama Error: {response.status_code}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def analyze_record(self, record: Dict) -> Dict:
        charged = get_record_field(record, 'Charged Services', 'charged_services', default='')
        note = get_record_field(record, 'Attending Note', 'attending_note', default='')
        approved = get_record_field(record, 'Approved Services', 'approved_services', default='')
        
        prompt = f"""You are a Senior Dental Auditor. Analyze this dental record for discrepancies.

CHARGED SERVICES:
{charged if charged else "NOT PROVIDED"}

ATTENDING'S NOTE:
{note if note else "NOT PROVIDED"}

APPROVED SERVICES:
{approved if approved else "NOT PROVIDED"}

RULES:
- Panoramic X-ray (037, DY004), Scaling (114, 115) do NOT require tooth numbers
- Code equivalents: 037 = DY004, 114/115 = DG001/DG002
- Services for "next visit" are NOT discrepancies
- Empty fields ARE discrepancies

OUTPUT JSON ONLY (no markdown):
{{"summary": "2-3 sentence overview", "discrepancies": [{{"type": "TYPE", "severity": "SEVERE|MODERATE|MILD", "message": "explanation", "code": "code", "tooth": "number or NA", "fix": "recommendation"}}], "correct": ["correct items"], "advice": ["recommendations"]}}"""
        
        try:
            result = self._call_api(prompt)
            result = result.strip()
            if result.startswith("```"):
                result = re.sub(r'^```\w*\n?', '', result)
                result = re.sub(r'\n?```$', '', result)
            json_match = re.search(r'\{[\s\S]*\}', result)
            if json_match:
                return json.loads(json_match.group())
            return {"error": "Could not parse response", "raw": result[:500]}
        except Exception as e:
            return {"error": str(e)}
    
    def chat(self, message: str, context: Optional[Dict] = None) -> str:
        ctx = f"\n\nContext:\n{json.dumps(context, indent=2)}" if context else ""
        prompt = f"""You are a dental auditing assistant. Be concise and professional.
{ctx}

Question: {message}

Answer:"""
        return self._call_api(prompt, temperature=0.7)


# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

:root { --primary: #0066FF; --success: #00C853; --warning: #FFB300; --danger: #FF3D00; }

.stApp { font-family: 'Plus Jakarta Sans', sans-serif; background: linear-gradient(135deg, #F8FAFC 0%, #EEF2FF 100%); }
#MainMenu, footer, header { visibility: hidden; }

.main-header {
    background: linear-gradient(135deg, #0066FF 0%, #0052CC 50%, #003D99 100%);
    padding: 2rem 2.5rem; border-radius: 20px; margin-bottom: 2rem;
    box-shadow: 0 10px 40px rgba(0, 102, 255, 0.3);
}
.main-header h1 { color: white; font-size: 2.5rem; font-weight: 700; margin: 0; }
.main-header p { color: rgba(255,255,255,0.85); font-size: 1.1rem; margin: 0.5rem 0 0 0; }

.metric-card {
    background: white; padding: 1.5rem; border-radius: 16px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #E2E8F0; margin-bottom: 1rem;
}
.metric-card .value { font-size: 2.5rem; font-weight: 700; color: #1E293B; }
.metric-card .label { font-size: 0.875rem; color: #64748B; text-transform: uppercase; margin-top: 0.5rem; }
.metric-card.success { border-left: 4px solid #00C853; }
.metric-card.warning { border-left: 4px solid #FFB300; }
.metric-card.danger { border-left: 4px solid #FF3D00; }
.metric-card.primary { border-left: 4px solid #0066FF; }

.card { background: white; padding: 1.5rem; border-radius: 16px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 1rem; }

.badge { display: inline-flex; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }
.badge-success { background: #DCFCE7; color: #166534; }
.badge-warning { background: #FEF3C7; color: #92400E; }
.badge-danger { background: #FEE2E2; color: #991B1B; }
.badge-info { background: #DBEAFE; color: #1E40AF; }

.analysis-result { padding: 1.25rem; border-radius: 12px; margin-bottom: 1rem; }
.analysis-result.severe { background: linear-gradient(135deg, #FEE2E2, #FECACA); border-left: 4px solid #DC2626; }
.analysis-result.moderate { background: linear-gradient(135deg, #FEF3C7, #FDE68A); border-left: 4px solid #D97706; }
.analysis-result.mild { background: linear-gradient(135deg, #DBEAFE, #BFDBFE); border-left: 4px solid #2563EB; }
.analysis-result.success { background: linear-gradient(135deg, #DCFCE7, #BBF7D0); border-left: 4px solid #16A34A; }

.chat-message { padding: 1rem; border-radius: 16px; margin-bottom: 0.75rem; max-width: 85%; }
.chat-message.user { background: linear-gradient(135deg, #0066FF, #0052CC); color: white; margin-left: auto; }
.chat-message.assistant { background: white; border: 1px solid #E2E8F0; }

.record-detail { background: #F8FAFC; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem; border-left: 3px solid #0066FF; }

.stButton > button {
    background: linear-gradient(135deg, #0066FF, #0052CC); color: white; border: none;
    padding: 0.75rem 1.5rem; border-radius: 10px; font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# ==================== SESSION STATE ====================
if 'supabase' not in st.session_state:
    st.session_state.supabase = SupabaseClient()
if 'ai' not in st.session_state:
    st.session_state.ai = AIAnalyzer()
if 'records' not in st.session_state:
    st.session_state.records = []
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'last_analysis' not in st.session_state:
    st.session_state.last_analysis = None


# ==================== HEADER ====================
st.markdown("""
<div class="main-header">
    <h1>🦷 Easy Tracking Pro</h1>
    <p>AI-Powered Dental Audit Analysis • Real-time Discrepancy Detection • Professional Compliance Reporting</p>
</div>
""", unsafe_allow_html=True)


# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    st.markdown("### 🤖 AI Model")
    model_type = st.radio("Model Type", ["☁️ Cloud (Cerebras)", "🖥️ Local (Ollama)"], index=0)
    
    if "Cloud" in model_type:
        selected_model = st.selectbox("Select Model", CEREBRAS_CLOUD_MODELS, index=0)
        st.session_state.ai.set_model(selected_model, use_cerebras=True)
    else:
        selected_model = st.selectbox("Select Model", OLLAMA_LOCAL_MODELS, index=0)
        st.session_state.ai.set_model(selected_model, use_cerebras=False)
    
    st.markdown("---")
    st.markdown("### 📂 Data Source")
    table_name = st.selectbox("Table", ["Easy Tracker", "easy_analysis", "audit_records_mmorgan"], index=0)
    
    st.markdown("---")
    st.markdown("### 📡 Connection")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔌 DB", use_container_width=True):
            result = st.session_state.supabase.test_connection()
            st.success("✓" if result['success'] else "✗")
    with col2:
        if st.button("🧠 AI", use_container_width=True):
            result = st.session_state.ai.test_connection()
            st.success("✓" if result['success'] else "✗")
    
    if st.button("🔍 Find Tables", use_container_width=True):
        tables = st.session_state.supabase.get_available_tables()
        st.info(f"Found: {', '.join(tables)}" if tables else "No tables found")
    
    st.markdown("---")
    st.markdown("### 📊 Stats")
    if st.session_state.records:
        total = len(st.session_state.records)
        with_disc = sum(1 for r in st.session_state.records if has_discrepancy(r))
        st.metric("Total", total)
        st.metric("Discrepancies", with_disc)
        st.metric("Rate", f"{(with_disc/total*100):.1f}%" if total > 0 else "0%")


# ==================== MAIN TABS ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "🔍 Analysis", "💬 Chat", "🤖 AI Check", "👨‍⚕️ Doctor"])


# ==================== TAB 1: DASHBOARD ====================
with tab1:
    st.markdown("### 📊 Live Tracking Dashboard")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True, key="dash_refresh"):
            with st.spinner("Loading..."):
                records = st.session_state.supabase.fetch_easy_analysis_records(table_name=table_name)
                if records:
                    st.session_state.records = records
                    st.success(f"✅ Loaded {len(records)} records!")
                    st.rerun()
                else:
                    st.warning("No records found")
    
    if not st.session_state.records:
        st.info("👆 Click **'Refresh Data'** to load records from Supabase")
    else:
        records = st.session_state.records
        total_records = len(records)
        records_with_disc = [r for r in records if has_discrepancy(r)]
        total_disc = len(records_with_disc)
        disc_rate = (total_disc / total_records * 100) if total_records > 0 else 0
        
        # Severity breakdown
        severity_counts = Counter()
        for r in records_with_disc:
            severity = get_severity_from_discrepancy(get_record_field(r, 'Discrepancy Details', default=''))
            severity_counts[severity] += 1
        
        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card primary"><div class="value">{total_records}</div><div class="label">📊 Total Cases</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card danger"><div class="value">{total_disc}</div><div class="label">⚠️ Discrepancies</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card warning"><div class="value">{disc_rate:.1f}%</div><div class="label">📈 Rate</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card success"><div class="value">{total_records - total_disc}</div><div class="label">✅ Clean</div></div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🎯 Severity Distribution")
            if severity_counts:
                colors_map = {'SEVERE': '#DC2626', 'MODERATE': '#D97706', 'MILD': '#2563EB'}
                fig = go.Figure(data=[go.Pie(
                    labels=list(severity_counts.keys()), values=list(severity_counts.values()), hole=0.6,
                    marker_colors=[colors_map.get(k, '#6B7280') for k in severity_counts.keys()]
                )])
                fig.update_layout(showlegend=True, height=300, margin=dict(t=20, b=40, l=20, r=20))
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("✅ No discrepancies!")
        
        with col2:
            st.markdown("#### 🏥 Branch Performance")
            branch_stats = defaultdict(lambda: {'total': 0, 'disc': 0})
            for r in records:
                branch = get_record_field(r, 'Hospital', 'hospital', default='Unknown')
                branch_stats[branch]['total'] += 1
                if has_discrepancy(r):
                    branch_stats[branch]['disc'] += 1
            
            df_branch = pd.DataFrame([
                {'Branch': b, 'Cases': s['total'], 'Disc': s['disc'], 
                 'Rate': f"{(s['disc']/s['total']*100):.1f}%" if s['total'] > 0 else "0%"}
                for b, s in sorted(branch_stats.items(), key=lambda x: x[1]['disc'], reverse=True)
            ])
            st.dataframe(df_branch, use_container_width=True, hide_index=True)
        
        # Top Doctors
        st.markdown("#### 👨‍⚕️ Top 10 Doctors by Discrepancies")
        doctor_stats = defaultdict(lambda: {'total': 0, 'disc': 0})
        for r in records:
            doctor = get_record_field(r, 'Doctor', default='Unknown')
            doctor_stats[doctor]['total'] += 1
            if has_discrepancy(r):
                doctor_stats[doctor]['disc'] += 1
        
        top_docs = sorted(doctor_stats.items(), key=lambda x: x[1]['disc'], reverse=True)[:10]
        if top_docs and any(d[1]['disc'] > 0 for d in top_docs):
            fig = go.Figure(data=[go.Bar(
                x=[d[0][:20] for d in top_docs], y=[d[1]['disc'] for d in top_docs],
                marker_color='#0066FF', text=[d[1]['disc'] for d in top_docs], textposition='auto'
            )])
            fig.update_layout(xaxis_title="Doctor", yaxis_title="Discrepancies", height=350, margin=dict(b=100))
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)


# ==================== TAB 2: ANALYSIS ====================
with tab2:
    st.markdown("### 🔍 Manual Analysis")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 📋 Charged Services")
        charged_input = st.text_area("Charged services", height=180, key="charged", 
                                     placeholder="037: Panoramic radiograph (Count: 1) [Teeth: NA]")
    with col2:
        st.markdown("#### 📝 Attending's Note")
        note_input = st.text_area("Clinical notes", height=180, key="note",
                                  placeholder="Patient presented for checkup. OPG taken.")
    
    st.markdown("#### ✅ Approved Services")
    approved_input = st.text_area("Approved services", height=100, key="approved",
                                  placeholder="037: Panoramic radiograph approved")
    
    if st.button("🤖 Analyze with AI", type="primary"):
        if not charged_input and not note_input:
            st.warning("Enter data to analyze")
        else:
            with st.spinner("🧠 AI analyzing..."):
                record = {'Charged Services': charged_input, 'Attending Note': note_input, 'Approved Services': approved_input}
                st.session_state.last_analysis = st.session_state.ai.analyze_record(record)
    
    if st.session_state.last_analysis:
        analysis = st.session_state.last_analysis
        st.markdown("---")
        st.markdown("### 📊 Results")
        
        if 'error' in analysis:
            st.error(f"❌ {analysis['error']}")
            if 'raw' in analysis:
                with st.expander("Raw"):
                    st.code(analysis['raw'])
        else:
            st.markdown(f'<div class="card"><h4>📋 Summary</h4><p>{analysis.get("summary", "N/A")}</p></div>', unsafe_allow_html=True)
            
            discrepancies = analysis.get('discrepancies', [])
            if discrepancies:
                st.markdown(f"#### ⚠️ {len(discrepancies)} Discrepancies")
                for i, d in enumerate(discrepancies, 1):
                    sev = d.get('severity', 'MODERATE')
                    st.markdown(f'''<div class="analysis-result {sev.lower()}">
                        <strong>{i}. [{d.get("type", "ISSUE")}]</strong> {get_severity_badge_html(sev)}
                        <p>{d.get("message", "")}</p>
                        {f"<p><strong>Fix:</strong> {d['fix']}</p>" if d.get("fix") else ""}
                    </div>''', unsafe_allow_html=True)
            else:
                st.markdown('<div class="analysis-result success"><strong>✅ No Discrepancies!</strong></div>', unsafe_allow_html=True)


# ==================== TAB 3: CHAT ====================
with tab3:
    st.markdown("### 💬 AI Assistant")
    
    for msg in st.session_state.chat_history:
        cls = "user" if msg['role'] == 'user' else "assistant"
        st.markdown(f'<div class="chat-message {cls}"><strong>{"You" if cls == "user" else "🤖 AI"}:</strong> {msg["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    user_input = st.text_input("Ask a question...", key="chat_input", placeholder="What's the difference between 037 and DY004?")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("📤 Send", use_container_width=True) and user_input:
            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
            with st.spinner("🤔 Thinking..."):
                response = st.session_state.ai.chat(user_input, st.session_state.last_analysis)
                st.session_state.chat_history.append({'role': 'assistant', 'content': response})
            st.rerun()
    with col2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()


# ==================== TAB 4: AI CHECK ====================
with tab4:
    st.markdown("### 🤖 AI Discrepancy Analysis")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🔄 Load Records", use_container_width=True, key="ai_load"):
            with st.spinner("Loading..."):
                records = st.session_state.supabase.fetch_easy_analysis_records(table_name=table_name)
                if records:
                    st.session_state.records = records
                    st.success(f"✅ {len(records)} records")
    with col2:
        filter_opt = st.selectbox("Filter", ["All", "With Discrepancy", "Without"], key="ai_filter")
    
    if st.session_state.records:
        filtered = st.session_state.records.copy()
        if filter_opt == "With Discrepancy":
            filtered = [r for r in filtered if has_discrepancy(r)]
        elif filter_opt == "Without":
            filtered = [r for r in filtered if not has_discrepancy(r)]
        
        st.markdown(f"**{len(filtered)} records**")
        
        if filtered:
            opts = [f"{i+1}. {get_record_field(r, 'Patient', default='?')} | MRN: {get_record_field(r, 'MRN', default='?')}" 
                   for i, r in enumerate(filtered)]
            sel = st.selectbox("Select record", range(len(opts)), format_func=lambda i: opts[i])
            
            if sel is not None:
                rec = filtered[sel]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### 📋 Details")
                    st.markdown(f'''<div class="record-detail">
                        <strong>Patient:</strong> {get_record_field(rec, "Patient", default="?")}<br>
                        <strong>MRN:</strong> {get_record_field(rec, "MRN", default="?")}<br>
                        <strong>Doctor:</strong> {get_record_field(rec, "Doctor", default="?")}<br>
                        <strong>Hospital:</strong> {get_record_field(rec, "Hospital", default="?")}<br>
                        <strong>Status:</strong> {get_record_field(rec, "Discrepancy", default="None")}
                    </div>''', unsafe_allow_html=True)
                    
                    with st.expander("📝 Charged Services"):
                        st.text(get_record_field(rec, 'Charged Services', default='None'))
                    with st.expander("📝 Attending Note"):
                        st.text(get_record_field(rec, 'Attending Note', default='None'))
                    with st.expander("📝 Approved Services"):
                        st.text(get_record_field(rec, 'Approved Services', default='None'))
                
                with col2:
                    st.markdown("#### 🤖 AI Analysis")
                    if st.button("⚡ Analyze", type="primary", use_container_width=True):
                        with st.spinner("🧠 Analyzing..."):
                            st.session_state.last_analysis = st.session_state.ai.analyze_record(rec)
                    
                    if st.session_state.last_analysis:
                        a = st.session_state.last_analysis
                        if 'error' in a:
                            st.error(f"❌ {a['error']}")
                        else:
                            st.info(f"**Summary:** {a.get('summary', 'N/A')}")
                            discs = a.get('discrepancies', [])
                            if discs:
                                st.warning(f"⚠️ {len(discs)} discrepancies")
                                for d in discs:
                                    sev = d.get('severity', 'MODERATE')
                                    st.markdown(f'''<div class="analysis-result {sev.lower()}">
                                        <strong>[{d.get("type")}]</strong> {get_severity_badge_html(sev)}<br>
                                        {d.get("message", "")}
                                    </div>''', unsafe_allow_html=True)
                            else:
                                st.success("✅ No discrepancies!")


# ==================== TAB 5: DOCTOR ====================
with tab5:
    st.markdown("### 👨‍⚕️ Doctor Performance")
    
    if not st.session_state.records:
        st.info("Load records from Dashboard or AI Check tab first")
    else:
        doctors = sorted(set(get_record_field(r, 'Doctor', default='?') for r in st.session_state.records))
        doctors = [d for d in doctors if d and d != '?']
        
        sel_doc = st.selectbox("Select Doctor", [""] + doctors)
        
        if sel_doc:
            doc_recs = [r for r in st.session_state.records if get_record_field(r, 'Doctor', default='') == sel_doc]
            total = len(doc_recs)
            with_d = sum(1 for r in doc_recs if has_discrepancy(r))
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("📊 Cases", total)
            c2.metric("⚠️ Disc", with_d)
            c3.metric("✅ Clean", total - with_d)
            c4.metric("📈 Rate", f"{(with_d/total*100):.1f}%" if total > 0 else "0%")
            
            # Breakdown
            disc_types = Counter()
            for r in doc_recs:
                if has_discrepancy(r):
                    disc_types[get_record_field(r, 'Discrepancy Details', 'Discrepancy', default='Unknown')] += 1
            
            if disc_types:
                st.markdown("#### 📊 Discrepancy Types")
                df = pd.DataFrame([{'Type': k[:50], 'Count': v} for k, v in disc_types.most_common(5)])
                st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.markdown("#### 📋 Recent Cases")
            df_cases = pd.DataFrame([{
                'Date': get_record_field(r, 'Service Date', default='?'),
                'Patient': get_record_field(r, 'Patient', default='?'),
                'MRN': get_record_field(r, 'MRN', default='?'),
                'Discrepancy': get_record_field(r, 'Discrepancy', default='None')
            } for r in doc_recs[:15]])
            st.dataframe(df_cases, use_container_width=True, hide_index=True)


# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748B; font-size: 0.875rem;">
    <p><strong>Easy Tracking Pro</strong> v2.0 Streamlit • AI by Cerebras • © 2024</p>
</div>
""", unsafe_allow_html=True)
