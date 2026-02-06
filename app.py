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
    page_title="CMH1 Fusion Pro", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. LIGHTWEIGHT CSS (STABLE VERSION) ---
st.markdown("""
<style>
    /* Import Font */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    .stApp {
        background: linear-gradient(180deg, #0a0e27 0%, #121631 100%);
        font-family: 'JetBrains Mono', monospace;
    }
    
    /* Hide Sidebar */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* Tabs Container */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background: rgba(26, 31, 58, 0.8);
        padding: 12px 24px;
        border-radius: 16px;
        border: 1px solid rgba(168, 85, 247, 0.3);
    }

    /* Individual Tabs */
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background: rgba(18, 22, 49, 0.6);
        border-radius: 10px;
        color: #94a3b8;
        font-weight: 600;
        border: 1px solid rgba(168, 85, 247, 0.2);
        padding: 0 20px;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Selected Tab */
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #a855f7 0%, #3b82f6 100%) !important;
        color: #ffffff !important;
        font-weight: 700;
        border: 1px solid rgba(168, 85, 247, 0.5);
    }
    
    /* Hover Effect */
    .stTabs [data-baseweb="tab"]:hover {
        color: #a855f7;
        border-color: rgba(168, 85, 247, 0.4);
    }

    /* Remove Default Elements */
    [data-testid="stDecoration"] {
        display: none;
    }
    header {
        visibility: hidden;
    }
    
    /* Container Padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    /* Input Fields */
    .stTextInput input, 
    .stNumberInput input, 
    .stTextArea textarea,
    .stSelectbox > div > div {
        background-color: #121631 !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(168, 85, 247, 0.3) !important;
        border-radius: 8px !important;
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Labels */
    [data-testid="stWidgetLabel"] p,
    .stMarkdown p,
    .stMarkdown h1, 
    .stMarkdown h2, 
    .stMarkdown h3,
    .stCheckbox > label {
        color: #e2e8f0 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    /* Buttons */
    .stButton button {
        font-weight: 600;
        background: linear-gradient(135deg, #a855f7 0%, #3b82f6 100%);
        border: none;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-family: 'JetBrains Mono', monospace;
    }
    
    .stButton button:hover {
        opacity: 0.9;
    }
    
    /* Alert Boxes */
    .stAlert {
        background: rgba(18, 22, 49, 0.8) !important;
        border-left: 4px solid #a855f7 !important;
        color: #e2e8f0 !important;
        border-radius: 8px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(18, 22, 49, 0.6) !important;
        border: 1px solid rgba(168, 85, 247, 0.2) !important;
        border-radius: 8px;
        color: #e2e8f0 !important;
    }
    
</style>
""", unsafe_allow_html=True)

# --- 3. NAVIGATION ---
tab1, tab2, tab3 = st.tabs(["💻 HTML FUSION", "📧 IMAP TOOL", "⚡ CMH-1 PRO"])

# ==========================================
# TAB 1: HTML FUSION EDITOR
# ==========================================
with tab1:
    st.markdown("### 💻 HTML Fusion Editor")
    
    v6_paths = ["V6.html", "/app/V6.html", "./V6.html"]
    v6_found = False
    
    for path in v6_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    html_code = f.read()
                components.html(html_code, height=850, scrolling=True)
                v6_found = True
                break
            except Exception as e:
                st.error(f"Error: {e}")
    
    if not v6_found:
        st.warning("⚠️ V6.html not found")
        st.info("📁 Upload V6.html to app directory")

