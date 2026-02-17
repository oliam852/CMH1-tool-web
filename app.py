import streamlit as st
import streamlit.components.v1 as components
import os
import re
import email
import imaplib
import zipfile
import io
import json
import base64
from email.header import decode_header

# ========== COOKIE-BASED SESSION (خاصة بكل متصفح) ==========
try:
    from streamlit_cookies_controller import CookieController
    cookie_ctrl = CookieController()
    COOKIES_OK = True
except:
    COOKIES_OK = False

def save_session(email_addr, password):
    try:
        if COOKIES_OK:
            encoded = base64.b64encode(f"{email_addr}|||{password}".encode()).decode()
            cookie_ctrl.set("imap_sess", encoded)
        if os.path.exists('.email_session.dat'):
            os.remove('.email_session.dat')
    except:
        pass

def load_session():
    try:
        if COOKIES_OK:
            encoded = cookie_ctrl.get("imap_sess")
            if encoded:
                decoded = base64.b64decode(encoded).decode()
                email_addr, password = decoded.split('|||')
                return {'email': email_addr, 'password': password}
    except:
        pass
    return None

def clear_session():
    try:
        if COOKIES_OK:
            cookie_ctrl.remove("imap_sess")
        if os.path.exists('.email_session.dat'):
            os.remove('.email_session.dat')
    except:
        pass

