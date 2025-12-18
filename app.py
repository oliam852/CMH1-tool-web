import streamlit as st
import streamlit.components.v1 as components
import os
import re
import email
import imaplib
import zipfile
import io
from email.header import decode_header

# --- 1. CONFIGURATION PRO (Wide & Collapsed Sidebar option) ---
st.set_page_config(
    page_title="CMH1 Studio", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. CSS FOR PRO LOOK (Hada howa sirr d Design) ---
st.markdown("""
<style>
    /* Nqado l'background d page kamla */
    .stApp {
        background-color: #1a1b26; /* Nafs loun d Editor */
    }
    
    /* N7yydo l'padding lkbir d streamlit */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    
    /* Sidebar Design - Dark & Clean */
    [data-testid="stSidebar"] {
        background-color: #16161e; /* Darker than main */
        border-right: 1px solid #2a2c3d;
    }
    
    /* Sidebar Text Colors */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] label, [data-testid="stSidebar"] span {
        color: #a9b1d6 !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Radio Button Style */
    div[role="radiogroup"] > label > div:first-of-type {
        background-color: #2a2c3d !important;
    }
    div[role="radiogroup"] label {
         color: #c0caf5 !important;
    }

    /* Hide standard Streamlit header/footer/menu to look like a real app */
    header[data-testid="stHeader"] {
        visibility: hidden;
        height: 0px;
    }
    footer {
        visibility: hidden;
    }
    
    /* iframe styling */
    iframe {
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("⚡ CMH1 STUDIO")
st.sidebar.caption("Professional Toolkit v2.0")
st.sidebar.markdown("---")

# Khtiyarat b icones
app_mode = st.sidebar.radio(
    "NAVIGATION",
    ["💻 HTML Fusion Editor", "📧 IMAP Email Tool"],
    index=0 
)

st.sidebar.markdown("---")
# Status indicator style
st.sidebar.markdown("""
<div style='background-color: #1e1f2b; padding: 10px; border-radius: 5px; border: 1px solid #2a2c3d;'>
    <small style='color: #00f5c3;'>● System Online</small><br>
    <small style='color: #565f89;'>Dev: @ayoubrhattoy</small>
</div>
""", unsafe_allow_html=True)

# ==========================================
# APP 1: HTML FUSION EDITOR (Pro Mode)
# ==========================================
if app_mode == "💻 HTML Fusion Editor":
    # Ma ndiroch title 3adi, ndiroh b HTML bach yban integrated
    # Walakin bima anna l'Editor fih header aslan, nqdro n-integréwah direct blama ndiro title hna
    
    if os.path.exists("V6.html"):
        with open("V6.html", "r", encoding="utf-8") as f:
            html_code = f.read()
        
        # HNA FIN KAYN L'BLAN: Height kbira bach t3mmr chacha
        # Scrolling=True darouri, walakin m3a CSS lfoq maghaybanch lferq
        components.html(html_code, height=950, scrolling=True)
    else:
        st.error("⚠️ Fichier 'V6.html' ma kaynch!")

# ==========================================
# APP 2: IMAP EMAIL TOOL (Pro Mode)
# ==========================================
elif app_mode == "📧 IMAP Email Tool":
    
    # ... (Functions dyal IMAP bqaw homa homa) ...
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

    # UI Modern
    st.markdown("<h1 style='color: #e0e0e0;'>📧 IMAP EXTRACTOR</h1>", unsafe_allow_html=True)
    
    # Styled Container
    with st.container():
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("""
            <div style='background-color: #2a2c3d; padding: 15px; border-radius: 8px;'>
                <h3 style='color:white; margin-top:0;'>🔐 Credentials</h3>
            </div>
            """, unsafe_allow_html=True)
            st.write("") # Spacer
            email_user = st.text_input("Email Address", placeholder="user@gmail.com")
            app_pass = st.text_input("App Password", type="password")
            
            st.write("")
            if st.button("🔌 CONNECT SERVER", use_container_width=True):
                if not email_user or not app_pass:
                    st.warning("Please enter credentials.")
                else:
                    mail = connect_imap(email_user, app_pass)
                    if mail:
                        st.session_state['mail_connected'] = True
                        st.success("CONNECTED")
                        mail.logout()
                    else:
                        st.session_state['mail_connected'] = False

        with col2:
            if st.session_state.get('mail_connected'):
                st.markdown("""
                <div style='background-color: #1e1f2b; padding: 15px; border-radius: 8px; border: 1px solid #00f5c3;'>
                    <h3 style='color:#00f5c3; margin-top:0;'>🚀 Control Panel</h3>
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
                    selected_folder = st.selectbox("Target Folder", clean_folders, index=clean_folders.index("INBOX") if "INBOX" in clean_folders else 0)
                    
                    with st.expander("⚙️ FILTER & CONFIGURATION", expanded=True):
                        c1, c2 = st.columns(2)
                        with c1:
                            max_results = st.number_input("Limit Emails", min_value=1, value=10)
                            rep_dom = st.checkbox("Change Domain (@)")
                            p_from = st.text_input("New Domain", value="[P_FROM]") if rep_dom else "[P_FROM]"
                        with c2:
                            std_headers = st.checkbox("Mask Headers (To/Date)")
                            clean_auth = st.checkbox("Strip Auth (DKIM/SPF)")
                            name_by_subj = st.checkbox("Filename = Subject")
                        
                        custom_headers_text = st.text_area("Inject Custom Headers (Key:Value)", height=70)

                    if st.button("📥 START EXTRACTION PROCESS", type="primary", use_container_width=True):
                        mail.select(f'"{selected_folder}"', readonly=True)
                        typ, data = mail.search(None, 'ALL')
                        id_list = data[0].split()
                        id_list.reverse()
                        id_list = id_list[:max_results]
                        
                        if not id_list:
                            st.error("Folder is empty.")
                        else:
                            progress_bar = st.progress(0)
                            zip_buffer = io.BytesIO()
                            status_text = st.empty()
                            
                            with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                                for i, email_id in enumerate(id_list):
                                    status_text.text(f"Processing {i+1}/{len(id_list)}...")
                                    try:
                                        typ, msg_data = mail.fetch(email_id, '(RFC822)')
                                        raw_bytes = msg_data[0][1]
                                        
                                        # Split Header/Body
                                        separator = b'\r\n\r\n'
                                        split_index = raw_bytes.find(separator)
                                        if split_index == -1: 
                                            separator = b'\n\n'
                                            split_index = raw_bytes.find(separator)
                                        
                                        header_bytes = raw_bytes[:split_index] if split_index != -1 else raw_bytes
                                        body_bytes = raw_bytes[split_index + len(separator):] if split_index != -1 else b""
                                        
                                        mime_headers = email.message_from_bytes(header_bytes)
                                        original_subj = mime_headers.get('Subject', 'no_subject')

                                        # Transformations
                                        if rep_dom and mime_headers.get('From'):
                                            new_from = re.sub(r'@[a-zA-Z0-9.-]+', f'@{p_from}', mime_headers['From'])
                                            del mime_headers['From']; mime_headers['From'] = new_from
                                        
                                        if std_headers:
                                            if 'To' in mime_headers: del mime_headers['To']
                                            mime_headers['To'] = '[*to]'
                                            if 'Date' in mime_headers: del mime_headers['Date']
                                            mime_headers['Date'] = '[*date]'
                                        
                                        if custom_headers_text:
                                            for line in custom_headers_text.split('\n'):
                                                if ":" in line:
                                                    k, v = line.split(":", 1)
                                                    if k.strip() in mime_headers: del mime_headers[k.strip()]
                                                    mime_headers[k.strip()] = v.strip()
                                        
                                        if clean_auth:
                                            for h in ['DKIM-Signature', 'Authentication-Results', 'Received-SPF', 'ARC-Authentication-Results']:
                                                while h in mime_headers: del mime_headers[h]

                                        final_bytes = mime_headers.as_bytes() + b'\r\n\r\n' + body_bytes
                                        
                                        fname = f"{i+1}_{clean_filename(original_subj)}.txt" if name_by_subj else f"email_{i+1}.txt"
                                        zip_file.writestr(fname, final_bytes)
                                        progress_bar.progress((i + 1) / len(id_list))
                                    except: continue
                            
                            status_text.empty()
                            st.success("✅ Extraction Complete")
                            st.download_button("💾 DOWNLOAD ZIP ARCHIVE", zip_buffer.getvalue(), "emails_clean.zip", "application/zip", use_container_width=True)
                    mail.logout()
            else:
                 st.info("Waiting for connection...")