# ==========================================
# TAB 2: IMAP TOOL
# ==========================================
with tab2:
    # Helper Functions
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
    
    def clean_html_to_plain(html_content):
        clean = re.sub(r'<[^>]+>', ' ', html_content)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def get_email_body_text(msg_obj):
        body_text = ""
        if msg_obj.is_multipart():
            for part in msg_obj.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                if 'attachment' in cdispo: continue
                try:
                    payload = part.get_payload(decode=True)
                    if not payload: continue
                    decoded_payload = payload.decode('utf-8', 'ignore')
                    if ctype == 'text/plain': return decoded_payload
                    elif ctype == 'text/html': body_text = clean_html_to_plain(decoded_payload)
                except: continue
        else:
            try:
                payload = msg_obj.get_payload(decode=True)
                if payload:
                    decoded = payload.decode('utf-8', 'ignore')
                    if msg_obj.get_content_type() == 'text/html':
                         body_text = clean_html_to_plain(decoded)
                    else: body_text = decoded
            except: pass
        return body_text
    
    def detect_duplicates(email_list):
        import hashlib
        seen_ids = set()
        seen_hashes = set()
        duplicates = []
        unique_emails = []
        
        for idx, email_data in enumerate(email_list):
            msg_obj = email_data['msg']
            email_id = email_data['id']
            msg_id = msg_obj.get('Message-ID', '')
            
            if msg_id and msg_id in seen_ids:
                duplicates.append({
                    'index': idx + 1, 'id': email_id,
                    'reason': 'Same Message-ID',
                    'subject': msg_obj.get('Subject', 'No Subject')
                })
                continue
            
            subject = msg_obj.get('Subject', '')
            from_addr = msg_obj.get('From', '')
            date = msg_obj.get('Date', '')
            combo = f"{subject}|{from_addr}|{date}".encode('utf-8')
            hash_val = hashlib.md5(combo).hexdigest()
            
            if hash_val in seen_hashes:
                duplicates.append({
                    'index': idx + 1, 'id': email_id,
                    'reason': 'Same Subject+From+Date',
                    'subject': subject
                })
                continue
            
            if msg_id: seen_ids.add(msg_id)
            seen_hashes.add(hash_val)
            unique_emails.append(email_data)
        
        return unique_emails, duplicates

    def connect_imap(user, password):
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(user, password)
            return mail
        except Exception as e:
            st.error(f"❌ Login Error: {e}")
            return None

    # UI
    st.markdown("## 🚀 IMAP Email Tool")
    st.caption("by @ayoubrhattoy")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("🔐 Credentials")
        email_user = st.text_input("Email:", placeholder="user@gmail.com")
        app_pass = st.text_input("App Password:", type="password")
        
        if st.button("🔌 Connect", use_container_width=True):
            if email_user and app_pass:
                mail = connect_imap(email_user, app_pass)
                if mail:
                    st.session_state['mail_connected'] = True
                    st.success("✅ Connected!")
                    mail.logout()
            else:
                st.warning("Enter credentials")

    with col2:
        if st.session_state.get('mail_connected'):
            mail = connect_imap(email_user, app_pass)
            if mail:
                cache_key = f"folders_{email_user}"
                if cache_key not in st.session_state:
                    status, folders = mail.list()
                    clean_folders = []
                    for folder in folders:
                        folder_str = folder.decode()
                        match = re.search(r'"([^"]+)"$', folder_str) or re.search(r' ([^ ]+)$', folder_str)
                        if match: clean_folders.append(match.group(1))
                        else: clean_folders.append(folder_str)
                    st.session_state[cache_key] = clean_folders
                else:
                    clean_folders = st.session_state[cache_key]
                
                count_cache_key = f"counts_{email_user}"
                if count_cache_key not in st.session_state:
                    folder_counts = {}
                    for folder in clean_folders:
                        try:
                            mail.select(f'"{folder}"', readonly=True)
                            typ, data = mail.search(None, 'ALL')
                            count = len(data[0].split()) if typ == 'OK' and data[0] else 0
                            folder_counts[folder] = count
                        except: folder_counts[folder] = 0
                    st.session_state[count_cache_key] = folder_counts
                else:
                    folder_counts = st.session_state[count_cache_key]
                
                folder_options = [f"{f} ({folder_counts.get(f, 0)})" for f in clean_folders]
                selected_display = st.selectbox("📂 Folder", folder_options)
                selected_folder = clean_folders[folder_options.index(selected_display)]
                total_emails = folder_counts.get(selected_folder, 0)
                
                with st.expander("⚙️ Settings", expanded=True):
                    st.info(f"📊 Total: **{total_emails}** emails")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        start_from = st.number_input("Start #:", 1, max(1, total_emails), 1)
                    with c2:
                        download_count = st.number_input("Download:", 1, total_emails, min(10, total_emails))
                    
                    end_at = min(start_from + download_count - 1, total_emails)
                    st.caption(f"📌 Range: #{start_from} to #{end_at}")
                    
                    st.markdown("---")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        rep_dom = st.checkbox("Change From Domain")
                        p_from = st.text_input("Tag:", "[P_FROM]") if rep_dom else "[P_FROM]"
                        extract_plain_only = st.checkbox("Body Only")
                        export_format = "Merged"
                        if extract_plain_only:
                            export_format = st.radio("Format:", ["Merged", "Separate ZIP"])

                    with c2:
                        std_headers = st.checkbox("Set To/Date Tags")
                        mod_eid = st.checkbox("Add [EID]")
                        clean_auth = st.checkbox("Remove DKIM/SPF")
                        name_by_subj = st.checkbox("Name by Subject")
                        detect_dupes = st.checkbox("Remove Duplicates")
                    
                    custom_headers_text = st.text_area("Custom Headers:")

                if st.button("🚀 DOWNLOAD", type="primary", use_container_width=True):
                    mail.select(f'"{selected_folder}"', readonly=True)
                    typ, data = mail.search(None, 'ALL')
                    id_list = data[0].split()
                    id_list.reverse()
                    id_list = id_list[start_from-1:start_from-1+download_count]
                    
                    if id_list:
                        prog = st.progress(0)
                        
                        if detect_dupes:
                            email_data_list = []
                            for eid in id_list:
                                try:
                                    _, msg_data = mail.fetch(eid, '(RFC822)')
                                    email_data_list.append({
                                        'msg': email.message_from_bytes(msg_data[0][1]),
                                        'id': eid, 'raw': msg_data[0][1]
                                    })
                                except: pass
                            
                            unique_emails, duplicates = detect_duplicates(email_data_list)
                            if duplicates:
                                st.warning(f"⚠️ {len(duplicates)} duplicates removed")
                            id_list = [item['id'] for item in unique_emails]
                        
                        if extract_plain_only:
                            if "Merged" in export_format:
                                texts = []
                                for i, eid in enumerate(id_list):
                                    try:
                                        _, msg_data = mail.fetch(eid, '(RFC822)')
                                        msg = email.message_from_bytes(msg_data[0][1])
                                        body = get_email_body_text(msg)
                                        if body: texts.append(body)
                                        prog.progress((i+1)/len(id_list))
                                    except: pass
                                
                                prog.empty()
                                st.success(f"✅ {len(texts)} emails extracted")
                                st.download_button("📥 Download TXT", 
                                    "\n__SEP__\n".join(texts),
                                    "emails_merged.txt", "text/plain")
                            else:
                                zip_buf = io.BytesIO()
                                with zipfile.ZipFile(zip_buf, "w") as zf:
                                    for i, eid in enumerate(id_list):
                                        try:
                                            _, msg_data = mail.fetch(eid, '(RFC822)')
                                            msg = email.message_from_bytes(msg_data[0][1])
                                            body = get_email_body_text(msg)
                                            if body:
                                                fname = f"{i+1}_{clean_filename(msg.get('Subject', 'email'))}.txt" if name_by_subj else f"email_{i+1}.txt"
                                                zf.writestr(fname, body.encode('utf-8'))
                                            prog.progress((i+1)/len(id_list))
                                        except: pass
                                
                                prog.empty()
                                st.success("✅ Done")
                                st.download_button("📥 Download ZIP",
                                    zip_buf.getvalue(), "emails.zip", "application/zip")
                        else:
                            zip_buf = io.BytesIO()
                            with zipfile.ZipFile(zip_buf, "w") as zf:
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
                                            mime.replace_header('From', re.sub(r'@[a-zA-Z0-9.-]+', f'@{p_from}', mime['From']))
                                        
                                        if std_headers:
                                            if 'To' in mime: mime.replace_header('To', '[*to]')
                                            else: mime['To'] = '[*to]'
                                            if 'Date' in mime: mime.replace_header('Date', '[*date]')
                                            else: mime['Date'] = '[*date]'
                                        
                                        if custom_headers_text:
                                            for l in custom_headers_text.split('\n'):
                                                if ":" in l:
                                                    k, v = l.split(":", 1)
                                                    if k.strip() in mime: mime.replace_header(k.strip(), v.strip())
                                                    else: mime[k.strip()] = v.strip()

                                        if mod_eid and mime.get('Message-ID'):
                                            mime.replace_header('Message-ID', mime['Message-ID'].replace('@', '[EID]@', 1))

                                        if clean_auth:
                                            for h in ['DKIM-Signature', 'Authentication-Results', 'Received']:
                                                while h in mime: del mime[h]
                                        
                                        fname = f"{i+1}_{clean_filename(mime.get('Subject', 'email'))}.txt" if name_by_subj else f"email_{i+1}.txt"
                                        zf.writestr(fname, mime.as_bytes() + b'\r\n\r\n' + body)
                                        prog.progress((i+1)/len(id_list))
                                    except: pass
                            
                            prog.empty()
                            st.success("✅ Complete")
                            st.download_button("📥 Download ZIP", zip_buf.getvalue(), "emails.zip")
                    else:
                        st.error("No emails found")
                mail.logout()

# ==========================================
# TAB 3: CMH-1 PRO
# ==========================================
with tab3:
    st.markdown("### ⚡ CMH-1 Pro")
    
    cmh1_paths = [
        "cmh1-pro.html"
    ]
    
    found = False
    for path in cmh1_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    components.html(f.read(), height=850, scrolling=True)
                found = True
                break
            except Exception as e:
                st.error(f"Error: {e}")
    
    if not found:
        st.warning("⚠️ CMH-1 Pro not found")
        st.info("📁 Upload cmh1-pro.html")
