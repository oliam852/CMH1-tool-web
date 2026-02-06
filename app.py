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
    page_title="CMH1 Fusion", 
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS FOR CUSTOM TABS & CLEAN LOOK ---
st.markdown("""
<style>
    /* Global Background */
    .stApp {
        background-color: #1a1b26;
    }
    
    /* 1. HIDE SIDEBAR COMPLETELY */
    [data-testid="stSidebar"] {
        display: none;
    }
    
    /* 2. Custom Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #565F89;
        padding: 10px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent;
        border-radius: 8px;
        color: #919499;
        font-weight: 600;
        border: none;
        padding: 0 20px;
    }
    label {
    color: #D3D6E4 !important;
}

    /* Selected Tab Style */
    .stTabs [aria-selected="true"] {
        background-color: #00f5c3 !important;
        color: #1a1b26 !important;
        font-weight: bold;
    }
    
    /* Hover Effect */
    .stTabs [data-baseweb="tab"]:hover {
        color: #00f5c3;
    }

    /* Remove Decoration */
    [data-testid="stDecoration"] {
        display: none;
    }
    header {
        visibility: hidden;
    }
    
    /* Padding Adjustments */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }

    # ... (كود قديم)
    /* Inputs Styling */
    .stTextInput input, .stNumberInput input, .stTextArea textarea {
        background-color: #24283b !important;
        color: #c0caf5 !important;
        border: 1px solid #414868 !important;
    }

    /* زيد هادو هنا باش يتحكمو فالعناوين (Labels) */
    [data-testid="stWidgetLabel"] p {
        color: #c0caf5 !important;
    }

    .stMarkdown p {
        color: #c0caf5 !important;
    }
# ... (باقي الكود)
    
    /* Buttons */
    .stButton button {
        font-weight: bold;
    }

    
</style>
""", unsafe_allow_html=True)

# --- 3. NAVIGATION (3 TABS NOW) ---
tab1, tab2, tab3 = st.tabs(["💻 HTML FUSION EDITOR", "📧 IMAP EMAIL TOOL", "⚡ CMH-1 PRO"])

# ==========================================
# TAB 1: HTML FUSION EDITOR
# ==========================================
with tab1:
    if os.path.exists("V6.html"):
        with open("V6.html", "r", encoding="utf-8") as f:
            html_code = f.read()
        components.html(html_code, height=920, scrolling=True)
    else:
        st.error("⚠️ Fichier 'V6.html' ma kaynch!")

