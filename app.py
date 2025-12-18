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
    page_title="CMH1 Studio", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 2. CSS CLEAN (Sahl w Nqi) ---
st.markdown("""
<style>
    /* Background dyal l'App kamla */
    .stApp {
        background-color: #1a1b26;
    }
    
    /* Background dyal Sidebar */
    [data-testid="stSidebar"] {
        background-color: #16161e;
        border-right: 1px solid #2a2c3d;
    }
    
    /* Header (fin kayn ssem) ykon b nfs loun l'background */
    header[data-testid="stHeader"] {
        background-color: #1a1b26;
    }

    /* Nqssu mn l'padding lfoqani bach tla3 l'page chwya */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }

    /* Nbedlo loun d lktaba f sidebar bla man9iso l'icons */
    [data-testid="stSidebar"] .stMarkdown {
        color: #a9b1d6;
    }
    
    /* Iframe Style */
    iframe {
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR ---
st.sidebar.title("⚡ CMH1 STUDIO")
st.sidebar.markdown("---")

app_mode = st.sidebar.radio(
    "MENU",
    ["💻 HTML Fusion Editor", "📧 IMAP Email Tool"],
)

st.sidebar.markdown("---")

# ==========================================
# APP 1: HTML FUSION EDITOR
# ==========================================
if app_mode == "💻 HTML Fusion Editor":
    if os.path.exists("V6.html"):
        with open("V6.html", "r", encoding="utf-8") as f:
            html_code = f.read()
        # Height: 900px kafi bach ybqa s-scroll dakhli
        components.html(html_code, height=900, scrolling=True)
    else:
        st.error("⚠️ Malqinach fichier V6.html")

# ==========================================
# APP 2: IMAP EMAIL TOOL
# ==========================================
elif app_mode == "📧 IMAP Email Tool":
    
    # Functions
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
            st.error(f"❌ Error: {e}")
            return None

    # UI
    st.markdown("<h2 style='color:#e0e0e0;'>📧 IMAP EXTRACTOR</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("Login Credentials")
        email_user = st.text_input("Email")
        app_pass = st.text_input("App Password", type="password")
        
        if st.button("🔌 Connect", use_container_width=True):
            if email_user and app_pass:
                mail = connect_imap(email_user, app_pass)
                if mail:
                    st.session_state['mail_connected'] = True
                    st.success("OK")
                    mail.logout()
                else:
                    st.session_state['mail_connected'] = False
            else:
                st.warning("Enter details.")

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

                selected_folder = st.selectbox("Folder", clean_folders, index=clean_folders.index("INBOX") if "INBOX" in clean_folders else 0)
                
                with st.expander("Settings", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        max_results = st.number_input("Count", value=10)
                        rep_dom = st.checkbox("Change Domain")
                        p_from = st.text_input("New Domain", value="[P_FROM]") if rep_dom else "[P_FROM]"
                    with c2:
                        std_headers = st.checkbox("Std Headers")
                        clean_auth = st.checkbox("Clean Auth")
                        name_by_subj = st.checkbox("Name by Subject")
                    
                    custom_headers_text = st.text_area("Custom Headers (Key:Value)")

                if st.button("🚀 DOWNLOAD ZIP", type="primary", use_container_width=True):
                    # (Nfs Logic dyal extraction hna...)
                    mail.select(f'"{selected_folder}"', readonly=True)
                    typ, data = mail.search(None, 'ALL')
                    id_list = data[0].split()
                    id_list.reverse()
                    id_list = id_list[:max_results]
                    
                    if id_list:
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

                                    if clean_auth:
                                        for h in ['DKIM-Signature', 'Authentication-Results']:
                                            while h in mime: del mime[h]
                                    
                                    fin = mime.as_bytes() + b'\r\n\r\n' + body
                                    subj = mime.get('Subject', 'no_subject')
                                    fn = f"{i+1}_{clean_filename(subj)}.txt" if name_by_subj else f"email_{i+1}.txt"
                                    zf.writestr(fn, fin)
                                except: continue
                        
                        st.success("Done!")
                        st.download_button("💾 Save ZIP", zip_buf.getvalue(), "emails.zip", "application/zip")
                mail.logout()
