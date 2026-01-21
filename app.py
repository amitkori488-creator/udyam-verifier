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
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Enhanced Custom CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #f8fafc; }
        h1 { color: #0f172a; font-family: 'Inter', sans-serif; font-weight: 700 !important; }
        div[data-testid="stContainer"] { border-radius: 12px; }
        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        div[data-testid="stMetricLabel"] { font-size: 0.8rem; color: #64748b; font-weight: 600; }
        div[data-testid="stMetricValue"] { font-size: 1.2rem; color: #0f172a; font-weight: 700; }
        .stTextInput input { padding: 12px; border-radius: 8px; border: 1px solid #cbd5e1; }
        section[data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; }
        div.stButton > button {
            background-color: #2563eb; color: white; border-radius: 8px;
            padding: 0.5rem 1rem; border: none; font-weight: 600; width: 100%;
        }
        div.stButton > button:hover { background-color: #1d4ed8; border-color: #1d4ed8; }
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    </style>
""", unsafe_allow_html=True)

# --- Session State for History ---
if 'history' not in st.session_state:
    st.session_state.history = []

def add_to_history(pan, name, udyam, status):
    st.session_state.history.insert(0, {
        "Time": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "UDYAM NO.": udyam,
        "PAN": pan,
        "Entity Name": name,
        "Status": status
    })

def fetch_udyam_details(client_id, client_secret, pan_number, use_sandbox):
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
        }))
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "status": "ERROR"}

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Verification History')
    return output.getvalue()

# --- Sidebar ---
with st.sidebar:
    st.markdown("### ⚙️ API Settings")
    
    # CHECK FOR SECRETS (This is the secure part)
    # It tries to get keys from st.secrets. If not found, defaults to empty string.
    try:
        default_id = st.secrets["CASHFREE_CLIENT_ID"]
        default_secret = st.secrets["CASHFREE_CLIENT_SECRET"]
        secrets_found = True
    except (FileNotFoundError, KeyError):
        default_id = ""
        default_secret = ""
        secrets_found = False

    with st.container(border=True):
        if secrets_found:
            st.success("🔒 Secured by Cloud Secrets")
            client_id = default_id
            client_secret = default_secret
            # We hide the inputs or disable them if secrets are found
            st.caption("Using credentials from secure configuration.")
        else:
            client_id = st.text_input("Client ID", value="", placeholder="Enter Client ID")
            client_secret = st.text_input("Client Secret", value="", type="password", placeholder="Enter Secret")
            
        use_sandbox = st.toggle("Sandbox Environment", value=True)
    
    st.markdown("### 📊 Monthly Quota")
    st.progress(0.45, text="450 / 1000 Calls Used")
    st.divider()
    st.caption("v2.5.0 • Secure Mode")

# --- Main Layout ---
col1, col2 = st.columns([3, 1])
with col1:
    st.title("Udyam Verification Portal")
    st.markdown("Verify business entities instantly using official government records.")
with col2:
    if client_id and client_secret:
        st.success("● API Connected")
    else:
        st.warning("● Config Required")

st.divider()

# Search Section
col_search, col_btn = st.columns([4, 1])
with col_search:
    pan_number = st.text_input("Enter PAN Number", max_chars=10, placeholder="ABCDE1234F", label_visibility="collapsed").upper()

with col_btn:
    fetch_btn = st.button("Verify Identity", use_container_width=True)

# Logic
if fetch_btn:
    if not client_id or not client_secret:
        st.toast("Please configure API credentials in the sidebar.", icon="⚠️")
    elif len(pan_number) != 10:
        st.toast("Invalid PAN Number format.", icon="❌")
    else:
        with st.spinner("Authenticating & Fetching Data..."):
            response = fetch_udyam_details(client_id, client_secret, pan_number, use_sandbox)
            
            if response.get("status") == "SUCCESS":
                data = response.get("data", {})
                add_to_history(pan_number, data.get("name"), data.get("udyamNumber"), "Verified")
                
                st.markdown("### ✅ Verification Result")
                with st.container(border=True):
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Status", "Active", delta="Verified", delta_color="normal")
                    m2.metric("Enterprise Type", data.get("enterprise_type", "N/A"))
                    m3.metric("State", data.get("state", "N/A"))
                    m4.metric("Activity", data.get("major_activity", "N/A"))
                    
                    st.divider()
                    
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.caption("Registered Entity Name")
                        st.subheader(data.get("name", "N/A"))
                    with c2:
                        st.caption("Udyam Registration Number")
                        st.code(data.get("udyamNumber", "N/A"), language="text")
                    
                    with st.expander("View Raw JSON Payload"):
                        st.json(response)
                        
            elif response.get("status") == "UDYAM_NOT_FOUND":
                add_to_history(pan_number, "Unknown", "-", "Not Found")
                st.error(f"No Udyam Registration found for PAN: {pan_number}")
            else:
                st.error(f"API Error: {response.get('message', 'Unknown Error')}")

# History Section
if len(st.session_state.history) > 0:
    st.divider()
    st.markdown("### 🕒 Recent Verification Log")
    
    df = pd.DataFrame(st.session_state.history)
    df.insert(0, 'S.No.', range(1, 1 + len(df)))
    
    desired_order = ['S.No.', 'UDYAM NO.', 'PAN', 'Entity Name', 'Time', 'Status']
    cols_to_use = [c for c in desired_order if c in df.columns]
    df = df[cols_to_use]

    with st.container(border=True):
        st.markdown("**Export Settings**")
        d_col1, d_col2, d_col3 = st.columns([1, 1, 2])
        
        with d_col1:
            start_row = st.number_input("Start Row", min_value=1, max_value=len(df), value=1)
        with d_col2:
            end_row = st.number_input("End Row", min_value=start_row, max_value=len(df), value=len(df))
        
        with d_col3:
            st.markdown("&nbsp;", unsafe_allow_html=True)
            df_download = df[(df['S.No.'] >= start_row) & (df['S.No.'] <= end_row)]
            
            try:
                excel_data = convert_df_to_excel(df_download)
                st.download_button(
                    label=f"📥 Download Rows {start_row} to {end_row} (.xlsx)",
                    data=excel_data,
                    file_name=f"Udyam_Data_{start_row}-{end_row}_{datetime.now().strftime('%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except ImportError:
                st.error("Install 'openpyxl' to enable downloads.")

    st.dataframe(
        df, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "S.No.": st.column_config.NumberColumn("S.No.", width="small"),
            "UDYAM NO.": st.column_config.TextColumn("UDYAM NO.", width="medium"),
            "PAN": st.column_config.TextColumn("PAN", width="small"),
            "Entity Name": st.column_config.TextColumn("Entity Name", width="large"),
            "Status": st.column_config.TextColumn("Status", validate="^Verified|Not Found$")
        }
    )


