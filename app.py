import streamlit as st
import streamlit.components.v1 as components
import os, re, email, imaplib, zipfile, io, base64, json, hashlib, time
from email.header import decode_header

# ==========================================
# SESSION VIA URL TOKEN (بدون أي library)
# ==========================================
# كيف يخدم:
# 1. مول يدخل credentials → نولدو token عشوائي
# 2. نحفظو sessions.json على السيرفر: {token: {email, password}}
# 3. نحطو token في URL: ?t=abc123
# 4. F5 → URL كيبقى → token كيبقى → يدخل تلقائي
# 5. كل متصفح عندو URL خاص بيه → جلسة منفصلة

SESSIONS_FILE = "sessions.json"

def load_all_sessions():
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, 'r') as f:
                return json.load(f)
    except: pass
    return {}

def save_all_sessions(sessions):
    try:
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f)
    except: pass

def create_token(email_addr, password):
    """يولد token فريد ويحفظو"""
    token = hashlib.sha256(f"{email_addr}{password}{time.time()}".encode()).hexdigest()[:32]
    sessions = load_all_sessions()
    sessions[token] = {"email": email_addr, "password": password}
    save_all_sessions(sessions)
    return token

def get_session_by_token(token):
    """يرجع الجلسة من token"""
    if not token: return None
    sessions = load_all_sessions()
    return sessions.get(token)

def delete_token(token):
    """يمسح token عند Disconnect"""
    if not token: return
    sessions = load_all_sessions()
    if token in sessions:
        del sessions[token]
        save_all_sessions(sessions)

# migration من الملف القديم
def migrate_old_session():
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
# AUTO-LOGIN من URL token
# ==========================================
def connect_imap(user, password):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        return mail
    except Exception as e:
        st.error(f"❌ Login Error: {e}")
        return None

# قرا الـ token من URL
url_token = st.query_params.get("t", None)