st.set_page_config(page_title="CMH1 Fusion", page_icon="🚀", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #1a1b26; }
    [data-testid="stSidebar"] { display: none; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px; background-color: #565F89;
        padding: 10px 20px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: transparent;
        border-radius: 8px; color: #919499;
        font-weight: 600; border: none; padding: 0 20px;
    }
    label { color: #D3D6E4 !important; }
    .stTabs [aria-selected="true"] { background-color: #00f5c3 !important; color: #1a1b26 !important; font-weight: bold; }
    .stTabs [data-baseweb="tab"]:hover { color: #00f5c3; }
    [data-testid="stDecoration"] { display: none; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background-color: #24283b !important; color: #c0caf5 !important; border: 1px solid #414868 !important;
    }
    [data-testid="stWidgetLabel"] p { color: #c0caf5 !important; }
    .stMarkdown p { color: #c0caf5 !important; }
    .stButton button { font-weight: bold; }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["💻 HTML FUSION EDITOR", "📧 IMAP EMAIL TOOL", "⚡ CMH-1 PRO"])

with tab1:
    if os.path.exists("V6.html"):
        with open("V6.html", "r", encoding="utf-8") as f:
            html_code = f.read()
        components.html(html_code, height=920, scrolling=True)
    else:
        st.error("⚠️ Fichier 'V6.html' ma kaynch!")

with tab2:
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
                    if msg_obj.get_content_type() == 'text/html': body_text = clean_html_to_plain(decoded)
                    else: body_text = decoded
            except: pass
        return body_text
    
    def detect_duplicates(email_list):
        import hashlib
        seen_ids = set(); seen_hashes = set(); duplicates = []; unique_emails = []
        for idx, email_data in enumerate(email_list):
            msg_obj = email_data['msg']; email_id = email_data['id']
            msg_id = msg_obj.get('Message-ID', '')
            if msg_id and msg_id in seen_ids:
                duplicates.append({'index': idx+1, 'id': email_id, 'reason': 'Same Message-ID', 'subject': msg_obj.get('Subject', 'No Subject')}); continue
            subject = msg_obj.get('Subject', ''); from_addr = msg_obj.get('From', ''); date = msg_obj.get('Date', '')
            combo = f"{subject}|{from_addr}|{date}".encode('utf-8')
            hash_val = hashlib.md5(combo).hexdigest()
            if hash_val in seen_hashes:
                duplicates.append({'index': idx+1, 'id': email_id, 'reason': 'Same Subject+From+Date', 'subject': subject}); continue
            if msg_id: seen_ids.add(msg_id)
            seen_hashes.add(hash_val); unique_emails.append(email_data)
        return unique_emails, duplicates

    def connect_imap(user, password):
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(user, password)
            return mail
        except Exception as e:
            st.error(f"❌ Login Error: {e}")
            return None

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## 🚀 GMAIL/IMAP RAW TOOL")
    st.markdown("Developed by **@ayoubrhattoy**")
    
    if 'mail_connected' not in st.session_state:
        saved = load_session()
        if saved:
            mail = connect_imap(saved['email'], saved['password'])
            if mail:
                st.session_state['mail_connected'] = True
                st.session_state['saved_email'] = saved['email']
                st.session_state['saved_password'] = saved['password']
                mail.logout()
    
    col1, col2 = st.columns([1, 2], gap="large")
    
    with col1:
        if st.session_state.get('mail_connected'):
            st.success(f"✅ Connected: {st.session_state.get('saved_email', 'Unknown')}")
            if st.button("🔌 Disconnect", type="secondary", use_container_width=True):
                st.session_state['mail_connected'] = False
                clear_session()
                if 'saved_email' in st.session_state: del st.session_state['saved_email']
                if 'saved_password' in st.session_state: del st.session_state['saved_password']
                for key in list(st.session_state.keys()):
                    if key.startswith('folders_') or key.startswith('counts_'): del st.session_state[key]
                st.rerun()
        else:
            st.info("🔐 Login Credentials")
            email_user = st.text_input("👉 Email:", placeholder="example@gmail.com")
            app_pass = st.text_input("👉 App Password:", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔌 Connect", use_container_width=True):
                if email_user and app_pass:
                    mail = connect_imap(email_user, app_pass)
                    if mail:
                        st.session_state['mail_connected'] = True
                        st.session_state['saved_email'] = email_user
                        st.session_state['saved_password'] = app_pass
                        save_session(email_user, app_pass)
                        st.success("✅ Connected!")
                        mail.logout()
                        st.rerun()
                    else:
                        st.session_state['mail_connected'] = False
                else:
                    st.warning("Please enter credentials.")

    with col2:
        if st.session_state.get('mail_connected'):
            email_user = st.session_state.get('saved_email')
            app_pass = st.session_state.get('saved_password')
            mail = connect_imap(email_user, app_pass)
            if mail:
                cache_key = f"folders_{email_user}"
                if cache_key not in st.session_state or st.session_state.get('refresh_folders'):
                    status, folders = mail.list()
                    clean_folders = []
                    for folder in folders:
                        folder_str = folder.decode()
                        match = re.search(r'"([^"]+)"$', folder_str) or re.search(r' ([^ ]+)$', folder_str)
                        if match: clean_folders.append(match.group(1))
                        else: clean_folders.append(folder_str)
                    st.session_state[cache_key] = clean_folders
                    st.session_state['refresh_folders'] = False
                else:
                    clean_folders = st.session_state[cache_key]
                
                if st.button("🔄 Refresh Folders", help="Update folder list"):
                    st.session_state['refresh_folders'] = True
                    st.session_state['refresh_counts'] = True
                    st.rerun()

                count_cache_key = f"counts_{email_user}_{selected_folder if 'selected_folder' in locals() else 'all'}"
                if count_cache_key not in st.session_state or st.session_state.get('refresh_counts'):
                    folder_counts = {}
                    with st.spinner("📊 Counting emails..."):
                        for folder in clean_folders:
                            try:
                                mail.select(f'"{folder}"', readonly=True)
                                typ, data = mail.search(None, 'ALL')
                                if typ == 'OK':
                                    count = len(data[0].split()) if data[0] else 0
                                    folder_counts[folder] = count
                            except: folder_counts[folder] = 0
                    st.session_state[count_cache_key] = folder_counts
                    st.session_state['refresh_counts'] = False
                else:
                    folder_counts = st.session_state[count_cache_key]
                
                folder_options = [f"{folder} ({folder_counts.get(folder, 0)} emails)" for folder in clean_folders]
                selected_display = st.selectbox("📂 Select Folder", folder_options,
                    index=next((i for i, f in enumerate(clean_folders) if f == "INBOX"), 0))
                selected_folder = clean_folders[folder_options.index(selected_display)]
                total_emails = folder_counts.get(selected_folder, 0)
                
                with st.expander("⚙️ SETTINGS (RAW BODY PRESERVATION)", expanded=True):
                    st.info(f"📊 Total emails in folder: **{total_emails}**")
                    col_range1, col_range2 = st.columns(2)
                    with col_range1:
                        start_from = st.number_input("🔢 Start from email #:", min_value=1, max_value=max(1, total_emails), value=1, help="Start downloading from this email number (1 = newest)")
                    with col_range2:
                        download_count = st.number_input("📥 How many to download:", min_value=1, max_value=max(1, total_emails), value=min(10, max(1, total_emails)), help="Number of emails to download starting from above number")
                    end_at = min(start_from + download_count - 1, total_emails)
                    if total_emails > 0: st.caption(f"📌 Will download: Email #{start_from} to #{end_at} ({end_at - start_from + 1} emails)")
                    else: st.caption("⚠️ No emails available in this folder")
                    st.markdown("---")
                    c1, c2 = st.columns(2)
                    with c1:
                        rep_dom = st.checkbox("2️⃣ Change 'From' Domain")
                        p_from = st.text_input("   Tag [P_FROM]:", value="[P_FROM]") if rep_dom else "[P_FROM]"
                        st.markdown("---")
                        extract_plain_only = st.checkbox("8️⃣ Extract Body Only?", help="Extract only email body text without headers")
                        export_format = "Merged"
                        if extract_plain_only:
                            export_format = st.radio("📤 Export Format:", options=["Merged (1 file with __SEP__)", "Separate files (ZIP)"], horizontal=True)
                    with c2:
                        std_headers = st.checkbox("3️⃣ Set To=[*to], Date=[*date]")
                        mod_eid = st.checkbox("5️⃣ Add [EID] to Message-ID")
                        clean_auth = st.checkbox("6️⃣ Remove DKIM/SPF headers")
                        name_by_subj = st.checkbox("7️⃣ Name files by Subject")
                        st.markdown("---")
                        detect_dupes = st.checkbox("9️⃣ Remove Duplicates", help="Skip duplicate emails based on Message-ID and Subject+From+Date")
                    custom_headers_text = st.text_area("4️⃣ Custom Headers (Key:Value)")

                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("🚀 START DOWNLOAD & PROCESS", type="primary", use_container_width=True):
                    mail.select(f'"{selected_folder}"', readonly=True)
                    typ, data = mail.search(None, 'ALL')
                    id_list = data[0].split()
                    id_list.reverse()
                    id_list = id_list[start_from-1:start_from-1+download_count]
                    
                    if not id_list:
                        st.error("📭 No emails found in selected range.")
                    else:
                        status_msg = st.empty()
                        prog_bar = st.progress(0)
                        
                        if detect_dupes:
                            status_msg.info("🔍 Detecting duplicates...")
                            email_data_list = []
                            for i, eid in enumerate(id_list):
                                try:
                                    _, msg_data = mail.fetch(eid, '(RFC822)')
                                    raw_bytes = msg_data[0][1]
                                    email_message = email.message_from_bytes(raw_bytes)
                                    email_data_list.append({'msg': email_message, 'id': eid, 'raw': raw_bytes})
                                except: continue
                            unique_emails, duplicates = detect_duplicates(email_data_list)
                            if duplicates:
                                status_msg.warning(f"⚠️ Found {len(duplicates)} duplicate(s). Processing {len(unique_emails)} unique emails.")
                                with st.expander(f"📋 View {len(duplicates)} Duplicates"):
                                    for dup in duplicates[:20]:
                                        st.caption(f"Email #{dup['index']}: {dup['subject'][:50]} - {dup['reason']}")
                                    if len(duplicates) > 20: st.caption(f"... and {len(duplicates)-20} more")
                            else:
                                status_msg.success("✅ No duplicates found!")
                            id_list = [item['id'] for item in unique_emails]
                            if not id_list:
                                st.error("📭 All emails were duplicates!")
                                mail.logout()
                                st.stop()
                        
                        if extract_plain_only:
                            if "Merged" in export_format:
                                full_extracted_text = []
                                for i, eid in enumerate(id_list):
                                    try:
                                        _, msg_data = mail.fetch(eid, '(RFC822)')
                                        raw_bytes = msg_data[0][1]
                                        email_message = email.message_from_bytes(raw_bytes)
                                        body_content = get_email_body_text(email_message)
                                        if body_content: full_extracted_text.append(body_content)
                                        prog_bar.progress((i+1)/len(id_list))
                                    except: continue
                                final_output = "\n__SEP__\n".join(full_extracted_text)
                                prog_bar.empty()
                                status_msg.success(f"🎉 Extracted {len(full_extracted_text)} emails into 1 merged file!")
                                st.download_button(label="📥 Download Merged Text File (.txt)", data=final_output, file_name="emails_bodies_merged.txt", mime="text/plain")
                            else:
                                zip_buf = io.BytesIO()
                                with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
                                    for i, eid in enumerate(id_list):
                                        try:
                                            _, msg_data = mail.fetch(eid, '(RFC822)')
                                            raw_bytes = msg_data[0][1]
                                            email_message = email.message_from_bytes(raw_bytes)
                                            body_content = get_email_body_text(email_message)
                                            if body_content:
                                                if name_by_subj:
                                                    original_subj = email_message.get('Subject', 'no_subject')
                                                    subj = clean_filename(original_subj)
                                                    fname = f"{i+1}_{subj}.txt"
                                                else:
                                                    fname = f"email_{i+1}.txt"
                                                zf.writestr(fname, body_content.encode('utf-8'))
                                            prog_bar.progress((i+1)/len(id_list))
                                        except: continue
                                prog_bar.empty()
                                status_msg.success(f"🎉 Extracted {len(id_list)} emails into separate files!")
                                st.download_button(label="📥 Download ZIP File (Separate Text Files)", data=zip_buf.getvalue(), file_name="emails_bodies_separate.zip", mime="application/zip", use_container_width=True)
                        else:
                            zip_buf = io.BytesIO()
                            with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
                                for i, eid in enumerate(id_list):
                                    try:
                                        _, msg = mail.fetch(eid, '(RFC822)')
                                        raw = msg[0][1]
                                        sep = b'\r\n\r\n'
                                        idx = raw.find(sep)
                                        if idx == -1: sep = b'\n\n'; idx = raw.find(sep)
                                        head = raw[:idx] if idx != -1 else raw
                                        body = raw[idx+len(sep):] if idx != -1 else b""
                                        mime_msg = email.message_from_bytes(head)
                                        original_subj = mime_msg.get('Subject', 'no_subject')
                                        if rep_dom and mime_msg.get('From'):
                                            n_from = re.sub(r'@[a-zA-Z0-9.-]+', f'@{p_from}', mime_msg['From'])
                                            del mime_msg['From']; mime_msg['From'] = n_from
                                        if std_headers:
                                            if 'To' in mime_msg: del mime_msg['To']
                                            mime_msg['To'] = '[*to]'
                                            if 'Date' in mime_msg: del mime_msg['Date']
                                            mime_msg['Date'] = '[*date]'
                                        if custom_headers_text:
                                            for l in custom_headers_text.split('\n'):
                                                if ":" in l:
                                                    k, v = l.split(":", 1)
                                                    if k.strip() in mime_msg: del mime_msg[k.strip()]
                                                    mime_msg[k.strip()] = v.strip()
                                        if mod_eid and mime_msg.get('Message-ID') and '@' in mime_msg['Message-ID']:
                                            new_mid = mime_msg['Message-ID'].replace('@', '[EID]@', 1)
                                            del mime_msg['Message-ID']; mime_msg['Message-ID'] = new_mid
                                        if clean_auth:
                                            for h in ['DKIM-Signature', 'Authentication-Results', 'Received', 'Received-SPF', 'ARC-Authentication-Results', 'ARC-Message-Signature', 'ARC-Seal']:
                                                while h in mime_msg: del mime_msg[h]
                                        fin = mime_msg.as_bytes() + b'\r\n\r\n' + body
                                        fname = f"email_{i+1}.txt"
                                        if name_by_subj:
                                            subj = clean_filename(original_subj)
                                            fname = f"{i+1}_{subj}.txt"
                                        zf.writestr(fname, fin)
                                        prog_bar.progress((i+1)/len(id_list))
                                    except: continue
                            prog_bar.empty()
                            status_msg.success("🎉 Download Complete!")
                            st.download_button("📥 Download ZIP File", zip_buf.getvalue(), "emails_raw_pack.zip", "application/zip", use_container_width=True)
                        
                        st.session_state['refresh_counts'] = True
                mail.logout()

with tab3:
    cmh1_html_path = "cmh1-pro.html"
    if os.path.exists(cmh1_html_path):
        with open(cmh1_html_path, "r", encoding="utf-8") as f:
            cmh1_html_code = f.read()
        components.html(cmh1_html_code, height=920, scrolling=True)
    else:
        st.error("⚠️ Fichier 'cmh1-pro.html' ma kaynch!")
