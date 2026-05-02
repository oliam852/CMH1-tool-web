import streamlit as st
import streamlit.components.v1 as components
import os, re, email, imaplib, zipfile, io, base64, json, hashlib, time
from email.header import decode_header
from cryptography.fernet import Fernet

# ==========================================
# ENCRYPTION KEY
# ==========================================
KEY_FILE = "session_key.key"

def get_fernet():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    with open(KEY_FILE, "rb") as f:
        return Fernet(f.read())

def encrypt_val(val: str) -> str:
    return get_fernet().encrypt(val.encode()).decode()

def decrypt_val(val: str) -> str:
    try:
        return get_fernet().decrypt(val.encode()).decode()
    except Exception:
        return ""

# ==========================================
# SESSIONS
# ==========================================
SESSIONS_FILE = "sessions.json"

def load_all_sessions():
    try:
        if os.path.exists(SESSIONS_FILE):
            with open(SESSIONS_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_all_sessions(sessions):
    try:
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f)
    except Exception:
        pass

def create_token(email_addr, password):
    token = hashlib.sha256(f"{email_addr}{password}{time.time()}".encode()).hexdigest()[:32]
    sessions = load_all_sessions()
    sessions[token] = {
        "email": encrypt_val(email_addr),
        "password": encrypt_val(password)
    }
    save_all_sessions(sessions)
    return token

def get_session_by_token(token):
    if not token:
        return None
    sessions = load_all_sessions()
    raw = sessions.get(token)
    if not raw:
        return None
    return {
        "email": decrypt_val(raw.get("email", "")),
        "password": decrypt_val(raw.get("password", ""))
    }

def delete_token(token):
    if not token:
        return
    sessions = load_all_sessions()
    if token in sessions:
        del sessions[token]
        save_all_sessions(sessions)

def migrate_old_session():
    if os.path.exists('.email_session.dat'):
        try:
            with open('.email_session.dat', 'r') as f:
                encoded = f.read()
            decoded = base64.b64decode(encoded).decode()
            email_addr, password = decoded.split('|||')
            os.remove('.email_session.dat')
            return {'email': email_addr, 'password': password}
        except Exception:
            pass
    return None

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="CMH1 Fusion",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@300;400;500&family=Space+Mono:wght@400;700&display=swap');

:root {
    --bg:      #0d0f12;
    --surface: #12151a;
    --panel:   #171b22;
    --border:  rgba(255,255,255,0.07);
    --amber:   #ffba00;
    --amber-d: rgba(255,186,0,0.12);
    --amber-g: rgba(255,186,0,0.06);
    --red:     #ff4d4d;
    --green:   #3ddc84;
    --text:    #dde2ec;
    --muted:   #525966;
    --muted2:  #2e333d;
}

.stApp {
    background-color: var(--bg) !important;
    background-image:
        linear-gradient(rgba(255,186,0,0.012) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,186,0,0.012) 1px, transparent 1px);
    background-size: 40px 40px;
    font-family: 'DM Mono', monospace !important;
}

[data-testid="stSidebar"]  { display: none !important; }
header                     { visibility: hidden !important; }
[data-testid="stDecoration"]{ display: none !important; }
[data-testid="stToolbar"]  { display: none !important; }
footer                     { display: none !important; }

.block-container {
    padding-top: 0.75rem !important;
    padding-bottom: 1rem !important;
    max-width: 100% !important;
}

/* TABS */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px !important;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    padding: 5px 8px !important;
    box-shadow: none !important;
}
.stTabs [data-baseweb="tab"] {
    height: 36px !important;
    background: transparent !important;
    border-radius: 3px !important;
    color: var(--muted) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 10px !important;
    font-weight: 500 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    border: none !important;
    padding: 0 18px !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text) !important; background: var(--panel) !important; }
.stTabs [aria-selected="true"] { background: var(--amber) !important; color: #0d0f12 !important; font-weight: 700 !important; }
.stTabs [data-baseweb="tab-highlight"] { background: transparent !important; }
.stTabs [data-baseweb="tab-border"] { background: var(--border) !important; height: 1px !important; }

/* TYPOGRAPHY */
p, label { font-family: 'DM Mono', monospace !important; }
h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; color: var(--text) !important; letter-spacing: 0.04em !important; }
.stMarkdown p { color: var(--text) !important; font-size: 12px !important; font-family: 'DM Mono', monospace !important; }
.stMarkdown h2 { font-family: 'Bebas Neue', sans-serif !important; font-size: 2.4rem !important; color: var(--text) !important; }

