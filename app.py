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
    page_title="CMH1 Toolkit", 
    page_icon="🚀", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. CSS CLEAN (Design Nqi bla machakil) ---
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #1a1b26;
    }
    
    /* Sidebar Background */
    [data-testid="stSidebar"] {
        background-color: #16161e;
        border-right: 1px solid #2a2c3d;
    }
    
    /* Header Fix */
    header[data-testid="stHeader"] {
        background-color: #1a1b26;
    }

    /* Padding Adjustment */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }

    /* Sidebar Text Color */
    [data-testid="stSidebar"] .stMarkdown h1, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p {
        color: #a9b1d6 !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Iframe Style */
    iframe {
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Input Fields Style */
    .stTextInput input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #2a2c3d !important;
        color: white !important;
        border: 1px solid #414868 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("🚀 CMH1 TOOLKIT")
st.sidebar.markdown("---")

app_mode = st.sidebar.radio(
    "Select App:",
    ["💻 HTML Fusion Editor", "📧 IMAP Email Tool"],
)

st.sidebar.markdown("---")
st.sidebar.markdown("Developed by **@ayoubrhattoy**")

# ==========================================
# APP 1: HTML FUSION EDITOR
# ==========================================
if app_mode == "💻 HTML Fusion Editor":
    if os.path.exists("V6.html"):
        with open("V6.html", "r", encoding="utf-8") as f:
            html_code = f.read()
        components.html(html_code, height=900, scrolling=True)
    else:
        st.error("⚠️ Fichier 'V6.html' malqinahch!")

# ==========================================
# APP 2: IMAP EMAIL TOOL (TEXTE ORIGINAL)
# ==========================================
elif app_mode == "📧 IMAP Email Tool":
    
    # --- Functions ---
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

    # --- UI ---
    st.title("🚀 GMAIL/IMAP RAW TOOL")
    st.markdown("Developed by **@ayoubrhattoy**")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🔐 Login Credentials")
        email_user = st.text_input("👉 Email:", placeholder="example@gmail.com")
        app_pass = st.text_input("👉 App Password:", type="password")
        
        if st.button("🔌 Connect"):
            if email_user and app_pass:
                mail = connect_imap(email_user, app_pass)
                if mail:
                    st.session_state['mail_connected'] = True
                    st.success("✅ Connected!")
                    mail.logout()
                else:
                    st.session_state['mail_connected'] = False
            else:
                st.warning("Please enter credentials.")

    with col2:
        if st.session_state.get('mail_connected'):
            mail = connect_imap(email_user, app_pass)
            if mail:
                status, folders = mail.list()
                clean_folders = []
                for folder in folders:
                    folder_str = folder.decode()
                    match = re.search(r'"([^"]+)"$', folder_str) or re.search(r' ([^ ]+)$', folder_str)
                    if match: clean_folders.append(match.group(1))
                    else: clean_folders.append(folder_str)

                st.write("---")
                selected_folder = st.selectbox("📂 Select Folder", clean_folders, index=clean_folders.index("INBOX") if "INBOX" in clean_folders else 0)
                
                with st.expander("⚙️ SETTINGS (RAW BODY PRESERVATION)", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        max_results = st.number_input("1️⃣ Count? (10):", min_value=1, value=10)
                        rep_dom = st.checkbox("2️⃣ Change 'From' Domain? (y/n)")
                        p_from = st.text_input("   Tag [P_FROM]:", value="[P_FROM]") if rep_dom else "[P_FROM]"
                    with c2:
                        std_headers = st.checkbox("3️⃣ Set To=[*to], Date=[*date]? (y/n)")
                        mod_eid = st.checkbox("5️⃣ Add [EID] to Message-ID? (y/n)")
                        clean_auth = st.checkbox("6️⃣ Remove DKIM/SPF headers? (y/n)")
                        name_by_subj = st.checkbox("7️⃣ Name files by Subject? (y/n)")
                    
                    custom_headers_text = st.text_area("4️⃣ Custom Headers (Key:Value)")

                if st.button("🚀 START DOWNLOAD & PROCESS", type="primary"):
                    mail.select(f'"{selected_folder}"', readonly=True)
                    typ, data = mail.search(None, 'ALL')
                    id_list = data[0].split()
                    id_list.reverse()
                    id_list = id_list[:max_results]
                    
                    if not id_list:
                        st.error("📭 No emails found.")
                    else:
                        progress = st.progress(0)
                        zip_buf = io.BytesIO()
                        
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
                                    original_subject = mime.get('Subject', 'no_subject')

                                    if rep_dom and mime.get('From'):
                                        n_from = re.sub(r'@[a-zA-Z0-9.-]+', f'@{p_from}', mime['From'])
                                        del mime['From']; mime['From'] = n_from
                                    
                                    if std_headers:
                                        if 'To' in mime: del mime['To']
                                        mime['To'] = '[*to]'
                                        if 'Date' in mime: del mime['Date']
                                        mime['Date'] = '[*date]'
                                    
                                    if custom_headers_text:
                                        for l in custom_headers_text.split('\n'):
                                            if ":" in l:
                                                k, v = l.split(":", 1)
                                                if k.strip() in mime: del mime[k.strip()]
                                                mime[k.strip()] = v.strip()

                                    if mod_eid and mime.get('Message-ID') and '@' in mime['Message-ID']:
                                        new_mid = mime['Message-ID'].replace('@', '[EID]@', 1)
                                        del mime['Message-ID']; mime['Message-ID'] = new_mid

                                    if clean_auth:
                                        for h in ['DKIM-Signature', 'Authentication-Results', 'Received', 'Received-SPF', 'ARC-Authentication-Results', 'ARC-Message-Signature', 'ARC-Seal']:
                                            while h in mime: del mime[h]
                                    
                                    fin = mime.as_bytes() + b'\r\n\r\n' + body
                                    
                                    fname = f"email_{i+1}.txt"
                                    if name_by_subj:
                                        subj = clean_filename(original_subject)
                                        fname = f"{i+1}_{subj}.txt"

                                    zf.writestr(fname, fin)
                                    progress.progress((i+1)/len(id_list))
                                except: continue
                        
                        st.success("🎉 Download Complete!")
                        st.download_button("📥 Download ZIP File", zip_buf.getvalue(), "emails_raw_pack.zip", "application/zip")
                mail.logout()