if 'mail_connected' not in st.session_state:
    st.session_state['mail_connected'] = False

    # 1. جرب من URL token
    if url_token:
        saved = get_session_by_token(url_token)
        if saved:
            mail_test = connect_imap(saved['email'], saved['password'])
            if mail_test:
                st.session_state['mail_connected'] = True
                st.session_state['saved_email'] = saved['email']
                st.session_state['saved_password'] = saved['password']
                st.session_state['current_token'] = url_token
                mail_test.logout()

    # 2. migration من الملف القديم
    if not st.session_state['mail_connected']:
        old = migrate_old_session()
        if old:
            mail_test = connect_imap(old['email'], old['password'])
            if mail_test:
                token = create_token(old['email'], old['password'])
                st.session_state['mail_connected'] = True
                st.session_state['saved_email'] = old['email']
                st.session_state['saved_password'] = old['password']
                st.session_state['current_token'] = token
                st.query_params["t"] = token
                mail_test.logout()

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

    def decode_header_text(hv):
        if not hv: return "no_subject"
        try:
            parts = []
            for content, enc in decode_header(hv):
                if isinstance(content, bytes):
                    try: content = content.decode(enc or 'utf-8', 'ignore')
                    except: content = content.decode('utf-8', 'ignore')
                parts.append(str(content))
            return "".join(parts)
        except: return hv

    def clean_filename(subject):
        ds = decode_header_text(subject or "")
        return re.sub(r'[^a-zA-Z0-9\s_\-\u00C0-\u017F]', '', ds).strip().replace(' ', '_')[:60] or "no_subject"

    def clean_html_to_plain(html):
        return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html)).strip()

    def get_email_body_text(msg_obj):
        body = ""
        if msg_obj.is_multipart():
            for part in msg_obj.walk():
                ct = part.get_content_type()
                if 'attachment' in str(part.get('Content-Disposition', '')): continue
                try:
                    p = part.get_payload(decode=True)
                    if not p: continue
                    d = p.decode('utf-8', 'ignore')
                    if ct == 'text/plain': return d
                    elif ct == 'text/html': body = clean_html_to_plain(d)
                except: continue
        else:
            try:
                p = msg_obj.get_payload(decode=True)
                if p:
                    d = p.decode('utf-8', 'ignore')
                    body = clean_html_to_plain(d) if msg_obj.get_content_type() == 'text/html' else d
            except: pass
        return body

    def detect_duplicates(email_list):
        seen_ids, seen_hashes, dups, unique = set(), set(), [], []
        for idx, ed in enumerate(email_list):
            mo = ed['msg']
            mid = mo.get('Message-ID', '')
            if mid and mid in seen_ids:
                dups.append({'index': idx+1, 'id': ed['id'], 'reason': 'Same Message-ID', 'subject': mo.get('Subject', '')}); continue
            hv = hashlib.md5(f"{mo.get('Subject','')}|{mo.get('From','')}|{mo.get('Date','')}".encode()).hexdigest()
            if hv in seen_hashes:
                dups.append({'index': idx+1, 'id': ed['id'], 'reason': 'Same Subject+From+Date', 'subject': mo.get('Subject', '')}); continue
            if mid: seen_ids.add(mid)
            seen_hashes.add(hv); unique.append(ed)
        return unique, dups

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## 🚀 GMAIL/IMAP RAW TOOL")
    st.markdown("Developed by **@ayoubrhattoy**")

    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        if st.session_state.get('mail_connected'):
            st.success(f"✅ Connected: {st.session_state.get('saved_email', '')}")
            if st.button("🔌 Disconnect", type="secondary", use_container_width=True):
                token = st.session_state.get('current_token')
                delete_token(token)
                st.query_params.clear()
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
                    mc = connect_imap(email_user, app_pass)
                    if mc:
                        token = create_token(email_user, app_pass)
                        st.session_state['mail_connected'] = True
                        st.session_state['saved_email'] = email_user
                        st.session_state['saved_password'] = app_pass
                        st.session_state['current_token'] = token
                        # نحطو token في URL → يبقى بعد F5
                        st.query_params["t"] = token
                        st.success("✅ Connected!")
                        mc.logout()
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
                    _, folders = mail.list()
                    clean_folders = []
                    for folder in folders:
                        fs = folder.decode()
                        m = re.search(r'"([^"]+)"$', fs) or re.search(r' ([^ ]+)$', fs)
                        clean_folders.append(m.group(1) if m else fs)
                    st.session_state[cache_key] = clean_folders
                    st.session_state['refresh_folders'] = False
                else:
                    clean_folders = st.session_state[cache_key]

                if st.button("🔄 Refresh Folders"):
                    st.session_state['refresh_folders'] = True
                    st.session_state['refresh_counts'] = True
                    st.rerun()

                cnt_key = f"counts_{email_user}_all"
                if cnt_key not in st.session_state or st.session_state.get('refresh_counts'):
                    fc = {}
                    with st.spinner("📊 Counting emails..."):
                        for folder in clean_folders:
                            try:
                                mail.select(f'"{folder}"', readonly=True)
                                typ, data = mail.search(None, 'ALL')
                                fc[folder] = len(data[0].split()) if typ == 'OK' and data[0] else 0
                            except: fc[folder] = 0
                    st.session_state[cnt_key] = fc
                    st.session_state['refresh_counts'] = False
                else:
                    fc = st.session_state[cnt_key]

                fopts = [f"{f} ({fc.get(f,0)} emails)" for f in clean_folders]
                sel_disp = st.selectbox("📂 Select Folder", fopts,
                    index=next((i for i, f in enumerate(clean_folders) if f == "INBOX"), 0))
                sel_folder = clean_folders[fopts.index(sel_disp)]
                total_emails = fc.get(sel_folder, 0)

                with st.expander("⚙️ SETTINGS (RAW BODY PRESERVATION)", expanded=True):
                    st.info(f"📊 Total emails in folder: **{total_emails}**")
                    cr1, cr2 = st.columns(2)
                    with cr1:
                        start_from = st.number_input("🔢 Start from email #:", min_value=1, max_value=max(1,total_emails), value=1)
                    with cr2:
                        dl_count = st.number_input("📥 How many to download:", min_value=1, max_value=max(1,total_emails), value=min(10,max(1,total_emails)))
                    end_at = min(start_from+dl_count-1, total_emails)
                    st.caption(f"📌 Will download: #{start_from} to #{end_at} ({end_at-start_from+1} emails)" if total_emails > 0 else "⚠️ No emails")
                    st.markdown("---")
                    c1, c2 = st.columns(2)
                    with c1:
                        rep_dom = st.checkbox("2️⃣ Change 'From' Domain")
                        p_from = st.text_input("   Tag [P_FROM]:", value="[P_FROM]") if rep_dom else "[P_FROM]"
                        st.markdown("---")
                        extract_plain = st.checkbox("8️⃣ Extract Body Only?")
                        exp_fmt = "Merged"
                        if extract_plain:
                            exp_fmt = st.radio("📤 Export Format:", ["Merged (1 file with __SEP__)", "Separate files (ZIP)"], horizontal=True)
                    with c2:
                        std_hdrs = st.checkbox("3️⃣ Set To=[*to], Date=[*date]")
                        mod_eid = st.checkbox("5️⃣ Add [EID] to Message-ID")
                        clean_auth = st.checkbox("6️⃣ Remove DKIM/SPF headers")
                        name_by_subj = st.checkbox("7️⃣ Name files by Subject")
                        st.markdown("---")
                        det_dupes = st.checkbox("9️⃣ Remove Duplicates")
                    custom_hdrs = st.text_area("4️⃣ Custom Headers (Key:Value)")

                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🚀 START DOWNLOAD & PROCESS", type="primary", use_container_width=True):
                    mail.select(f'"{sel_folder}"', readonly=True)
                    _, data = mail.search(None, 'ALL')
                    id_list = data[0].split()
                    id_list.reverse()
                    id_list = id_list[start_from-1:start_from-1+dl_count]

                    if not id_list:
                        st.error("📭 No emails found.")
                    else:
                        smsg = st.empty(); pbar = st.progress(0)

                        if det_dupes:
                            smsg.info("🔍 Detecting duplicates...")
                            edl = []
                            for eid in id_list:
                                try:
                                    _, md = mail.fetch(eid, '(RFC822)')
                                    em = email.message_from_bytes(md[0][1])
                                    edl.append({'msg': em, 'id': eid, 'raw': md[0][1]})
                                except: continue
                            unique, dups = detect_duplicates(edl)
                            if dups:
                                smsg.warning(f"⚠️ Found {len(dups)} duplicate(s). Processing {len(unique)} unique.")
                                with st.expander(f"📋 {len(dups)} Duplicates"):
                                    for d in dups[:20]: st.caption(f"#{d['index']}: {d['subject'][:50]} - {d['reason']}")
                                    if len(dups)>20: st.caption(f"... and {len(dups)-20} more")
                            else: smsg.success("✅ No duplicates!")
                            id_list = [x['id'] for x in unique]
                            if not id_list:
                                st.error("📭 All duplicates!"); mail.logout(); st.stop()

                        if extract_plain:
                            if "Merged" in exp_fmt:
                                texts = []
                                for i, eid in enumerate(id_list):
                                    try:
                                        _, md = mail.fetch(eid, '(RFC822)')
                                        b = get_email_body_text(email.message_from_bytes(md[0][1]))
                                        if b: texts.append(b)
                                        pbar.progress((i+1)/len(id_list))
                                    except: continue
                                pbar.empty(); smsg.success(f"🎉 Extracted {len(texts)} emails!")
                                st.download_button("📥 Download Merged .txt", "\n__SEP__\n".join(texts), "emails_bodies_merged.txt", "text/plain")
                            else:
                                zbuf = io.BytesIO()
                                with zipfile.ZipFile(zbuf,"a",zipfile.ZIP_DEFLATED,False) as zf:
                                    for i, eid in enumerate(id_list):
                                        try:
                                            _, md = mail.fetch(eid, '(RFC822)')
                                            em = email.message_from_bytes(md[0][1])
                                            b = get_email_body_text(em)
                                            if b:
                                                fn = f"{i+1}_{clean_filename(em.get('Subject',''))}.txt" if name_by_subj else f"email_{i+1}.txt"
                                                zf.writestr(fn, b.encode('utf-8'))
                                            pbar.progress((i+1)/len(id_list))
                                        except: continue
                                pbar.empty(); smsg.success("🎉 Done!")
                                st.download_button("📥 Download ZIP", zbuf.getvalue(), "emails_bodies_separate.zip", "application/zip", use_container_width=True)
                        else:
                            zbuf = io.BytesIO()
                            with zipfile.ZipFile(zbuf,"a",zipfile.ZIP_DEFLATED,False) as zf:
                                for i, eid in enumerate(id_list):
                                    try:
                                        _, msg = mail.fetch(eid, '(RFC822)')
                                        raw = msg[0][1]
                                        sep = b'\r\n\r\n'; idx = raw.find(sep)
                                        if idx==-1: sep=b'\n\n'; idx=raw.find(sep)
                                        head = raw[:idx] if idx!=-1 else raw
                                        body = raw[idx+len(sep):] if idx!=-1 else b""
                                        mm = email.message_from_bytes(head)
                                        os_ = mm.get('Subject','no_subject')
                                        if rep_dom and mm.get('From'):
                                            nf = re.sub(r'@[a-zA-Z0-9.-]+', f'@{p_from}', mm['From'])
                                            del mm['From']; mm['From'] = nf
                                        if std_hdrs:
                                            if 'To' in mm: del mm['To']
                                            mm['To']='[*to]'
                                            if 'Date' in mm: del mm['Date']
                                            mm['Date']='[*date]'
                                        if custom_hdrs:
                                            for l in custom_hdrs.split('\n'):
                                                if ':' in l:
                                                    k,v=l.split(':',1)
                                                    if k.strip() in mm: del mm[k.strip()]
                                                    mm[k.strip()]=v.strip()
                                        if mod_eid and mm.get('Message-ID') and '@' in mm['Message-ID']:
                                            nm=mm['Message-ID'].replace('@','[EID]@',1)
                                            del mm['Message-ID']; mm['Message-ID']=nm
                                        if clean_auth:
                                            for h in ['DKIM-Signature','Authentication-Results','Received','Received-SPF','ARC-Authentication-Results','ARC-Message-Signature','ARC-Seal']:
                                                while h in mm: del mm[h]
                                        fin = mm.as_bytes()+b'\r\n\r\n'+body
                                        fn = f"{i+1}_{clean_filename(os_)}.txt" if name_by_subj else f"email_{i+1}.txt"
                                        zf.writestr(fn, fin)
                                        pbar.progress((i+1)/len(id_list))
                                    except: continue
                            pbar.empty(); smsg.success("🎉 Download Complete!")
                            st.download_button("📥 Download ZIP File", zbuf.getvalue(), "emails_raw_pack.zip", "application/zip", use_container_width=True)
                        st.session_state['refresh_counts'] = True
                mail.logout()

with tab3:
    if os.path.exists("cmh1-pro.html"):
        with open("cmh1-pro.html","r",encoding="utf-8") as f:
            components.html(f.read(), height=920, scrolling=True)
    else:
        st.error("⚠️ Fichier 'cmh1-pro.html' ma kaynch!")
