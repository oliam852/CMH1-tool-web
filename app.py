import streamlit as st
import streamlit.components.v1 as components
import os
import re
import email
import imaplib
import zipfile
import io
from email.header import decode_header

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="CMH1 Fusion", 
    page_icon="⚡", 
    layout="wide",
    initial_sidebar_state="collapsed" # Hna hbbtna sidebar
)

# --- 2. CSS FOR CUSTOM TABS & HIDING SIDEBAR ---
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #1a1b26;
    }
    
    /* 1. HIDE SIDEBAR COMPLETELY */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* 2. Custom Tabs Styling (Navigation Bar) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #16161e;
        padding: 10px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 8px;
        color: #565f89;
        font-weight: 600;
        border: none;
        padding: 0 20px;
    }

    /* Selected Tab Style */
    .stTabs [aria-selected="true"] {
        background-color: #00f5c3 !important;
        color: #1a1b26 !important;
        font-weight: bold;
    }
    
    /* Hover Effect */
    .stTabs [data-baseweb="tab"]:hover {
        color: #00f5c3;
    }

    /* Remove Top Decoration */
    [data-testid="stDecoration"] {
        display: none;
    }
    header {
        visibility: hidden;
    }
    
    /* Padding Adjustments */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }

    /* Inputs Styling */
    .stTextInput input, .stNumberInput input {
        background-color: #24283b !important;
        color: #c0caf5 !important;
        border: 1px solid #414868 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. NAVIGATION (TABS) ---
# Hada howa l-menu l-jdid li lfoq
tab1, tab2 = st.tabs(["💻 HTML FUSION EDITOR", "📧 IMAP EMAIL TOOL"])

# ==========================================
# TAB 1: HTML EDITOR
# ==========================================
with tab1:
    if os.path.exists("V6.html"):
        with open("V6.html", "r", encoding="utf-8") as f:
            html_code = f.read()
        # Height adjustment
        components.html(html_code, height=920, scrolling=True)
    else:
        st.error("⚠️ Fichier 'V6.html' ma kaynch f dossier!")

# ==========================================
# TAB 2: IMAP TOOL (Logic dialk nfsso)
# ==========================================
with tab2:
    # --- Helper Functions ---
    def decode_header_text(header_value):
        if not header_value: return "no_subject"
        try:
            decoded_list = decode_header(header_value)
            text_parts = []
            for content, encoding in decoded_list:
                if isinstance(content, bytes):
                    if encoding:
                        try: content = content.decode(encoding)
                        except: content = content.decode('utf-8', 'ignore')
                    else: content = content.decode('utf-8', 'ignore')
                text_parts.append(str(content))
            return "".join(text_parts)
        except: return header_value

    def clean_filename(subject):
        if not subject: return "no_subject"
        decoded_subj = decode_header_text(subject)
        clean = re.sub(r'[^a-zA-Z0-9\s_\-\u00C0-\u017F]', '', decoded_subj) 
        return clean.strip().replace(' ', '_')[:60]

    def connect_imap(user, password):
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(user, password)
            return mail
        except Exception as e:
            st.error(f"❌ Login Error: {e}")
            return None

    # UI IMAP
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2], gap="large")
    
    with col1:
        st.markdown("""
        <div style="background:#16161e; padding:15px; border-radius:10px; border-left:4px solid #00f5c3;">
            <h4 style="margin:0; color:white;">🔐 Access Credentials</h4>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        
        email_user = st.text_input("📧 Email Address")
        app_pass = st.text_input("🔑 App Password", type="password")
        
        st.write("")
        if st.button("🔌 CONNECT SERVER", use_container_width=True):
            if email_user and app_pass:
                mail = connect_imap(email_user, app_pass)
                if mail:
                    st.session_state['mail_connected'] = True
                    st.success("SUCCESSFULLY CONNECTED")
                    mail.logout()
                else:
                    st.session_state['mail_connected'] = False
            else:
                st.warning("Please check your input.")

    with col2:
        if st.session_state.get('mail_connected'):
            st.markdown("""
            <div style="background:#16161e; padding:15px; border-radius:10px; border-left:4px solid #7aa2f7;">
                <h4 style="margin:0; color:white;">⚙️ Configuration & Filters</h4>
            </div>
            """, unsafe_allow_html=True)
            
            mail = connect_imap(email_user, app_pass)
            if mail:
                status, folders = mail.list()
                clean_folders = []
                for folder in folders:
                    folder_str = folder.decode()
                    match = re.search(r'"([^"]+)"$', folder_str) or re.search(r' ([^ ]+)$', folder_str)
                    if match: clean_folders.append(match.group(1))
                    else: clean_folders.append(folder_str)

                st.write("")
                selected_folder = st.selectbox("📂 Select Folder", clean_folders, index=clean_folders.index("INBOX") if "INBOX" in clean_folders else 0)
                
                with st.expander("🛠️ ADVANCED OPTIONS", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        max_results = st.number_input("Count Limit", value=10, min_value=1)
                        rep_dom = st.checkbox("Change Domain")
                        p_from = st.text_input("Domain Tag", value="[P_FROM]") if rep_dom else "[P_FROM]"
                    with c2:
                        std_headers = st.checkbox("Standard Headers")
                        clean_auth = st.checkbox("Clean Authentication")
                        name_by_subj = st.checkbox("Filename as Subject")
                    
                    custom_headers_text = st.text_area("Custom Headers (Key:Value)")

                st.markdown("<hr style='border-color: #2a2c3d;'>", unsafe_allow_html=True)
                
                if st.button("🚀 LAUNCH EXTRACTION", type="primary", use_container_width=True):
                    # --- CORE LOGIC ---
                    mail.select(f'"{selected_folder}"', readonly=True)
                    typ, data = mail.search(None, 'ALL')
                    id_list = data[0].split()
                    id_list.reverse()
                    id_list = id_list[:max_results]
                    
                    if id_list:
                        zip_buf = io.BytesIO()
                        status_msg = st.empty()
                        prog_bar = st.progress(0)
                        
                        with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
                            for i, eid in enumerate(id_list):
                                try:
                                    _, msg = mail.fetch(eid, '(RFC822)')
                                    raw = msg[0][1]
                                    
                                    sep = b'\r\n\r\n'
                                    idx = raw.find(sep)
                                    if idx == -1: 
                                        sep = b'\n\n'
                                        idx = raw.find(sep)
                                    
                                    head = raw[:idx] if idx != -1 else raw
                                    body = raw[idx+len(sep):] if idx != -1 else b""
                                    
                                    mime = email.message_from_bytes(head)
                                    subj = mime.get('Subject', 'no_subject')

                                    # Filters
                                    if rep_dom and mime.get('From'):
                                        n_from = re.sub(r'@[a-zA-Z0-9.-]+', f'@{p_from}', mime['From'])
                                        del mime['From']; mime['From'] = n_from
                                    
                                    if std_headers:
                                        if 'To' in mime: del mime['To']
                                        mime['To'] = '[*to]'
                                        if 'Date' in mime: del mime['Date']
                                        mime['Date'] = '[*date]'
                                    
                                    if clean_auth:
                                        for h in ['DKIM-Signature', 'Authentication-Results']:
                                            while h in mime: del mime[h]
                                    
                                    if custom_headers_text:
                                        for l in custom_headers_text.split('\n'):
                                            if ":" in l:
                                                k, v = l.split(":", 1)
                                                if k.strip() in mime: del mime[k.strip()]
                                                mime[k.strip()] = v.strip()

                                    fin = mime.as_bytes() + b'\r\n\r\n' + body
                                    fn = f"{i+1}_{clean_filename(subj)}.txt" if name_by_subj else f"email_{i+1}.txt"
                                    zf.writestr(fn, fin)
                                    prog_bar.progress((i+1)/len(id_list))
                                except: continue
                        
                        prog_bar.empty()
                        status_msg.success("Extraction Completed!")
                        st.download_button("💾 DOWNLOAD ZIP ARCHIVE", zip_buf.getvalue(), "emails_pack.zip", "application/zip", use_container_width=True)
                mail.logout()
