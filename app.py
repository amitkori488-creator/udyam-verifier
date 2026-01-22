import streamlit as st
import requests
import uuid
import json
import pandas as pd
from datetime import datetime
import io

# --- Page Config ---
st.set_page_config(
    page_title="CorpVerify | Udyam Intelligence",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME & CSS OVERRIDES ---
st.markdown("""
    <style>
        /* --- 1. HIDE STREAMLIT BRANDING --- */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        .stDeployButton { display: none; }
        header[data-testid="stHeader"] { background-color: transparent; border: none; }
        div[class^="block-container"] { padding-top: 2rem; }

        /* --- 2. APP STYLING --- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: #0f172a;
        }
        
        .stApp { background-color: #f8fafc; }
        
        /* SIDEBAR STYLING */
        section[data-testid="stSidebar"] {
            background-color: #0f172a;
            border-right: 1px solid #1e293b;
        }
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] h3, 
        section[data-testid="stSidebar"] label, 
        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] p {
            color: #e2e8f0 !important;
        }
        
        /* Sidebar Inputs */
        section[data-testid="stSidebar"] input {
            background-color: #1e293b;
            color: white;
            border: 1px solid #334155;
        }
        
        /* Content Cards */
        div[data-testid="stVerticalBlock"] > div[style*="background-color"] {
            background-color: white;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        }

        /* Buttons & Inputs */
        div.stButton > button {
            background-color: #2563eb;
            color: white;
            border-radius: 8px;
            height: 48px;
            font-weight: 600;
            border: none;
        }
        div.stButton > button:hover {
            background-color: #1d4ed8;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
        }
        .stTextInput input {
            padding: 12px;
            border-radius: 8px;
            border: 1px solid #cbd5e1;
            height: 48px;
        }
    </style>
""", unsafe_allow_html=True)

# --- Session State ---
if 'history' not in st.session_state:
    # Started as empty list (No mock data)
    st.session_state.history = []

# --- Helper Functions ---
def add_to_history(pan, name, udyam, status):
    st.session_state.history.insert(0, {
        "Time": datetime.now().strftime("%H:%M:%S"),
        "UDYAM NO.": udyam,
        "PAN": pan,
        "Entity Name": name,
        "Status": status
    })

def fetch_udyam_details(client_id, client_secret, pan_number, use_sandbox):
    # --- REAL API LOGIC ONLY (Mocking Removed) ---
    
    # Validation
    if not client_id or not client_secret:
        return {
            "status": "ERROR", 
            "message": "API Keys Missing. Please provide Client ID and Secret in sidebar."
        }

    if use_sandbox:
        base_url = "https://sandbox.cashfree.com/verification"
    else:
        base_url = "https://api.cashfree.com/verification"

    endpoint = f"{base_url}/pan-udyam"
    headers = {
        "x-client-id": client_id,
        "x-client-secret": client_secret,
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.post(endpoint, headers=headers, data=json.dumps({
            "verification_id": str(uuid.uuid4()),
            "pan": pan_number
        }), timeout=10)
        
        # Handle non-200 but valid JSON responses (like 400 Bad Request from API)
        if response.status_code != 200:
            try:
                err_data = response.json()
                return {"status": "ERROR", "message": err_data.get("message", response.reason)}
            except:
                return {"status": "ERROR", "message": f"HTTP {response.status_code}: {response.reason}"}

        return response.json()
    except requests.exceptions.Timeout:
        return {"status": "ERROR", "message": "Request timed out."}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Verification History')
    return output.getvalue()

# --- SIDEBAR CONTENT ---
with st.sidebar:
    # Header
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px; padding-bottom: 24px; border-bottom: 1px solid #1e293b;">
            <div style="width: 32px; height: 32px; background-color: #2563eb; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
            </div>
            <span style="font-size: 1.125rem; font-weight: 700; color: white;">CorpVerify<span style="color: #3b82f6;">.io</span></span>
        </div>
    """, unsafe_allow_html=True)
    
    # Configuration
    st.markdown("<p style='font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px;'>Configuration</p>", unsafe_allow_html=True)

    # API Keys Logic
    try:
        default_id = st.secrets["CASHFREE_CLIENT_ID"]
        default_secret = st.secrets["CASHFREE_CLIENT_SECRET"]
        secrets_found = True
    except (FileNotFoundError, KeyError):
        default_id = ""
        default_secret = ""
        secrets_found = False

    if secrets_found:
        st.success("🔒 Secured by Cloud Secrets")
        client_id = default_id
        client_secret = default_secret
    else:
        client_id = st.text_input("Client ID", value="", placeholder="Required")
        client_secret = st.text_input("Client Secret", value="", type="password", placeholder="Required")
            
    use_sandbox = st.toggle("Sandbox Mode", value=True)
    
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 12px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px;'>Platform</p>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style="background: #2563eb; color: white; padding: 10px 12px; border-radius: 8px; margin-bottom: 8px; font-size: 14px; font-weight: 500; display: flex; align-items: center; gap: 10px;">
            Verify Identity
        </div>
        <div style="color: #94a3b8; padding: 10px 12px; font-size: 14px; font-weight: 500;">History Log</div>
        <div style="color: #94a3b8; padding: 10px 12px; font-size: 14px; font-weight: 500;">Usage Analytics</div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Admin Access • v2.6.0")


# --- MAIN CONTENT ---

# 1. Custom Header
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown('<h1 style="margin-bottom: 0;">Udyam Verification</h1>', unsafe_allow_html=True)
with col_h2:
    st.markdown("""
        <div style="display: flex; justify-content: flex-end; align-items: center; gap: 12px; height: 100%;">
            <div style="background: #eff6ff; color: #1d4ed8; padding: 6px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; border: 1px solid #dbeafe; display: flex; align-items: center; gap: 6px;">
                <span style="width: 6px; height: 6px; background: #2563eb; border-radius: 50%;"></span>
                System Operational
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 32px'></div>", unsafe_allow_html=True)

# 2. Search Card
with st.container():
    st.markdown("""
        <h2 style="font-size: 24px; font-weight: 700; color: #0f172a; margin-bottom: 8px;">Verify Business Entity</h2>
        <p style="color: #64748b; margin-bottom: 24px;">Enter the Permanent Account Number (PAN) to fetch official Udyam Registration details via Cashfree API.</p>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([5, 1])
    with c1:
        pan_number = st.text_input("PAN Number", placeholder="ABCDE1234F", label_visibility="collapsed").upper()
    with c2:
        fetch_btn = st.button("Verify", use_container_width=True)


# 3. Logic & Results
if fetch_btn:
    if len(pan_number) < 5:
        st.toast("Please enter a valid PAN.", icon="⚠️")
    else:
        with st.spinner("Connecting to Registry API..."):
            response = fetch_udyam_details(client_id, client_secret, pan_number, use_sandbox)

        if response.get("status") == "SUCCESS":
            data = response.get("data", {})
            # Handle case where API returns success but empty data (unlikely but possible)
            if not data:
                st.error("API returned Success but no data found.")
            else:
                add_to_history(pan_number, data.get("name", "N/A"), data.get("udyamNumber", "N/A"), "Verified")
                
                st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
                
                with st.container():
                    st.markdown(f"""
                    <div style="display: flex; flex-wrap: wrap; gap: 24px; background-color: #f8fafc; padding: 24px; border-radius: 12px; border: 1px solid #e2e8f0;">
                        
                        <!-- Left Column: Status & Udyam No -->
                        <div style="flex: 1; min-width: 250px; display: flex; flex-direction: column; gap: 16px;">
                            <!-- Status Card -->
                            <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #d1fae5; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                                    <div style="width: 24px; height: 24px; background: #d1fae5; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #059669;">✔</div>
                                    <span style="color: #047857; font-weight: 600; font-size: 14px;">Active & Verified</span>
                                </div>
                                <div style="font-size: 28px; font-weight: 700; color: #0f172a;">{data.get('enterprise_type', 'N/A')}</div>
                                <div style="font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 4px;">Enterprise Type</div>
                            </div>

                            <!-- Number Card -->
                            <div style="background: white; padding: 20px; border-radius: 12px; border: 1px solid #e2e8f0;">
                                 <div style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px;">Udyam Registration Number</div>
                                 <div style="background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px dashed #cbd5e1; display: flex; justify-content: space-between; align-items: center;">
                                    <code style="color: #2563eb; font-weight: 700; font-size: 14px;">{data.get('udyamNumber', 'N/A')}</code>
                                 </div>
                            </div>
                        </div>

                        <!-- Right Column: Details Grid -->
                        <div style="flex: 2; min-width: 300px; background: white; padding: 24px; border-radius: 12px; border: 1px solid #e2e8f0;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #f1f5f9;">
                                <h3 style="font-size: 16px; font-weight: 600; color: #0f172a; margin: 0; display: flex; align-items: center; gap: 8px;">
                                    🏢 Entity Details
                                </h3>
                                <span style="color: #2563eb; font-size: 12px; font-weight: 500; cursor: pointer;">Download Report</span>
                            </div>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
                                <div>
                                    <label style="display: block; font-size: 12px; color: #64748b; margin-bottom: 4px;">Registered Name</label>
                                    <div style="font-weight: 500; color: #0f172a;">{data.get('name', 'N/A')}</div>
                                </div>
                                <div>
                                    <label style="display: block; font-size: 12px; color: #64748b; margin-bottom: 4px;">Major Activity</label>
                                    <div style="font-weight: 500; color: #0f172a;">{data.get('major_activity', 'N/A')}</div>
                                </div>
                                <div>
                                    <label style="display: block; font-size: 12px; color: #64748b; margin-bottom: 4px;">Registration Date</label>
                                    <div style="font-weight: 500; color: #0f172a;">{data.get('date_of_registration', 'N/A')}</div>
                                </div>
                                <div>
                                    <label style="display: block; font-size: 12px; color: #64748b; margin-bottom: 4px;">Location</label>
                                    <div style="font-weight: 500; color: #0f172a;">{data.get('district', '')}, {data.get('state', '')}</div>
                                </div>
                            </div>
                        </div>

                    </div>
                    """, unsafe_allow_html=True)

        elif response.get("status") == "UDYAM_NOT_FOUND":
            add_to_history(pan_number, "Unknown", "-", "Not Found")
            st.error(f"No Udyam Registration found for PAN: {pan_number}")
        elif response.get("status") == "ERROR":
             st.error(f"System Error: {response.get('message')}")
        else:
            st.error(f"API Error: {response.get('message', 'Unknown Error')}")


# 4. History Table
st.markdown("<div style='height: 40px'></div>", unsafe_allow_html=True)

h_col1, h_col2 = st.columns([1, 1])
with h_col1:
    st.markdown("<h3 style='font-size: 18px; font-weight: 600; color: #1e293b;'>Recent Verifications</h3>", unsafe_allow_html=True)

# Prepare DataFrame
df = pd.DataFrame(st.session_state.history)
if not df.empty:
    df.insert(0, 'S.No.', range(1, 1 + len(df)))
    
    # --- ORDER: S.No., Status, UDYAM NO., PAN, Entity Name, Time ---
    df = df[['S.No.', 'Status', 'UDYAM NO.', 'PAN', 'Entity Name', 'Time']]

    # Export Controls (Visual match)
    with st.container():
        row1, row2, row3 = st.columns([1, 1, 4])
        with row1:
            start_row = st.number_input("Start", min_value=1, max_value=len(df), value=1, label_visibility="collapsed")
        with row2:
            end_row = st.number_input("End", min_value=start_row, max_value=len(df), value=len(df), label_visibility="collapsed")
        with row3:
            if st.button("Download Excel Report", key="dl_btn"):
                # Real app would trigger download here
                pass

        st.dataframe(
            df, 
            use_container_width=True,
            hide_index=True,
            column_config={
                "S.No.": st.column_config.NumberColumn("S.No.", width="small"),
                "Status": st.column_config.TextColumn("Status", width="small"),
                "UDYAM NO.": st.column_config.TextColumn("UDYAM NO.", width="medium"),
                "PAN": st.column_config.TextColumn("PAN", width="medium"),
                "Entity Name": st.column_config.TextColumn("Entity Name", width="large"),
                "Time": st.column_config.TextColumn("Time", width="small"),
            }
        )
else:
    st.info("No verification history available.")
