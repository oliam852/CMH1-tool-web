import streamlit as st
import streamlit.components.v1 as components
import os, re, email, imaplib, zipfile, io, base64, json, hashlib, time, quopri
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
@keyframes bgShift {
  0%   { background-color: #0b0f1a; }
  25%  { background-color: #0a1520; }
  50%  { background-color: #0d1218; }
  75%  { background-color: #0f0d1c; }
  100% { background-color: #0b0f1a; }
}

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
    --text:    #ffffff;
    --muted:   #8a96a8;
    --muted2:  #2e333d;
}

.stApp {
    animation: bgShift 14s ease-in-out infinite !important;
    background-image:
        linear-gradient(rgba(255,186,0,0.013) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,186,0,0.013) 1px, transparent 1px) !important;
    background-size: 40px 40px !important;
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

/* INPUTS */
.stTextInput input, .stTextArea textarea {
    background-color: var(--panel) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
}

/* ALERTS */
[data-testid="stInfo"]    { background: rgba(255,186,0,0.06) !important; border-left: 3px solid var(--amber) !important; color: var(--text) !important; }
[data-testid="stSuccess"] { background: rgba(61,220,132,0.06) !important; border-left: 3px solid var(--green) !important; color: var(--text) !important; }

::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-thumb { background: var(--muted2); border-radius: 2px; }
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
        if not hv: return "no_subject"
        try:
            parts = []
            for content, enc in decode_header(hv):
                if isinstance(content, bytes):
                    content = content.decode(enc or 'utf-8', 'ignore')
                parts.append(str(content))
            return "".join(parts)
        except: return hv

    def clean_filename(subject):
        ds = decode_header_text(subject or "")
        return re.sub(r'[^a-zA-Z0-9\s_\-\u00C0-\u017F]', '', ds).strip().replace(' ', '_')[:60] or "no_subject"

    def remove_header_lines(lines, header_name):
        result = []
        skip = False
        hn_lower = header_name.lower() + ':'
        for line in lines:
            if line.lower().startswith(hn_lower):
                skip = True
                continue
            if skip and line and line[0] in (' ', '\t'): continue
            skip = False
            result.append(line)
        return result

    def set_header_lines(lines, header_name, value):
        lines = remove_header_lines(lines, header_name)
        lines.insert(1 if len(lines) > 1 else 0, f"{header_name}: {value}")
        return lines

    # PAGE HEADER
    st.markdown("""
    <div style="border-bottom:1px solid rgba(255,255,255,0.07); padding-bottom:10px; margin-bottom:18px;">
        <div style="font-family:'Bebas Neue',sans-serif; font-size:2.6rem; color:#dde2ec;">GMAIL / IMAP RAW</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2], gap="large")

    with col1:
        if st.session_state.get('mail_connected'):
            st.success(f"Connected: {st.session_state.get('saved_email', '')}")
            if st.button("Disconnect", type="secondary", use_container_width=True):
                delete_token(st.session_state.get('current_token'))
                st.query_params.clear()
                for k in list(st.session_state.keys()): del st.session_state[k]
                st.rerun()
        else:
            email_user = st.text_input("Email")
            app_pass = st.text_input("App Password", type="password")
            if st.button("Connect", type="primary", use_container_width=True):
                if email_user and app_pass:
                    mc = connect_imap(email_user, app_pass)
                    if mc:
                        token = create_token(email_user, app_pass)
                        st.session_state.update({'mail_connected': True, 'saved_email': email_user, 'saved_password': app_pass, 'current_token': token})
                        st.query_params["t"] = token
                        mc.logout()
                        st.rerun()

    with col2:
        if st.session_state.get('mail_connected'):
            email_user = st.session_state.get('saved_email')
            app_pass   = st.session_state.get('saved_password')
            mail = connect_imap(email_user, app_pass)
            if mail:
                try:
                    _, folders = mail.list()
                    clean_folders = []
                    for f in folders:
                        fs = f.decode()
                        m = re.search(r'"([^"]+)"$', fs) or re.search(r' ([^ ]+)$', fs)
                        clean_folders.append(m.group(1) if m else fs)
                    
                    sel_folder = st.selectbox("Select Folder", clean_folders, index=clean_folders.index("INBOX") if "INBOX" in clean_folders else 0)
                    
                    with st.expander("Process Settings", expanded=True):
                        c1, c2 = st.columns(2)
                        with c1:
                            start_from = st.number_input("Start Index", min_value=1, value=1)
                            dl_count = st.number_input("Count", min_value=1, value=10)
                            rep_dom = st.checkbox("Change From Domain")
                            p_from = st.text_input("From Tag", "[P_FROM]") if rep_dom else ""
                        with c2:
                            # [جديد] - تبديل الدومينات + حيد السطور الخاوية
                            rep_body_dom = st.checkbox("Custom Body Domain & Clean")
                            p_domain = st.text_input("New Body Domain/Tag", "[P_DOMAIN]") if rep_body_dom else ""
                            rm_empty = st.checkbox("Remove Empty Lines", value=True) if rep_body_dom else False
                            
                            std_hdrs = st.checkbox("Set To/Date tags")
                            clean_auth = st.checkbox("Remove Auth Headers")
                            headers_only = st.checkbox("Headers Only")
                        
                        custom_hdrs = st.text_area("Custom Headers (K:V)")
                        zip_filename = st.text_input("ZIP Name", "processed_emails")

                    if st.button("Start Processing", type="primary", use_container_width=True):
                        mail.select(f'"{sel_folder}"', readonly=True)
                        _, data = mail.search(None, 'ALL')
                        ids = data[0].split()[::-1][start_from-1 : start_from-1+dl_count]
                        
                        if not ids: st.error("No emails.")
                        else:
                            zbuf = io.BytesIO()
                            pbar = st.progress(0)
                            with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as zf:
                                for i, eid in enumerate(ids):
                                    _, md = mail.fetch(eid, '(RFC822)')
                                    raw = md[0][1]
                                    
                                    # Split Head/Body
                                    sep = b'\r\n\r\n' if b'\r\n\r\n' in raw else b'\n\n'
                                    raw_head, body = raw.split(sep, 1) if sep in raw else (raw, b'')
                                    
                                    # Process Headers
                                    h_text = raw_head.decode('utf-8', 'replace')
                                    h_lines = h_text.split('\r\n' if b'\r\n' in sep else '\n')
                                    subj = email.message_from_string(h_text).get('Subject', 'no_subj')
                                    
                                    if rep_dom:
                                        for idx, l in enumerate(h_lines):
                                            if l.lower().startswith('from:'): h_lines[idx] = re.sub(r'@[a-zA-Z0-9.\-]+', f'@{p_from}', l)
                                    if std_hdrs:
                                        h_lines = set_header_lines(h_lines, 'To', '[*to]')
                                        h_lines = set_header_lines(h_lines, 'Date', '[*date]')
                                    if custom_hdrs:
                                        for cl in custom_hdrs.split('\n'):
                                            if ':' in cl: k, v = cl.split(':', 1); h_lines = set_header_lines(h_lines, k.strip(), v.strip())
                                    if clean_auth:
                                        for h in ['DKIM-Signature','Authentication-Results','Received-SPF','ARC-Authentication-Results']:
                                            h_lines = remove_header_lines(h_lines, h)

                                    # Process Body (Domains + Empty Lines)
                                    if not headers_only and body:
                                        is_qp = any('quoted-printable' in hl.lower() for hl in h_lines if 'content-transfer-encoding' in hl.lower())
                                        b_text = quopri.decodestring(body).decode('utf-8', 'ignore') if is_qp else body.decode('utf-8', 'ignore')
                                        
                                        if rep_body_dom:
                                            # Replace Domains
                                            dom_reg = r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}'
                                            protect = ['utf-8', 'iso-8859', 'quoted-printable', 'text/html', 'text/plain']
                                            b_text = re.sub(dom_reg, lambda m: m.group(0) if m.group(0).lower() in protect else p_domain, b_text)
                                            
                                            # [الحل ديالك هنا] - Remove Empty Lines
                                            if rm_empty:
                                                # كنقسمو النص لسطور، كنحيدو لي خاويين، وكنجمعوه عاوتاني
                                                filtered_lines = [line for line in b_text.splitlines() if line.strip()]
                                                b_text = "\n".join(filtered_lines)

                                        body = quopri.encodestring(b_text.encode('utf-8')) if is_qp else b_text.encode('utf-8')
                                    elif headers_only: body = b''

                                    final_raw = ('\r\n' if b'\r\n' in sep else '\n').join(h_lines).encode('utf-8') + sep + body
                                    zf.writestr(f"{i+1}_{clean_filename(subj)}.txt", final_raw)
                                    pbar.progress((i+1)/len(ids))
                            
                            st.success("Done!")
                            st.download_button("Download ZIP", zbuf.getvalue(), f"{zip_filename}.zip", use_container_width=True)
                finally: mail.logout()

with tab3:
    if os.path.exists("cmh1-pro.html"):
        with open("cmh1-pro.html", "r", encoding="utf-8") as f: components.html(f.read(), height=920, scrolling=True)
