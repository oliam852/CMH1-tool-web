import streamlit as st
import streamlit.components.v1 as components
import os
import re
import email
import imaplib
import zipfile
import io
from email.header import decode_header

# --- 1. CONFIGURATION PAGE ---
st.set_page_config(page_title="CMH1 Toolkit", page_icon="🛠️", layout="wide")

# --- 2. SIDEBAR MENU (L'MOHIM) ---
st.sidebar.title("🚀 CMH1 TOOLKIT")
st.sidebar.markdown("---")
# Hna fin katkhter Application
app_mode = st.sidebar.radio("🔎 Khtar l'Application:", ["📧 IMAP Email Tool", "💻 HTML Fusion Editor"])
st.sidebar.markdown("---")
st.sidebar.markdown("Developed by **@ayoubrhattoy**")

# ==========================================
# APP 1: IMAP EMAIL TOOL
# ==========================================
if app_mode == "📧 IMAP Email Tool":
    
    # --- HELPER FUNCTIONS ---
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

    # --- UI IMAP ---
    st.title("📧 GMAIL/IMAP RAW TOOL")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("🔐 Login")
        email_user = st.text_input("Email", placeholder="example@gmail.com")
        app_pass = st.text_input("App Password", type="password")
        
        if st.button("🔌 Connect"):
            if not email_user or not app_pass:
                st.warning("3mmr l'email w password b3da!")
            else:
                mail = connect_imap(email_user, app_pass)
                if mail:
                    st.session_state['mail_connected'] = True
                    st.success("✅ Connected!")
                    mail.logout()
                else:
                    st.session_state['mail_connected'] = False

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

                selected_folder = st.selectbox("📂 Select Folder", clean_folders, index=clean_folders.index("INBOX") if "INBOX" in clean_folders else 0)
                
                with st.expander("⚙️ Advanced Settings", expanded=True):
                    c1, c2 = st.columns(2)
                    with c1:
                        max_results = st.number_input("Count", min_value=1, value=10)
                        rep_dom = st.checkbox("Change 'From' Domain?")
                        p_from = st.text_input("Tag Domain", value="[P_FROM]") if rep_dom else "[P_FROM]"
                    with c2:
                        std_headers = st.checkbox("Set To=[*to], Date=[*date]?")
                        clean_auth = st.checkbox("Remove DKIM/SPF headers?")
                        name_by_subj = st.checkbox("Name files by Subject?")
                    
                    custom_headers_text = st.text_area("Custom Headers (Key:Value)", height=70)

                if st.button("🚀 START DOWNLOAD", type="primary"):
                    mail.select(f'"{selected_folder}"', readonly=True)
                    typ, data = mail.search(None, 'ALL')
                    id_list = data[0].split()
                    id_list.reverse()
                    id_list = id_list[:max_results]
                    
                    if not id_list:
                        st.error("No emails found.")
                    else:
                        progress_bar = st.progress(0)
                        zip_buffer = io.BytesIO()
                        
                        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
                            for i, email_id in enumerate(id_list):
                                try:
                                    typ, msg_data = mail.fetch(email_id, '(RFC822)')
                                    raw_bytes = msg_data[0][1]
                                    
                                    separator = b'\r\n\r\n'
                                    split_index = raw_bytes.find(separator)
                                    if split_index == -1: 
                                        separator = b'\n\n'
                                        split_index = raw_bytes.find(separator)
                                    
                                    header_bytes = raw_bytes[:split_index] if split_index != -1 else raw_bytes
                                    body_bytes = raw_bytes[split_index + len(separator):] if split_index != -1 else b""
                                    
                                    mime_headers = email.message_from_bytes(header_bytes)
                                    original_subj = mime_headers.get('Subject', 'no_subject')

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
                                        for h in ['DKIM-Signature', 'Authentication-Results', 'Received-SPF']:
                                            while h in mime_headers: del mime_headers[h]

                                    final_bytes = mime_headers.as_bytes() + b'\r\n\r\n' + body_bytes
                                    
                                    fname = f"{i+1}_{clean_filename(original_subj)}.txt" if name_by_subj else f"email_{i+1}.txt"
                                    zip_file.writestr(fname, final_bytes)
                                    progress_bar.progress((i + 1) / len(id_list))
                                except: continue
                        
                        st.success("🎉 Done!")
                        st.download_button("📥 Download ZIP", zip_buffer.getvalue(), "emails_processed.zip", "application/zip")
                mail.logout()
        else:
             st.info("👈 Connecti b3da f jnb lissr.")

# ==========================================
# APP 2: HTML FUSION EDITOR
# ==========================================
elif app_mode == "💻 HTML Fusion Editor":
    st.title("💻 HTML Fusion Editor")
    
    # Hna fin kanqraw V6.html
    if os.path.exists("V6.html"):
        with open("V6.html", "r", encoding="utf-8") as f:
            html_code = f.read()
        components.html(html_code, height=1000, scrolling=True)
    else:
        st.error("⚠️ Fichier 'V6.html' ma kaynch f Repository GitHub!")
        st.info("3afak uploadé V6.html m3a app.py")
