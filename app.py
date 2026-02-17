import streamlit as st
import streamlit.components.v1 as components
import os
import re
import email
import imaplib
import zipfile
import io
import base64
from email.header import decode_header

# ==========================================
# ⚠️ COOKIES - يخص يكون قبل أي st. call
# ==========================================
from streamlit_cookies_controller import CookieController
controller = CookieController()

def save_session(email_addr, password):
    encoded = base64.b64encode(f"{email_addr}|||{password}".encode()).decode()
    controller.set("imap_sess", encoded)
    if os.path.exists('.email_session.dat'):
        try: os.remove('.email_session.dat')
        except: pass

def load_session():
    try:
        val = controller.get("imap_sess")
        if val:
            decoded = base64.b64decode(val).decode()
            email_addr, password = decoded.split('|||')
            return {'email': email_addr, 'password': password}
    except: pass
    # migration من الملف القديم
    if os.path.exists('.email_session.dat'):
        try:
            with open('.email_session.dat', 'r') as f:
                encoded = f.read()
            decoded = base64.b64decode(encoded).decode()
            email_addr, password = decoded.split('|||')
            os.remove('.email_session.dat')
            return {'email': email_addr, 'password': password}
        except: pass
    return None

def clear_session():
    try: controller.remove("imap_sess")
    except: pass
    if os.path.exists('.email_session.dat'):
        try: os.remove('.email_session.dat')
        except: pass

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="CMH1 Fusion",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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
    .stTabs [aria-selected="true"] {
        background-color: #00f5c3 !important;
        color: #1a1b26 !important; font-weight: bold;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #00f5c3; }
    [data-testid="stDecoration"] { display: none; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background-color: #24283b !important;
        color: #c0caf5 !important;
        border: 1px solid #414868 !important;
    }
    [data-testid="stWidgetLabel"] p { color: #c0caf5 !important; }
    .stMarkdown p { color: #c0caf5 !important; }
    .stButton button { font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# AUTO-LOGIN LOGIC (Double-Rerun Pattern)
# ==========================================
# على Streamlit Cloud، الـ cookies كتتحمل async
# في أول render كترجع None، في الثاني كترجع القيمة
# الحل: نعملو rerun وحدة إذا ما زال ما جربناش

def connect_imap(user, password):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        return mail
    except Exception as e:
        st.error(f"❌ Login Error: {e}")
        return None

if 'mail_connected' not in st.session_state:
    st.session_state['mail_connected'] = False
    st.session_state['_cookie_checked'] = False

# الـ cookie check - مرتان باش نضمن
if not st.session_state['mail_connected'] and not st.session_state['_cookie_checked']:
    st.session_state['_cookie_checked'] = True
    saved = load_session()
    if saved:
        mail_test = connect_imap(saved['email'], saved['password'])
        if mail_test:
            st.session_state['mail_connected'] = True
            st.session_state['saved_email'] = saved['email']
            st.session_state['saved_password'] = saved['password']
            mail_test.logout()
    else:
        # أول render، الـ cookie ما تحملتش بعد - نعاودو مرة
        st.rerun()

elif not st.session_state['mail_connected'] and st.session_state['_cookie_checked']:
    # المرة الثانية - نجربو مرة أخيرة
    if not st.session_state.get('_cookie_checked_twice'):
        st.session_state['_cookie_checked_twice'] = True
        saved = load_session()
        if saved:
            mail_test = connect_imap(saved['email'], saved['password'])
            if mail_test:
                st.session_state['mail_connected'] = True
                st.session_state['saved_email'] = saved['email']
                st.session_state['saved_password'] = saved['password']
                mail_test.logout()
                st.rerun()

# ==========================================
# TABS
# ==========================================
tab1, tab2, tab3 = st.tabs(["💻 HTML FUSION EDITOR", "📧 IMAP EMAIL TOOL", "⚡ CMH-1 PRO"])

with tab1:
    if os.path.exists("V6.html"):
        with open("V6.html", "r", encoding="utf-8") as f:
            components.html(f.read(), height=920, scrolling=True)
    else:
        st.error("⚠️ Fichier 'V6.html' ma kaynch!")

# ==========================================
# TAB 2
# ==========================================
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
        return re.sub(r'\s+', ' ', clean).strip()

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
                    body_text = clean_html_to_plain(decoded) if msg_obj.get_content_type() == 'text/html' else decoded
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
            hash_val = hashlib.md5(f"{msg_obj.get('Subject','')}|{msg_obj.get('From','')}|{msg_obj.get('Date','')}".encode()).hexdigest()
            if hash_val in seen_hashes:
                duplicates.append({'index': idx+1, 'id': email_id, 'reason': 'Same Subject+From+Date', 'subject': msg_obj.get('Subject','')}); continue
            if msg_id: seen_ids.add(msg_id)
            seen_hashes.add(hash_val); unique_emails.append(email_data)
        return unique_emails, duplicates

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## 🚀 GMAIL/IMAP RAW TOOL")
    st.markdown("Developed by **@ayoubrhattoy**")

    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        if st.session_state.get('mail_connected'):
            st.success(f"✅ Connected: {st.session_state.get('saved_email', 'Unknown')}")
            if st.button("🔌 Disconnect", type="secondary", use_container_width=True):
                clear_session()
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()
        else:
            st.info("🔐 Login Credentials")
            email_user = st.text_input("👉 Email:", placeholder="example@gmail.com")
            app_pass = st.text_input("👉 App Password:", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔌 Connect", use_container_width=True):
                if email_user and app_pass:
                    mail_conn = connect_imap(email_user, app_pass)
                    if mail_conn:
                        st.session_state['mail_connected'] = True
                        st.session_state['saved_email'] = email_user
                        st.session_state['saved_password'] = app_pass
                        st.session_state['_cookie_checked'] = True
                        st.session_state['_cookie_checked_twice'] = True
                        save_session(email_user, app_pass)
                        st.success("✅ Connected!")
                        mail_conn.logout()
                        st.rerun()
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
                        clean_folders.append(match.group(1) if match else folder_str)
                    st.session_state[cache_key] = clean_folders
                    st.session_state['refresh_folders'] = False
                else:
                    clean_folders = st.session_state[cache_key]

                if st.button("🔄 Refresh Folders"):
                    st.session_state['refresh_folders'] = True
                    st.session_state['refresh_counts'] = True
                    st.rerun()

                count_cache_key = f"counts_{email_user}_all"
                if count_cache_key not in st.session_state or st.session_state.get('refresh_counts'):
                    folder_counts = {}
                    with st.spinner("📊 Counting emails..."):
                        for folder in clean_folders:
                            try:
                                mail.select(f'"{folder}"', readonly=True)
                                typ, data = mail.search(None, 'ALL')
                                folder_counts[folder] = len(data[0].split()) if typ == 'OK' and data[0] else 0
                            except: folder_counts[folder] = 0
                    st.session_state[count_cache_key] = folder_counts
                    st.session_state['refresh_counts'] = False
                else:
                    folder_counts = st.session_state[count_cache_key]

                folder_options = [f"{f} ({folder_counts.get(f,0)} emails)" for f in clean_folders]
                selected_display = st.selectbox("📂 Select Folder", folder_options,
                    index=next((i for i, f in enumerate(clean_folders) if f == "INBOX"), 0))
                selected_folder = clean_folders[folder_options.index(selected_display)]
                total_emails = folder_counts.get(selected_folder, 0)

                with st.expander("⚙️ SETTINGS (RAW BODY PRESERVATION)", expanded=True):
                    st.info(f"📊 Total emails in folder: **{total_emails}**")
                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        start_from = st.number_input("🔢 Start from email #:", min_value=1, max_value=max(1, total_emails), value=1)
                    with col_r2:
                        download_count = st.number_input("📥 How many to download:", min_value=1, max_value=max(1, total_emails), value=min(10, max(1, total_emails)))
                    end_at = min(start_from + download_count - 1, total_emails)
                    st.caption(f"📌 Will download: Email #{start_from} to #{end_at} ({end_at-start_from+1} emails)" if total_emails > 0 else "⚠️ No emails available")
                    st.markdown("---")
                    c1, c2 = st.columns(2)
                    with c1:
                        rep_dom = st.checkbox("2️⃣ Change 'From' Domain")
                        p_from = st.text_input("   Tag [P_FROM]:", value="[P_FROM]") if rep_dom else "[P_FROM]"
                        st.markdown("---")
                        extract_plain_only = st.checkbox("8️⃣ Extract Body Only?")
                        export_format = "Merged"
                        if extract_plain_only:
                            export_format = st.radio("📤 Export Format:", ["Merged (1 file with __SEP__)", "Separate files (ZIP)"], horizontal=True)
                    with c2:
                        std_headers = st.checkbox("3️⃣ Set To=[*to], Date=[*date]")
                        mod_eid = st.checkbox("5️⃣ Add [EID] to Message-ID")
                        clean_auth = st.checkbox("6️⃣ Remove DKIM/SPF headers")
                        name_by_subj = st.checkbox("7️⃣ Name files by Subject")
                        st.markdown("---")
                        detect_dupes = st.checkbox("9️⃣ Remove Duplicates")
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
                                    em = email.message_from_bytes(msg_data[0][1])
                                    email_data_list.append({'msg': em, 'id': eid, 'raw': msg_data[0][1]})
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
                                mail.logout(); st.stop()

                        if extract_plain_only:
                            if "Merged" in export_format:
                                texts = []
                                for i, eid in enumerate(id_list):
                                    try:
                                        _, msg_data = mail.fetch(eid, '(RFC822)')
                                        em = email.message_from_bytes(msg_data[0][1])
                                        body = get_email_body_text(em)
                                        if body: texts.append(body)
                                        prog_bar.progress((i+1)/len(id_list))
                                    except: continue
                                prog_bar.empty()
                                status_msg.success(f"🎉 Extracted {len(texts)} emails into 1 merged file!")
                                st.download_button("📥 Download Merged Text File (.txt)", "\n__SEP__\n".join(texts), "emails_bodies_merged.txt", "text/plain")
                            else:
                                zip_buf = io.BytesIO()
                                with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
                                    for i, eid in enumerate(id_list):
                                        try:
                                            _, msg_data = mail.fetch(eid, '(RFC822)')
                                            em = email.message_from_bytes(msg_data[0][1])
                                            body = get_email_body_text(em)
                                            if body:
                                                fname = f"{i+1}_{clean_filename(em.get('Subject',''))}.txt" if name_by_subj else f"email_{i+1}.txt"
                                                zf.writestr(fname, body.encode('utf-8'))
                                            prog_bar.progress((i+1)/len(id_list))
                                        except: continue
                                prog_bar.empty()
                                status_msg.success("🎉 Done!")
                                st.download_button("📥 Download ZIP", zip_buf.getvalue(), "emails_bodies_separate.zip", "application/zip", use_container_width=True)
                        else:
                            zip_buf = io.BytesIO()
                            with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
                                for i, eid in enumerate(id_list):
                                    try:
                                        _, msg = mail.fetch(eid, '(RFC822)')
                                        raw = msg[0][1]
                                        sep = b'\r\n\r\n'; idx = raw.find(sep)
                                        if idx == -1: sep = b'\n\n'; idx = raw.find(sep)
                                        head = raw[:idx] if idx != -1 else raw
                                        body = raw[idx+len(sep):] if idx != -1 else b""
                                        mm = email.message_from_bytes(head)
                                        orig_subj = mm.get('Subject', 'no_subject')
                                        if rep_dom and mm.get('From'):
                                            nf = re.sub(r'@[a-zA-Z0-9.-]+', f'@{p_from}', mm['From'])
                                            del mm['From']; mm['From'] = nf
                                        if std_headers:
                                            if 'To' in mm: del mm['To']
                                            mm['To'] = '[*to]'
                                            if 'Date' in mm: del mm['Date']
                                            mm['Date'] = '[*date]'
                                        if custom_headers_text:
                                            for l in custom_headers_text.split('\n'):
                                                if ':' in l:
                                                    k, v = l.split(':', 1)
                                                    if k.strip() in mm: del mm[k.strip()]
                                                    mm[k.strip()] = v.strip()
                                        if mod_eid and mm.get('Message-ID') and '@' in mm['Message-ID']:
                                            new_mid = mm['Message-ID'].replace('@', '[EID]@', 1)
                                            del mm['Message-ID']; mm['Message-ID'] = new_mid
                                        if clean_auth:
                                            for h in ['DKIM-Signature','Authentication-Results','Received','Received-SPF','ARC-Authentication-Results','ARC-Message-Signature','ARC-Seal']:
                                                while h in mm: del mm[h]
                                        fin = mm.as_bytes() + b'\r\n\r\n' + body
                                        fname = f"{i+1}_{clean_filename(orig_subj)}.txt" if name_by_subj else f"email_{i+1}.txt"
                                        zf.writestr(fname, fin)
                                        prog_bar.progress((i+1)/len(id_list))
                                    except: continue
                            prog_bar.empty()
                            status_msg.success("🎉 Download Complete!")
                            st.download_button("📥 Download ZIP File", zip_buf.getvalue(), "emails_raw_pack.zip", "application/zip", use_container_width=True)

                        st.session_state['refresh_counts'] = True
                mail.logout()

with tab3:
    if os.path.exists("cmh1-pro.html"):
        with open("cmh1-pro.html", "r", encoding="utf-8") as f:
            components.html(f.read(), height=920, scrolling=True)
    else:
        st.error("⚠️ Fichier 'cmh1-pro.html' ma kaynch!")
