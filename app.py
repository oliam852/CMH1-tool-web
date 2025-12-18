import streamlit as st
import streamlit.components.v1 as components
import os
import re
import email
import imaplib
import zipfile
import io
from email.header import decode_header

# --- 1. CONFIGURATION PRO ---
st.set_page_config(
    page_title="CMH1 Studio", 
    page_icon="⚡", 
    layout="wide", 
    initial_sidebar_state="expanded" # Hna golna lih ibda m7lol
)

# --- 2. CSS FOR PRO LOOK (Fixed Icons Issue) ---
st.markdown("""
<style>
    /* 1. Global Background */
    .stApp {
        background-color: #1a1b26;
    }
    
    /* 2. Fix Header - N7yydo decoration w nkhlliw background transparent */
    [data-testid="stDecoration"] {
        display: none;
    }
    header[data-testid="stHeader"] {
        background-color: #1a1b26 !important;
    }
    
    /* 3. HIDE TOOLBAR (Hada bach n7yydo 3 nuqat w Deploy li lfoq) */
    [data-testid="stToolbar"] {
        visibility: hidden;
    }
    .stDeployButton {
        display: none;
    }
    
    /* 4. Fix Padding - N9sso lfra3at */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    
    /* 5. Sidebar Design */
    [data-testid="stSidebar"] {
        background-color: #16161e;
        border-right: 1px solid #2a2c3d;
    }
    
    /* 6. Sidebar Text - HNA KAN LMOCHKIL: 7yyedna 'span' */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] label, [data-testid="stSidebar"] p {
        color: #a9b1d6 !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* 7. Fix Icons (Bach mayktbch lik keyboard...) */
    button span {
        font-family: 'Material Icons' !important; /* Kanferdo 3lih ybqa icone */
    }
    
    /* 8. Radio Button Style */
    div[role="radiogroup"] > label > div:first-of-type {
        background-color: #2a2c3d !important;
    }
    div[role="radiogroup"] label {
         color: #c0caf5 !important;
    }

    /* 9. Hide Footer */
    footer {
        visibility: hidden;
    }
    
    /* 10. Iframe Style */
    iframe {
        border-radius: 8px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("⚡ CMH1 STUDIO")
st.sidebar.markdown("---")

app_mode = st.sidebar.radio(
    "NAVIGATION",
    ["💻 HTML Fusion Editor", "📧 IMAP Email Tool"],
    index=0 
)

st.sidebar.markdown("---")
st.sidebar.info("System Online v2.1")

# ==========================================
# APP 1: HTML FUSION EDITOR
# ==========================================
if app_mode == "💻 HTML Fusion Editor":
    if os.path.exists("V6.html"):
        with open("V6.html", "r", encoding="utf-8") as f:
            html_code = f.read()
        # Height 900px bach tchad chacha
        components.html(html_code, height=900, scrolling=True)
    else:
        st.error("⚠️ Fichier 'V6.html' ma kaynch!")

# ==========================================
# APP 2: IMAP EMAIL TOOL
# ==========================================
elif app_mode == "📧 IMAP Email Tool":
    
    # ... Functions ...
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

    # UI Content
    st.markdown("<h2 style='color: #e0e0e0; margin-bottom: 20px;'>📧 IMAP EXTRACTOR PRO</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<div style='background-color: #2a2c3d; padding: 10px; border-radius: 5px; color: white; margin-bottom: 10px;'>🔐 Login</div>", unsafe_allow_html=True)
        email_user = st.text_input("Email", placeholder="user@gmail.com")
        app_pass = st.text_input("App Password", type="password")
        
        if st.button("🔌 CONNECT", use_container_width=True):
            if not email_user or not app_pass:
                st.warning("Enter credentials.")
            else:
                mail = connect_imap(email_user, app_pass)
                if mail:
                    st.session_state['mail_connected'] = True
                    st.success("Connected")
                    mail.logout()
                else:
                    st.session_state['mail_connected'] = False

    with col2:
        if st.session_state.get('mail_connected'):
            st.markdown("<div style='background-color: #1e1f2b; padding: 10px; border-radius: 5px; border: 1px solid #00f5c3; color: #00f5c3; margin-bottom: 10px;'>🚀 Operations</div>", unsafe_allow_html=True)
            
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
                
                with st.expander("⚙️ Settings", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        max_results = st.number_input("Count", min_value=1, value=10)
                        rep_dom = st.checkbox("Change Domain")
                        p_from = st.text_input("Domain", value="[P_FROM]") if rep_dom else "[P_FROM]"
                    with c2:
                        std_headers = st.checkbox("Standard Headers")
                        clean_auth = st.checkbox("Clean Auth")
                        name_by_subj = st.checkbox("Name by Subject")
                    
                    custom_headers_text = st.text_area("Headers (Key:Value)", height=60)

                if st.button("📥 DOWNLOAD EMAILS", type="primary", use_container_width=True):
                    mail.select(f'"{selected_folder}"', readonly=True)
                    typ, data = mail.search(None, 'ALL')
                    id_list = data[0].split()
                    id_list.reverse()
                    id_list = id_list[:max_results]
                    
                    if not id_list:
                        st.error("No emails.")
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
                                    subj = mime.get('Subject', 'no_subject')

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
                                        for h in ['DKIM-Signature', 'Authentication-Results', 'Received-SPF']:
                                            while h in mime: del mime[h]

                                    fin = mime.as_bytes() + b'\r\n\r\n' + body
                                    fn = f"{i+1}_{clean_filename(subj)}.txt" if name_by_subj else f"email_{i+1}.txt"
                                    zf.writestr(fn, fin)
                                    progress.progress((i+1)/len(id_list))
                                except: continue
                        
                        st.success("Done!")
                        st.download_button("💾 SAVE ZIP", zip_buf.getvalue(), "emails.zip", "application/zip", use_container_width=True)
                mail.logout()


