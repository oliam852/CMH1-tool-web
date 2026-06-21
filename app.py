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
# PAGE CONFIG & CSS (ORIGINAL)
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

.stTabs [data-baseweb="tab-list"] {
    gap: 4px !important;
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    padding: 5px 8px !important;
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
}
.stTabs [aria-selected="true"] { background: var(--amber) !important; color: #0d0f12 !important; font-weight: 700 !important; }

.stTextInput input, .stTextArea textarea {
    background-color: var(--panel) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    font-family: 'DM Mono', monospace !important;
}

.stButton button[kind="primary"] {
    background: var(--amber) !important;
    color: #0d0f12 !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

def connect_imap(user, password):
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(user, password)
        return mail
    except Exception as e:
        st.error(f"Login Error: {e}")
        return None

# Auto-login Logic
url_token = st.query_params.get("t", None)
if 'mail_connected' not in st.session_state:
    st.session_state['mail_connected'] = False
    if url_token:
        saved = get_session_by_token(url_token)
        if saved and saved.get("email"):
            m_t = connect_imap(saved['email'], saved['password'])
            if m_t:
                st.session_state.update({'mail_connected': True, 'saved_email': saved['email'], 'saved_password': saved['password'], 'current_token': url_token})
                m_t.logout()

tab1, tab2, tab3 = st.tabs(["💻 HTML FUSION EDITOR", "📧 IMAP EMAIL TOOL", "⚡ CMH-1 PRO"])

with tab1:
    if os.path.exists("V6.html"):
        with open("V6.html", "r", encoding="utf-8") as f:
            components.html(f.read(), height=920, scrolling=True)
    else: st.error("V6.html missing")
        # --- تكميلة الملف (Part 2/2) ---

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
        insert_pos = 1 if len(lines) > 1 else 0
        lines.insert(insert_pos, f"{header_name}: {value}")
        return lines

    st.markdown("""
    <div style="border-bottom:1px solid rgba(255,255,255,0.07); padding-bottom:10px; margin-bottom:18px; margin-top:4px;">
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
            e_user = st.text_input("Email", placeholder="example@gmail.com")
            a_pass = st.text_input("App Password", type="password")
            if st.button("Connect", type="primary", use_container_width=True):
                if e_user and a_pass:
                    mc = connect_imap(e_user, a_pass)
                    if mc:
                        tk = create_token(e_user, a_pass)
                        st.session_state.update({'mail_connected': True, 'saved_email': e_user, 'saved_password': a_pass, 'current_token': tk})
                        st.query_params["t"] = tk
                        mc.logout(); st.rerun()

    with col2:
        if st.session_state.get('mail_connected'):
            mail = connect_imap(st.session_state['saved_email'], st.session_state['saved_password'])
            if mail:
                try:
                    _, folders = mail.list()
                    clean_folders = [re.search(r'"([^"]+)"$', f.decode()).group(1) if '"' in f.decode() else f.decode().split()[-1] for f in folders]
                    sel_folder = st.selectbox("Select Folder", clean_folders, index=clean_folders.index("INBOX") if "INBOX" in clean_folders else 0)

                    with st.expander("Settings & Advanced Processing", expanded=True):
                        c1, c2 = st.columns(2)
                        with c1:
                            start_from = st.number_input("Start index", min_value=1, value=1)
                            dl_count = st.number_input("Count", min_value=1, value=10)
                            rep_dom = st.checkbox("Change From Domain")
                            p_from = st.text_input("Tag [P_FROM]", "[P_FROM]") if rep_dom else ""
                            mod_subject = st.checkbox("Modify Subject")
                            subj_new = st.text_input("New Subject", "[S]") if mod_subject else ""
                        with c2:
                            rep_body_dom = st.checkbox("Custom Body Domain (Advanced)")
                            p_domain = st.text_input("New Body Tag", "[P_DOMAIN]") if rep_body_dom else ""
                            rm_empty = st.checkbox("Remove Empty Lines (Body)", value=True)
                            
                            std_hdrs = st.checkbox("Set To/Date tags")
                            clean_auth = st.checkbox("Remove Auth Headers")
                            headers_only = st.checkbox("Headers Only")
                        
                        custom_hdrs = st.text_area("Custom Headers (Key:Value)")
                        zip_filename = st.text_input("ZIP Name", "processed_emails")

                    if st.button("Start Download & Process", type="primary", use_container_width=True):
                        mail.select(f'"{sel_folder}"', readonly=True)
                        _, data = mail.search(None, 'ALL')
                        ids = data[0].split()[::-1][start_from-1 : start_from-1+dl_count]
                        
                        if not ids: st.error("No emails found.")
                        else:
                            zbuf = io.BytesIO()
                            pbar = st.progress(0)
                            with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as zf:
                                for i, eid in enumerate(ids):
                                    try:
                                        _, md = mail.fetch(eid, '(RFC822)')
                                        raw = md[0][1]
                                        # Split Header / Body
                                        sep = b'\r\n\r\n' if b'\r\n\r\n' in raw else b'\n\n'
                                        raw_head, body = raw.split(sep, 1) if sep in raw else (raw, b'')
                                        
                                        h_text = raw_head.decode('utf-8', 'replace')
                                        h_lines = h_text.split('\r\n' if b'\r\n' in sep else '\n')
                                        orig_subj = email.message_from_string(h_text).get('Subject', 'no_subject')

                                        # Header Modifications
                                        if rep_dom:
                                            for idx, l in enumerate(h_lines):
                                                if l.lower().startswith('from:'): h_lines[idx] = re.sub(r'@[a-zA-Z0-9.\-]+', f'@{p_from}', l)
                                        if std_hdrs: h_lines = set_header_lines(h_lines, 'To', '[*to]'); h_lines = set_header_lines(h_lines, 'Date', '[*date]')
                                        if clean_auth:
                                            for h in ['DKIM-Signature','Authentication-Results','Received-SPF','ARC-Authentication-Results','ARC-Message-Signature','ARC-Seal']: h_lines = remove_header_lines(h_lines, h)
                                        if mod_subject: h_lines = set_header_lines(h_lines, 'Subject', subj_new)
                                        if custom_hdrs:
                                            for cl in custom_hdrs.split('\n'):
                                                if ':' in cl: k, v = cl.split(':', 1); h_lines = set_header_lines(h_lines, k.strip(), v.strip())

                                        # Body Processing (Domains + Empty Lines)
                                        if not headers_only and body:
                                            is_qp = any('quoted-printable' in hl.lower() for hl in h_lines if 'content-transfer-encoding' in hl.lower())
                                            b_text = quopri.decodestring(body).decode('utf-8', 'ignore') if is_qp else body.decode('utf-8', 'ignore')
                                            
                                            if rep_body_dom:
                                                dom_reg = r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}'
                                                b_text = re.sub(dom_reg, lambda m: m.group(0) if m.group(0).lower() in ['utf-8','text/html','text/plain'] else p_domain, b_text)
                                            
                                            if rm_empty:
                                                b_text = "\n".join([line for line in b_text.splitlines() if line.strip()])

                                            body = quopri.encodestring(b_text.encode('utf-8')) if is_qp else b_text.encode('utf-8')
                                        elif headers_only: body = b''

                                        # Final Join: NO BLANK LINE (Directly attach body after last header line)
                                        nl_str = ('\r\n' if b'\r\n' in sep else '\n')
                                        final_raw = nl_str.join(h_lines).encode('utf-8') + nl_str.encode('utf-8') + body
                                        
                                        zf.writestr(f"{i+1}_{clean_filename(orig_subj)}.txt", final_raw)
                                        pbar.progress((i+1)/len(ids))
                                    except: continue
                            
                            st.success("Complete!")
                            st.download_button("Download ZIP File", zbuf.getvalue(), f"{zip_filename}.zip", use_container_width=True)
                finally:
                    try: mail.logout()
                    except: pass

with tab3:
    if os.path.exists("cmh1-pro.html"):
        with open("cmh1-pro.html", "r", encoding="utf-8") as f:
            components.html(f.read(), height=920, scrolling=True)
    else:
        st.error("cmh1-pro.html ma kaynch!")