/* FIX: prevent DM Mono from breaking SVG/icon fonts */
svg, svg *, [data-testid="stExpanderToggleIcon"], .stExpanderIcon,
[class*="Icon"], [class*="icon"], button svg, summary svg { font-family: inherit !important; }

/* INPUTS */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea {
    background-color: var(--panel) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus {
    border-color: var(--amber) !important;
    box-shadow: 0 0 0 2px rgba(255,186,0,0.1) !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: var(--muted2) !important; }
[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {
    color: var(--muted) !important;
    font-size: 9px !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    font-family: 'DM Mono', monospace !important;
}

/* BUTTONS */
.stButton button {
    font-family: 'DM Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    border-radius: 3px !important;
    font-weight: 500 !important;
    transition: all 0.15s !important;
}
.stButton button[kind="primary"] {
    background: var(--amber) !important;
    color: #0d0f12 !important;
    border: none !important;
    font-weight: 700 !important;
}
.stButton button[kind="primary"]:hover { background: #ffd040 !important; box-shadow: 0 4px 16px rgba(255,186,0,0.25) !important; }
.stButton button[kind="secondary"] { background: var(--panel) !important; color: var(--muted) !important; border: 1px solid var(--border) !important; }
.stButton button[kind="secondary"]:hover { border-color: var(--amber) !important; color: var(--amber) !important; background: var(--amber-g) !important; }

/* DOWNLOAD BUTTON */
.stDownloadButton button {
    background: var(--surface) !important;
    color: var(--amber) !important;
    border: 1px solid rgba(255,186,0,0.3) !important;
    border-radius: 3px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    font-weight: 500 !important;
}
.stDownloadButton button:hover { background: var(--amber-d) !important; border-color: var(--amber) !important; }

/* CHECKBOX */
.stCheckbox label { color: var(--text) !important; font-size: 11px !important; font-family: 'DM Mono', monospace !important; text-transform: none !important; letter-spacing: 0 !important; }
.stCheckbox [data-baseweb="checkbox"] > div { background: var(--panel) !important; border-color: var(--muted2) !important; border-radius: 2px !important; }
.stCheckbox [aria-checked="true"] > div { background: var(--amber) !important; border-color: var(--amber) !important; }

/* RADIO */
.stRadio label { color: var(--text) !important; font-size: 11px !important; font-family: 'DM Mono', monospace !important; text-transform: none !important; letter-spacing: 0 !important; }
.stRadio [data-baseweb="radio"] > div { border-color: var(--muted2) !important; }
.stRadio [aria-checked="true"] > div { background: var(--amber) !important; border-color: var(--amber) !important; }

/* SELECT */
.stSelectbox [data-baseweb="select"] > div {
    background: var(--panel) !important;
    border: 1px solid var(--border) !important;
    border-radius: 3px !important;
    color: var(--text) !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 12px !important;
}
.stSelectbox [data-baseweb="select"] > div:focus-within { border-color: var(--amber) !important; }
[data-baseweb="menu"] { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 3px !important; }
[data-baseweb="option"] { background: transparent !important; color: var(--muted) !important; font-family: 'DM Mono', monospace !important; font-size: 11px !important; }
[data-baseweb="option"]:hover, [aria-selected="true"][data-baseweb="option"] { background: var(--amber-d) !important; color: var(--amber) !important; }

/* NUMBER INPUT */
.stNumberInput [data-baseweb="input"] { background: var(--panel) !important; border: 1px solid var(--border) !important; border-radius: 3px !important; }
.stNumberInput button { background: var(--panel) !important; border-color: var(--border) !important; color: var(--muted) !important; }
.stNumberInput button:hover { color: var(--amber) !important; background: var(--amber-g) !important; }

/* EXPANDER - FIXED ERROR */
.stExpander { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: 4px !important; }
.stExpander summary { 
    font-size: 10px !important; 
    letter-spacing: 0.14em !important; 
    text-transform: uppercase !important; 
    color: var(--muted) !important; 
    background: var(--panel) !important; 
    border-radius: 3px !important; 
    padding: 8px 12px !important; 
}
.stExpander summary p {
    font-family: 'DM Mono', monospace !important;
    margin: 0 !important;
}
.stExpander summary:hover { color: var(--text) !important; }
.stExpander [data-testid="stExpanderToggleIcon"] { font-family: inherit !important; }

/* ALERTS */
[data-testid="stInfo"]    { background: rgba(255,186,0,0.06) !important; border: 1px solid rgba(255,186,0,0.2) !important; border-left: 3px solid var(--amber) !important; color: var(--text) !important; border-radius: 3px !important; }
[data-testid="stSuccess"] { background: rgba(61,220,132,0.06) !important; border: 1px solid rgba(61,220,132,0.2) !important; border-left: 3px solid var(--green) !important; color: var(--text) !important; border-radius: 3px !important; }
[data-testid="stWarning"] { background: rgba(255,186,0,0.08) !important; border: 1px solid rgba(255,186,0,0.25) !important; border-left: 3px solid var(--amber) !important; color: var(--text) !important; border-radius: 3px !important; }
[data-testid="stError"]   { background: rgba(255,77,77,0.06) !important; border: 1px solid rgba(255,77,77,0.2) !important; border-left: 3px solid var(--red) !important; color: var(--text) !important; border-radius: 3px !important; }
.stAlert { font-family: 'DM Mono', monospace !important; font-size: 11px !important; }

/* PROGRESS */
.stProgress > div > div > div > div { background: var(--amber) !important; border-radius: 2px !important; }
.stProgress > div > div > div { background: var(--muted2) !important; border-radius: 2px !important; }

/* CAPTION */
.stCaptionContainer p, [data-testid="stCaptionContainer"] p { color: var(--muted) !important; font-size: 10px !important; font-family: 'DM Mono', monospace !important; }

/* MISC */
hr { border-color: var(--border) !important; margin: 10px 0 !important; }
[data-testid="column"] { padding: 0 8px !important; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--muted2); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: var(--amber); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# IMAP CONNECT
# ==========================================
def connect_imap(user, password):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        return mail
    except Exception as e:
        st.error(f"Login Error: {e}")
        return None

# ==========================================
# AUTO-LOGIN
# ==========================================
url_token = st.query_params.get("t", None)

if 'mail_connected' not in st.session_state:
    st.session_state['mail_connected'] = False

    if url_token:
        saved = get_session_by_token(url_token)
        if saved and saved.get("email"):
            mail_test = connect_imap(saved['email'], saved['password'])
            if mail_test:
                st.session_state['mail_connected'] = True
                st.session_state['saved_email'] = saved['email']
                st.session_state['saved_password'] = saved['password']
                st.session_state['current_token'] = url_token
                mail_test.logout()

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
        st.error("Fichier 'V6.html' ma kaynch!")

# ==========================================
# TAB 2 — IMAP
# ==========================================
with tab2:

    def decode_header_text(hv):
        if not hv:
            return "no_subject"
        try:
            parts = []
            for content, enc in decode_header(hv):
                if isinstance(content, bytes):
                    try:
                        content = content.decode(enc or 'utf-8', 'ignore')
                    except Exception:
                        content = content.decode('utf-8', 'ignore')
                parts.append(str(content))
            return "".join(parts)
        except Exception:
            return hv

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
                if 'attachment' in str(part.get('Content-Disposition', '')):
                    continue
                try:
                    p = part.get_payload(decode=True)
                    if not p:
                        continue
                    d = p.decode('utf-8', 'ignore')
                    if ct == 'text/plain':
                        return d
                    elif ct == 'text/html':
                        body = clean_html_to_plain(d)
                except Exception:
                    continue
        else:
            try:
                p = msg_obj.get_payload(decode=True)
                if p:
                    d = p.decode('utf-8', 'ignore')
                    body = clean_html_to_plain(d) if msg_obj.get_content_type() == 'text/html' else d
            except Exception:
                pass
        return body

    def detect_duplicates(email_list):
        seen_ids, seen_hashes, dups, unique = set(), set(), [], []
        for idx, ed in enumerate(email_list):
            mo = ed['msg']
            mid = mo.get('Message-ID', '')
            if mid and mid in seen_ids:
                dups.append({'index': idx + 1, 'id': ed['id'], 'reason': 'Same Message-ID', 'subject': mo.get('Subject', '')})
                continue
            hv = hashlib.md5(f"{mo.get('Subject','')}|{mo.get('From','')}|{mo.get('Date','')}".encode()).hexdigest()
            if hv in seen_hashes:
                dups.append({'index': idx + 1, 'id': ed['id'], 'reason': 'Same Subject+From+Date', 'subject': mo.get('Subject', '')})
                continue
            if mid:
                seen_ids.add(mid)
            seen_hashes.add(hv)
            unique.append(ed)
        return unique, dups

    # PAGE HEADER
    st.markdown("""
    <div style="border-bottom:1px solid rgba(255,255,255,0.07); padding-bottom:10px; margin-bottom:18px; margin-top:4px;">
        <div style="font-size:9px; letter-spacing:0.2em; text-transform:uppercase; color:#ffba00;
                    background:rgba(255,186,0,0.12); border:1px solid rgba(255,186,0,0.2);
                    padding:2px 8px; border-radius:2px; display:inline-block; margin-bottom:4px;">
            ● IMAP Email Tool
        </div>
        <div style="font-family:'Bebas Neue',sans-serif; font-size:2.6rem; line-height:1;
                    color:#dde2ec; letter-spacing:0.04em;">
            GMAIL / IMAP RAW
        </div>
        <div style="font-size:9px; letter-spacing:0.14em; text-transform:uppercase;
                    color:#525966; margin-top:2px;">
            Download and process raw email headers
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        if st.session_state.get('mail_connected'):
            st.success(f"Connected: {st.session_state.get('saved_email', '')}")
            if st.button("Disconnect", type="secondary", use_container_width=True):
                token = st.session_state.get('current_token')
                delete_token(token)
                st.query_params.clear()
                for k in list(st.session_state.keys()):
                    del st.session_state[k]
                st.rerun()
        else:
            st.info("Login Credentials")
            email_user = st.text_input("Email", placeholder="example@gmail.com")
            app_pass = st.text_input("App Password", type="password")
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Connect", type="primary", use_container_width=True):
                if email_user and app_pass:
                    mc = connect_imap(email_user, app_pass)
                    if mc:
                        token = create_token(email_user, app_pass)
                        st.session_state['mail_connected'] = True
                        st.session_state['saved_email'] = email_user
                        st.session_state['saved_password'] = app_pass
                        st.session_state['current_token'] = token
                        st.query_params["t"] = token
                        st.success("Connected!")
                        mc.logout()
                        st.rerun()
                else:
                    st.warning("Please enter credentials.")

    with col2:
        if st.session_state.get('mail_connected'):
            email_user = st.session_state.get('saved_email')
            app_pass   = st.session_state.get('saved_password')

            mail = connect_imap(email_user, app_pass)
            if mail:
                try:
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

                    if st.button("Refresh Folders", type="secondary"):
                        st.session_state['refresh_folders'] = True
                        st.session_state['refresh_counts'] = True
                        st.rerun()

                    cnt_key = f"counts_{email_user}_all"
                    if cnt_key not in st.session_state or st.session_state.get('refresh_counts'):
                        fc = {}
                        with st.spinner("Counting emails..."):
                            for folder in clean_folders:
                                try:
                                    mail.select(f'"{folder}"', readonly=True)
                                    typ, data = mail.search(None, 'ALL')
                                    fc[folder] = len(data[0].split()) if typ == 'OK' and data[0] else 0
                                except Exception:
                                    fc[folder] = 0
                        st.session_state[cnt_key] = fc
                        st.session_state['refresh_counts'] = False
                    else:
                        fc = st.session_state[cnt_key]

                    fopts = [f"{f} ({fc.get(f, 0)} emails)" for f in clean_folders]
                    sel_disp = st.selectbox("Select Folder", fopts,
                        index=next((i for i, f in enumerate(clean_folders) if f == "INBOX"), 0))
                    sel_folder = clean_folders[fopts.index(sel_disp)]
                    total_emails = fc.get(sel_folder, 0)

                    with st.expander("Settings — RAW Body Preservation", expanded=True):
                        st.info(f"Total emails in folder: **{total_emails}**")
                        cr1, cr2 = st.columns(2)
                        with cr1:
                            start_from = st.number_input("Start from email #", min_value=1, max_value=max(1, total_emails), value=1)
                        with cr2:
                            dl_count = st.number_input("How many to download", min_value=1, max_value=max(1, total_emails), value=min(10, max(1, total_emails)))
                        end_at = min(start_from + dl_count - 1, total_emails)
                        st.caption(f"Will download: #{start_from} to #{end_at} ({end_at - start_from + 1} emails)" if total_emails > 0 else "No emails")
                        st.markdown("---")

                        c1, c2 = st.columns(2)
                        with c1:
                            rep_dom = st.checkbox("Change 'From' Domain")
                            p_from = st.text_input("Tag [P_FROM]", value="[P_FROM]") if rep_dom else "[P_FROM]"
                            st.markdown("---")
                            mod_subject = st.checkbox("Modify Subject")
                            subj_new_value = ""
                            if mod_subject:
                                subj_new_value = st.text_input("New Subject", value="", placeholder="e.g. [S]")
                                st.caption("Replaces the original subject entirely")
                            st.markdown("---")
                            mod_content_type = st.checkbox("Modify Content-Type")
                            custom_content_type = ""
                            if mod_content_type:
                                custom_content_type = st.text_input("Content-Type", value="text/plain; charset=UTF-8")
                            st.markdown("---")
                            extract_plain = st.checkbox("Extract Body Only")
                            exp_fmt = "Merged"
                            if extract_plain:
                                exp_fmt = st.radio("Export Format", ["Merged (1 file with __SEP__)", "Separate files (ZIP)"], horizontal=True)

                        with c2:
                            std_hdrs     = st.checkbox("Set To=[*to], Date=[*date]")
                            mod_eid      = st.checkbox("Add [EID] to Message-ID")
                            clean_auth   = st.checkbox("Remove DKIM/SPF headers")
                            name_by_subj = st.checkbox("Name files by Subject")
                            st.markdown("---")
                            headers_only = st.checkbox("Headers Only (no Body)")
                            if headers_only:
                                st.caption("File will contain headers only.")
                            st.markdown("---")
                            det_dupes = st.checkbox("Remove Duplicates")

                        custom_hdrs  = st.text_area("Custom Headers (Key:Value)")
                        st.markdown("---")
                        zip_filename = st.text_input("ZIP File Name", value="emails_raw_pack", placeholder="name without .zip")
                        zip_filename = zip_filename.strip().replace(" ", "_") or "emails_raw_pack"

                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Start Download & Process", type="primary", use_container_width=True):
                        mail.select(f'"{sel_folder}"', readonly=True)
                        _, data = mail.search(None, 'ALL')
                        id_list = data[0].split()
                        id_list.reverse()
                        id_list = id_list[start_from - 1:start_from - 1 + dl_count]

                        if not id_list:
                            st.error("No emails found.")
                        else:
                            smsg = st.empty()
                            pbar = st.progress(0)

                            smsg.info("Fetching emails...")
                            fetched_emails = []
                            for i, eid in enumerate(id_list):
                                try:
                                    _, md = mail.fetch(eid, '(RFC822)')
                                    raw_bytes = md[0][1]
                                    em = email.message_from_bytes(raw_bytes)
                                    fetched_emails.append({'msg': em, 'id': eid, 'raw': raw_bytes})
                                    pbar.progress((i + 1) / len(id_list) * 0.4)
                                except Exception:
                                    continue

                            if det_dupes:
                                smsg.info("Detecting duplicates...")
                                unique, dups = detect_duplicates(fetched_emails)
                                if dups:
                                    smsg.warning(f"Found {len(dups)} duplicate(s). Processing {len(unique)} unique.")
                                    with st.expander(f"{len(dups)} Duplicates found"):
                                        for d in dups[:20]:
                                            st.caption(f"#{d['index']}: {d['subject'][:50]} — {d['reason']}")
                                        if len(dups) > 20:
                                            st.caption(f"... and {len(dups) - 20} more")
                                else:
                                    smsg.success("No duplicates found!")
                                fetched_emails = unique

                            if not fetched_emails:
                                st.error("All duplicates — nothing to process!")
                            elif extract_plain:
                                if "Merged" in exp_fmt:
                                    texts = []
                                    for i, ed in enumerate(fetched_emails):
                                        try:
                                            b = get_email_body_text(ed['msg'])
                                            if b:
                                                texts.append(b)
                                            pbar.progress(0.4 + (i + 1) / len(fetched_emails) * 0.6)
                                        except Exception:
                                            continue
                                    pbar.empty()
                                    smsg.success(f"Extracted {len(texts)} emails!")
                                    st.download_button("Download Merged .txt", "\n__SEP__\n".join(texts), "emails_bodies_merged.txt", "text/plain")
                                else:
                                    zbuf = io.BytesIO()
                                    with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as zf:
                                        for i, ed in enumerate(fetched_emails):
                                            try:
                                                b = get_email_body_text(ed['msg'])
                                                if b:
                                                    fn = f"{i+1}_{clean_filename(ed['msg'].get('Subject',''))}.txt" if name_by_subj else f"email_{i+1}.txt"
                                                    zf.writestr(fn, b.encode('utf-8'))
                                                pbar.progress(0.4 + (i + 1) / len(fetched_emails) * 0.6)
                                            except Exception:
                                                continue
                                    pbar.empty()
                                    smsg.success("Done!")
                                    st.download_button("Download ZIP", zbuf.getvalue(), f"{zip_filename}.zip", "application/zip", use_container_width=True)
                            else:
                                zbuf = io.BytesIO()
                                with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as zf:
                                    for i, ed in enumerate(fetched_emails):
                                        try:
                                            raw = ed['raw']
                                            sep = b'\r\n\r\n'
                                            idx = raw.find(sep)
                                            if idx == -1:
                                                sep = b'\n\n'
                                                idx = raw.find(sep)
                                            head = raw[:idx] if idx != -1 else raw
                                            body = raw[idx + len(sep):] if idx != -1 else b""
                                            mm = email.message_from_bytes(head)
                                            os_ = mm.get('Subject', 'no_subject')

                                            if rep_dom and mm.get('From'):
                                                nf = re.sub(r'@[a-zA-Z0-9.-]+', f'@{p_from}', mm['From'])
                                                del mm['From']
                                                mm['From'] = nf

                                            if std_hdrs:
                                                if 'To' in mm: del mm['To']
                                                mm['To'] = '[*to]'
                                                if 'Date' in mm: del mm['Date']
                                                mm['Date'] = '[*date]'

                                            if custom_hdrs:
                                                for l in custom_hdrs.split('\n'):
                                                    if ':' in l:
                                                        k, v = l.split(':', 1)
                                                        if k.strip() in mm: del mm[k.strip()]
                                                        mm[k.strip()] = v.strip()

                                            if mod_eid and mm.get('Message-ID') and '@' in mm['Message-ID']:
                                                nm = mm['Message-ID'].replace('@', '[EID]@', 1)
                                                del mm['Message-ID']
                                                mm['Message-ID'] = nm

                                            if clean_auth:
                                                for h in ['DKIM-Signature', 'Authentication-Results', 'Received',
                                                          'Received-SPF', 'ARC-Authentication-Results',
                                                          'ARC-Message-Signature', 'ARC-Seal']:
                                                    while h in mm: del mm[h]

                                            if mod_subject:
                                                if 'Subject' in mm: del mm['Subject']
                                                mm['Subject'] = subj_new_value

                                            if mod_content_type and custom_content_type:
                                                if 'Content-Type' in mm: del mm['Content-Type']
                                                mm['Content-Type'] = custom_content_type

                                            if headers_only:
                                                body = b""

                                            fin = mm.as_bytes() + b'\r\n\r\n' + body
                                            fn = f"{i+1}_{clean_filename(os_)}.txt" if name_by_subj else f"email_{i+1}.txt"
                                            zf.writestr(fn, fin)
                                            pbar.progress(0.4 + (i + 1) / len(fetched_emails) * 0.6)
                                        except Exception:
                                            continue
                                pbar.empty()
                                smsg.success("Download Complete!")
                                st.download_button("Download ZIP File", zbuf.getvalue(), f"{zip_filename}.zip", "application/zip", use_container_width=True)

                            st.session_state['refresh_counts'] = True

                finally:
                    try:
                        mail.logout()
                    except Exception:
                        pass

# ==========================================
# TAB 3 — CMH-1 PRO
# ==========================================
with tab3:
    if os.path.exists("cmh1-pro.html"):
        with open("cmh1-pro.html", "r", encoding="utf-8") as f:
            components.html(f.read(), height=920, scrolling=True)
    else:
        st.error("Fichier 'cmh1-pro.html' ma kaynch!")