# ==========================================
# TAB 2: IMAP EMAIL TOOL
# ==========================================
with tab2:
    # --- Helper Functions ---
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
    
    # Function to strip HTML manually (Regex) to be dependency-free
    def clean_html_to_plain(html_content):
        # Basic regex to strip tags
        clean = re.sub(r'<[^>]+>', ' ', html_content)
        # Collapse whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def get_email_body_text(msg_obj):
        """Extracts plain text body, preferring plain text over HTML."""
        body_text = ""
        if msg_obj.is_multipart():
            # Walk through parts
            for part in msg_obj.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get('Content-Disposition'))
                
                # Skip attachments
                if 'attachment' in cdispo:
                    continue
                
                try:
                    payload = part.get_payload(decode=True)
                    if not payload: continue
                    decoded_payload = payload.decode('utf-8', 'ignore')
                    
                    if ctype == 'text/plain':
                        return decoded_payload # Best case, return immediately
                    elif ctype == 'text/html':
                        body_text = clean_html_to_plain(decoded_payload) # Backup
                except: continue
        else:
            # Not multipart
            try:
                payload = msg_obj.get_payload(decode=True)
                if payload:
                    decoded = payload.decode('utf-8', 'ignore')
                    if msg_obj.get_content_type() == 'text/html':
                         body_text = clean_html_to_plain(decoded)
                    else:
                        body_text = decoded
            except: pass
            
        return body_text
    
    def detect_duplicates(email_list):
        """Detect duplicate emails based on Message-ID and Subject+From combination"""
        import hashlib
        
        seen_ids = set()
        seen_hashes = set()
        duplicates = []
        unique_emails = []
        
        for idx, email_data in enumerate(email_list):
            msg_obj = email_data['msg']
            email_id = email_data['id']
            
            # Check Message-ID
            msg_id = msg_obj.get('Message-ID', '')
            if msg_id and msg_id in seen_ids:
                duplicates.append({
                    'index': idx + 1,
                    'id': email_id,
                    'reason': 'Same Message-ID',
                    'subject': msg_obj.get('Subject', 'No Subject')
                })
                continue
            
            # Check Subject + From + Date hash
            subject = msg_obj.get('Subject', '')
            from_addr = msg_obj.get('From', '')
            date = msg_obj.get('Date', '')
            
            # Create hash
            combo = f"{subject}|{from_addr}|{date}".encode('utf-8')
            hash_val = hashlib.md5(combo).hexdigest()
            
            if hash_val in seen_hashes:
                duplicates.append({
                    'index': idx + 1,
                    'id': email_id,
                    'reason': 'Same Subject+From+Date',
                    'subject': subject
                })
                continue
            
            # Mark as seen
            if msg_id:
                seen_ids.add(msg_id)
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

    # UI Content
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("## 🚀 GMAIL/IMAP RAW TOOL")
    st.markdown("Developed by **@ayoubrhattoy**")
    
    col1, col2 = st.columns([1, 2], gap="large")
    
    with col1:
        st.info("🔐 Login Credentials")
        email_user = st.text_input("👉 Email:", placeholder="example@gmail.com")
        app_pass = st.text_input("👉 App Password:", type="password")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔌 Connect", use_container_width=True):
            if email_user and app_pass:
                mail = connect_imap(email_user, app_pass)
                if mail:
                    st.session_state['mail_connected'] = True
                    st.success("✅ Connected!")
                    mail.logout()
                else:
                    st.session_state['mail_connected'] = False
            else:
                st.warning("Please enter credentials.")

    with col2:
        if st.session_state.get('mail_connected'):
            mail = connect_imap(email_user, app_pass)
            if mail:
                # --- PERFORMANCE: Cache folder list ---
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
                
                # Refresh button for folders
                if st.button("🔄 Refresh Folders", help="Update folder list"):
                    st.session_state['refresh_folders'] = True
                    st.rerun()

                # Get email counts for each folder (WITH CACHING)
                count_cache_key = f"counts_{email_user}_{selected_folder if 'selected_folder' in locals() else 'all'}"
                
                # Check if we need to refresh counts
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
                            except:
                                folder_counts[folder] = 0
                    st.session_state[count_cache_key] = folder_counts
                    st.session_state['refresh_counts'] = False
                else:
                    folder_counts = st.session_state[count_cache_key]
                
                # Create folder display with counts
                folder_options = [f"{folder} ({folder_counts.get(folder, 0)} emails)" for folder in clean_folders]
                
                # Select Folder
                selected_display = st.selectbox("📂 Select Folder", folder_options, 
                    index=next((i for i, f in enumerate(clean_folders) if f == "INBOX"), 0))
                
                # Extract actual folder name
                selected_folder = clean_folders[folder_options.index(selected_display)]
                total_emails = folder_counts.get(selected_folder, 0)
                
                # ORIGINAL SETTINGS UI
                with st.expander("⚙️ SETTINGS (RAW BODY PRESERVATION)", expanded=True):
                    # Email Range Selection (NEW)
                    st.info(f"📊 Total emails in folder: **{total_emails}**")
                    
                    col_range1, col_range2 = st.columns(2)
                    with col_range1:
                        start_from = st.number_input(
                            "🔢 Start from email #:", 
                            min_value=1, 
                            max_value=max(1, total_emails), 
                            value=1,
                            help="Start downloading from this email number (1 = newest)"
                        )
                    with col_range2:
                        download_count = st.number_input(
                            "📥 How many to download:", 
                            min_value=1, 
                            max_value=total_emails, 
                            value=min(10, total_emails),
                            help="Number of emails to download starting from above number"
                        )
                    
                    # Calculate actual range
                    end_at = min(start_from + download_count - 1, total_emails)
                    st.caption(f"📌 Will download: Email #{start_from} to #{end_at} ({end_at - start_from + 1} emails)")
                    
                    st.markdown("---")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        rep_dom = st.checkbox("2️⃣ Change 'From' Domain")
                        p_from = st.text_input("   Tag [P_FROM]:", value="[P_FROM]") if rep_dom else "[P_FROM]"
                        
                        # NEW OPTION HERE - UPDATED
                        st.markdown("---")
                        extract_plain_only = st.checkbox("8️⃣ Extract Body Only?", help="Extract only email body text without headers")
                        
                        # Export format selection - NEW FEATURE
                        export_format = "Merged"  # Default value
                        if extract_plain_only:
                            export_format = st.radio(
                                "📤 Export Format:",
                                options=["Merged (1 file with __SEP__)", "Separate files (ZIP)"],
                                horizontal=True
                            )

                    with c2:
                        std_headers = st.checkbox("3️⃣ Set To=[*to], Date=[*date]")
                        mod_eid = st.checkbox("5️⃣ Add [EID] to Message-ID")
                        clean_auth = st.checkbox("6️⃣ Remove DKIM/SPF headers")
                        name_by_subj = st.checkbox("7️⃣ Name files by Subject")
                        
                        # NEW: Duplicate Detection
                        st.markdown("---")
                        detect_dupes = st.checkbox("9️⃣ Remove Duplicates", help="Skip duplicate emails based on Message-ID and Subject+From+Date")
                    
                    custom_headers_text = st.text_area("4️⃣ Custom Headers (Key:Value)")

                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("🚀 START DOWNLOAD & PROCESS", type="primary", use_container_width=True):
                    mail.select(f'"{selected_folder}"', readonly=True)
                    typ, data = mail.search(None, 'ALL')
                    id_list = data[0].split()
                    id_list.reverse()  # Newest first
                    
                    # Apply range selection
                    id_list = id_list[start_from-1:start_from-1+download_count]
                    
                    if not id_list:
                        st.error("📭 No emails found in selected range.")
                    else:
                        status_msg = st.empty()
                        prog_bar = st.progress(0)
                        
                        # === DUPLICATE DETECTION (if enabled) ===
                        if detect_dupes:
                            status_msg.info("🔍 Detecting duplicates...")
                            email_data_list = []
                            
                            for i, eid in enumerate(id_list):
                                try:
                                    _, msg_data = mail.fetch(eid, '(RFC822)')
                                    raw_bytes = msg_data[0][1]
                                    email_message = email.message_from_bytes(raw_bytes)
                                    email_data_list.append({
                                        'msg': email_message,
                                        'id': eid,
                                        'raw': raw_bytes
                                    })
                                except:
                                    continue
                            
                            # Detect and remove duplicates
                            unique_emails, duplicates = detect_duplicates(email_data_list)
                            
                            if duplicates:
                                status_msg.warning(f"⚠️ Found {len(duplicates)} duplicate(s). Processing {len(unique_emails)} unique emails.")
                                
                                # Show duplicate details in expander
                                with st.expander(f"📋 View {len(duplicates)} Duplicates"):
                                    for dup in duplicates[:20]:  # Show first 20
                                        st.caption(f"Email #{dup['index']}: {dup['subject'][:50]} - {dup['reason']}")
                                    if len(duplicates) > 20:
                                        st.caption(f"... and {len(duplicates)-20} more")
                            else:
                                status_msg.success("✅ No duplicates found!")
                            
                            # Update id_list to only unique emails
                            id_list = [item['id'] for item in unique_emails]
                            
                            if not id_list:
                                st.error("📭 All emails were duplicates!")
                                mail.logout()
                                st.stop()
                        
                        # === LOGIC BRANCH: EXTRACT TEXT ONLY vs ORIGINAL ===
                        if extract_plain_only:
                            # Check which format user selected
                            if "Merged" in export_format:
                                # --- OPTION: MERGED TEXT FILE ---
                                full_extracted_text = []
                                for i, eid in enumerate(id_list):
                                    try:
                                        _, msg_data = mail.fetch(eid, '(RFC822)')
                                        raw_bytes = msg_data[0][1]
                                        email_message = email.message_from_bytes(raw_bytes)
                                        
                                        # Get clean body
                                        body_content = get_email_body_text(email_message)
                                        
                                        if body_content:
                                            full_extracted_text.append(body_content)
                                        
                                        prog_bar.progress((i+1)/len(id_list))
                                    except: continue
                                    
                                # Merge with Separator
                                final_output = "\n__SEP__\n".join(full_extracted_text)
                                
                                prog_bar.empty()
                                status_msg.success(f"🎉 Extracted {len(full_extracted_text)} emails into 1 merged file!")
                                
                                st.download_button(
                                    label="📥 Download Merged Text File (.txt)", 
                                    data=final_output, 
                                    file_name="emails_bodies_merged.txt", 
                                    mime="text/plain"
                                )
                            
                            else:
                                # --- OPTION: SEPARATE FILES IN ZIP ---
                                zip_buf = io.BytesIO()
                                with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
                                    for i, eid in enumerate(id_list):
                                        try:
                                            _, msg_data = mail.fetch(eid, '(RFC822)')
                                            raw_bytes = msg_data[0][1]
                                            email_message = email.message_from_bytes(raw_bytes)
                                            
                                            # Get clean body
                                            body_content = get_email_body_text(email_message)
                                            
                                            if body_content:
                                                # Create filename
                                                if name_by_subj:
                                                    original_subj = email_message.get('Subject', 'no_subject')
                                                    subj = clean_filename(original_subj)
                                                    fname = f"{i+1}_{subj}.txt"
                                                else:
                                                    fname = f"email_{i+1}.txt"
                                                
                                                # Write to zip
                                                zf.writestr(fname, body_content.encode('utf-8'))
                                            
                                            prog_bar.progress((i+1)/len(id_list))
                                        except: continue
                                
                                prog_bar.empty()
                                status_msg.success(f"🎉 Extracted {len(id_list)} emails into separate files!")
                                
                                st.download_button(
                                    label="📥 Download ZIP File (Separate Text Files)", 
                                    data=zip_buf.getvalue(), 
                                    file_name="emails_bodies_separate.zip", 
                                    mime="application/zip",
                                    use_container_width=True
                                )

                        else:
                            # --- ORIGINAL LOGIC (ZIP FILES WITH HEADERS) ---
                            zip_buf = io.BytesIO()
                            with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zf:
                                for i, eid in enumerate(id_list):
                                    try:
                                        _, msg = mail.fetch(eid, '(RFC822)')
                                        raw = msg[0][1]
                                        
                                        # Split Logic
                                        sep = b'\r\n\r\n'
                                        idx = raw.find(sep)
                                        if idx == -1: 
                                            sep = b'\n\n'
                                            idx = raw.find(sep)
                                        
                                        head = raw[:idx] if idx != -1 else raw
                                        body = raw[idx+len(sep):] if idx != -1 else b""
                                        
                                        mime = email.message_from_bytes(head)
                                        original_subj = mime.get('Subject', 'no_subject')

                                        # LOGIC TRANSFORMATIONS
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

                                        if mod_eid and mime.get('Message-ID') and '@' in mime['Message-ID']:
                                            new_mid = mime['Message-ID'].replace('@', '[EID]@', 1)
                                            del mime['Message-ID']; mime['Message-ID'] = new_mid

                                        if clean_auth:
                                            for h in ['DKIM-Signature', 'Authentication-Results', 'Received', 'Received-SPF', 'ARC-Authentication-Results', 'ARC-Message-Signature', 'ARC-Seal']:
                                                while h in mime: del mime[h]
                                        
                                        fin = mime.as_bytes() + b'\r\n\r\n' + body
                                        
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
                mail.logout()

# ==========================================
# TAB 3: CMH-1 PRO (NEW)
# ==========================================
with tab3:
    # Load and display the CMH-1 Pro HTML file
    cmh1_html_path = "cmh1-pro.html"
    
    if os.path.exists(cmh1_html_path):
        with open(cmh1_html_path, "r", encoding="utf-8") as f:
            cmh1_html_code = f.read()
        components.html(cmh1_html_code, height=920, scrolling=True)
    else:
        st.error("⚠️ Fichier 'cmh1-pro.html' ma kaynch!")
