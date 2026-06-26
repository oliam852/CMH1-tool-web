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
# ==========================================
# TAB 2 — IMAP (Updated with Header Filter)
# ==========================================
with tab2:
    # ... (Keep existing helper functions: decode_header_text, clean_filename, etc.)

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
            Download and process raw email headers with filtering
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

    with col2:
        if st.session_state.get('mail_connected'):
            email_user = st.session_state.get('saved_email')
            app_pass   = st.session_state.get('saved_password')

            mail = connect_imap(email_user, app_pass)
            if mail:
                try:
                    # Folder Selection
                    cache_key = f"folders_{email_user}"
                    if cache_key not in st.session_state or st.session_state.get('refresh_folders'):
                        _, folders = mail.list()
                        clean_folders = [ (re.search(r'"([^"]+)"$', f.decode()) or re.search(r' ([^ ]+)$', f.decode())).group(1) for f in folders ]
                        st.session_state[cache_key] = clean_folders
                        st.session_state['refresh_folders'] = False
                    
                    clean_folders = st.session_state[cache_key]
                    sel_folder = st.selectbox("Select Folder", clean_folders, index=next((i for i, f in enumerate(clean_folders) if f == "INBOX"), 0))

                    # --- NEW FILTER SECTION ---
                    st.markdown("### 🔍 Filter by Header Parameter")
                    use_filter = st.checkbox("Enable Search Filter (Only download specific emails)")
                    search_query = "ALL"
                    
                    if use_filter:
                        f_col1, f_col2 = st.columns(2)
                        with f_col1:
                            h_key = st.text_input("Header Name", value="In-Reply-To", help="e.g. In-Reply-To, References, X-Mailer")
                        with f_col2:
                            h_val = st.text_input("Header Value", value="", help="Value to search for (partial match)")
                        
                        if h_key:
                            search_query = f'(HEADER "{h_key}" "{h_val}")'
                    
                    # Check Count Button
                    if st.button("Check Matching Emails Count"):
                        mail.select(f'"{sel_folder}"', readonly=True)
                        typ, data = mail.search(None, search_query)
                        if typ == 'OK':
                            found_ids = data[0].split()
                            st.info(f"Found **{len(found_ids)}** emails matching your criteria.")
                        else:
                            st.error("Error searching.")

                    with st.expander("Settings — Download & Preservation", expanded=True):
                        cr1, cr2 = st.columns(2)
                        with cr1:
                            dl_count = st.number_input("How many to download (from newest)", min_value=1, value=10)
                        with cr2:
                            zip_filename = st.text_input("ZIP Name", value="filtered_emails")

                        st.markdown("---")
                        c1, c2 = st.columns(2)
                        with c1:
                            rep_dom = st.checkbox("Change 'From' Domain")
                            p_from = st.text_input("Tag [P_FROM]", value="[P_FROM]") if rep_dom else "[P_FROM]"
                            mod_subject = st.checkbox("Modify Subject")
                            subj_new_value = st.text_input("New Subject") if mod_subject else ""
                            extract_plain = st.checkbox("Extract Body Only")
                        with c2:
                            std_hdrs = st.checkbox("Set To=[*to], Date=[*date]")
                            clean_auth = st.checkbox("Remove DKIM/SPF headers")
                            headers_only = st.checkbox("Headers Only")
                            det_dupes = st.checkbox("Remove Duplicates")

                    # START PROCESSING
                    if st.button("Start Download & Process", type="primary", use_container_width=True):
                        mail.select(f'"{sel_folder}"', readonly=True)
                        # Use the search_query (either ALL or specific header)
                        typ, data = mail.search(None, search_query)
                        
                        if typ != 'OK' or not data[0]:
                            st.error("No emails found with this filter.")
                        else:
                            id_list = data[0].split()
                            id_list.reverse() # Newest first
                            id_list = id_list[:dl_count] # Limit to dl_count
                            
                            st.info(f"Processing {len(id_list)} emails...")
                            pbar = st.progress(0)
                            
                            fetched_emails = []
                            for i, eid in enumerate(id_list):
                                try:
                                    _, md = mail.fetch(eid, '(RFC822)')
                                    raw_bytes = md[0][1]
                                    em = email.message_from_bytes(raw_bytes)
                                    fetched_emails.append({'msg': em, 'id': eid, 'raw': raw_bytes})
                                    pbar.progress((i + 1) / len(id_list) * 0.5)
                                except: continue

                            if det_dupes:
                                fetched_emails, _ = detect_duplicates(fetched_emails)

                            # Create ZIP
                            zbuf = io.BytesIO()
                            with zipfile.ZipFile(zbuf, "w", zipfile.ZIP_DEFLATED) as zf:
                                for i, ed in enumerate(fetched_emails):
                                    # ... (Same logic as your code to process headers/body)
                                    # [Keep the rest of your original logic for building the ZIP here]
                                    # For brevity, I'm just showing the filter part
                                    raw = ed['raw']
                                    # [Header modification logic as per your original file]
                                    zf.writestr(f"mail_{i+1}.txt", raw) # Example
                                    pbar.progress(0.5 + (i + 1) / len(fetched_emails) * 0.5)

                            st.success("Done!")
                            st.download_button("Download ZIP", zbuf.getvalue(), f"{zip_filename}.zip")

                finally:
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
