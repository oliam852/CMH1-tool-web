import streamlit as st
import os
import re
import email
import imaplib
import shutil
import base64
import time
from email.header import decode_header
import zipfile
import io

# --- CONFIGURATION DIAL PAGE ---
st.set_page_config(page_title="IMAP Email Tool", page_icon="📧", layout="centered")

# --- FONCTIONS (Mkhbbyin bach mayt3wdch l'code) ---

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

# --- WAJIHAT TATBIQ (UI) ---

st.title("🚀 GMAIL/IMAP RAW TOOL")
st.markdown("Developed by **@ayoubrhattoy**")

# 1. SIDEBAR (Login)
st.sidebar.header("🔐 Login Credentials")
email_user = st.sidebar.text_input("Email", placeholder="example@gmail.com")
app_pass = st.sidebar.text_input("App Password", type="password", help="Dir App Password machi mot de passe 3adi")

if not email_user or not app_pass:
    st.warning("👈 Bda b Login f Sidebar 3la lissr.")
    st.stop()

# 2. CONNECT
if st.sidebar.button("🔌 Connect"):
    mail = connect_imap(email_user, app_pass)
    if mail:
        st.session_state['mail_connected'] = True
        st.sidebar.success("✅ Connected!")
        mail.logout()
    else:
        st.session_state['mail_connected'] = False

if not st.session_state.get('mail_connected'):
    st.info("Please connect to fetch folders.")
    st.stop()

# Reconnect pour l'execution réelle
mail = connect_imap(email_user, app_pass)

# 3. SELECT FOLDER
status, folders = mail.list()
clean_folders = []
for folder in folders:
    folder_str = folder.decode()
    match = re.search(r'"([^"]+)"$', folder_str) or re.search(r' ([^ ]+)$', folder_str)
    if match: clean_folders.append(match.group(1))
    else: clean_folders.append(folder_str)

selected_folder = st.selectbox("📂 Select Folder", clean_folders, index=clean_folders.index("INBOX") if "INBOX" in clean_folders else 0)

# 4. SETTINGS
st.divider()
st.subheader("⚙️ Settings")

col1, col2 = st.columns(2)
with col1:
    max_results = st.number_input("Count (Combien d'emails ?)", min_value=1, value=10)
    rep_dom = st.checkbox("Change 'From' Domain?")
    p_from = "[P_FROM]"
    if rep_dom:
        p_from = st.text_input("Tag Domain", value="[P_FROM]")

with col2:
    std_headers = st.checkbox("Set To=[*to], Date=[*date]?")
    mod_eid = st.checkbox("Add [EID] to Message-ID?")
    clean_auth = st.checkbox("Remove DKIM/SPF headers?")
    name_by_subj = st.checkbox("Name files by Subject?")

# Custom Headers
custom_headers_text = st.text_area("Custom Headers (Format: Key:Value)", help="Header1:Value1\nHeader2:Value2")

# 5. EXECUTION
if st.button("🚀 START DOWNLOAD & PROCESS"):
    
    # Select Folder
    mail.select(f'"{selected_folder}"', readonly=True)
    
    # Search
    typ, data = mail.search(None, 'ALL')
    id_list = data[0].split()
    id_list.reverse()
    id_list = id_list[:max_results]
    
    if not id_list:
        st.error("📭 No emails found.")
    else:
        # Progress Bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # In-Memory Zip
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            
            for i, email_id in enumerate(id_list):
                try:
                    status_text.text(f"Processing email {i+1}/{len(id_list)}...")
                    typ, msg_data = mail.fetch(email_id, '(RFC822)')
                    raw_bytes = msg_data[0][1]

                    # Separation Body/Header
                    separator = b'\r\n\r\n'
                    split_index = raw_bytes.find(separator)
                    if split_index == -1:
                        separator = b'\n\n'
                        split_index = raw_bytes.find(separator)

                    if split_index != -1:
                        header_bytes = raw_bytes[:split_index]
                        body_content_only = raw_bytes[split_index + len(separator):]
                    else:
                        header_bytes = raw_bytes
                        body_content_only = b""

                    mime_headers = email.message_from_bytes(header_bytes)
                    original_subject = mime_headers.get('Subject', 'no_subject')

                    # MODIFICATIONS
                    if rep_dom and mime_headers.get('From'):
                        new_from = re.sub(r'@[a-zA-Z0-9.-]+', f'@{p_from}', mime_headers['From'])
                        del mime_headers['From']
                        mime_headers['From'] = new_from

                    if std_headers:
                        if 'To' in mime_headers: del mime_headers['To']
                        mime_headers['To'] = '[*to]'
                        if 'Date' in mime_headers: del mime_headers['Date']
                        mime_headers['Date'] = '[*date]'
                    
                    # Custom Headers
                    if custom_headers_text:
                        for line in custom_headers_text.split('\n'):
                            if ":" in line:
                                k, v = line.split(":", 1)
                                if k.strip() in mime_headers: del mime_headers[k.strip()]
                                mime_headers[k.strip()] = v.strip()

                    if mod_eid and mime_headers.get('Message-ID') and '@' in mime_headers['Message-ID']:
                        new_mid = mime_headers['Message-ID'].replace('@', '[EID]@', 1)
                        del mime_headers['Message-ID']
                        mime_headers['Message-ID'] = new_mid

                    if clean_auth:
                        for h in ['DKIM-Signature', 'Authentication-Results', 'Received', 'Received-SPF', 'ARC-Authentication-Results', 'ARC-Message-Signature', 'ARC-Seal']:
                            while h in mime_headers: del mime_headers[h]

                    final_bytes = mime_headers.as_bytes() + b'\r\n\r\n' + body_content_only

                    # Naming
                    fname = f"email_{i+1}.txt"
                    if name_by_subj:
                        subj = clean_filename(original_subject)
                        fname = f"{i+1}_{subj}.txt"

                    # Add to Zip
                    zip_file.writestr(fname, final_bytes)
                    
                    # Update Progress
                    progress_bar.progress((i + 1) / len(id_list))

                except Exception as e:
                    st.error(f"Error on email {i+1}: {e}")
                    continue

        status_text.text("✅ Processing Complete!")
        
        # DOWNLOAD BUTTON
        st.success("🎉 Emails processed successfully!")
        st.download_button(
            label="📥 Download ZIP File",
            data=zip_buffer.getvalue(),
            file_name="emails_processed.zip",
            mime="application/zip"
        )

    mail.logout()