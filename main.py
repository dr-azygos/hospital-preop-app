import streamlit as st
import urllib.parse
from datetime import datetime, timedelta
import json
from github import Github
import uuid

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Pre-Op Dispatcher", page_icon="👁️", layout="wide")

# --- DR. AZYGOS WATERMARK ---
st.markdown(
    """
    <style>
    .watermark { position: fixed; bottom: 20px; left: 20px; font-size: 16px; color: #888888; z-index: 999999; pointer-events: none; font-style: italic; font-weight: bold; }
    </style>
    <div class="watermark">Designed by dr.azygos</div>
    """, unsafe_allow_html=True
)

# --- 🔒 SECURITY GATE ---
HOSPITAL_PASSWORD = "123" 
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Authorized Personnel Only")
    st.info("Please enter the staff password to access the dispatch queue.")
    pwd = st.text_input("Password", type="password")
    if st.button("Unlock Dashboard", type="primary"):
        if pwd == HOSPITAL_PASSWORD:
            st.session_state.authenticated = True
            st.rerun() 
        else:
            st.error("❌ Incorrect Password.")
    st.stop() 

# --- HOSPITAL CONSTANTS & MEMORY ---
if 'patient_list' not in st.session_state:
    st.session_state.patient_list = []

BRANCHES = ["New Colony", "Mihan"]
ANESTHESIA_OPTS = ["Local Anesthesia (LA)", "Fasting (NPM)"]
COMORB_OPTS = ["None (No HTN, No DM)", "Only HTN", "Only DM", "Both HTN & DM"]

start_time = datetime.strptime("07:45 AM", "%I:%M %p")
TIME_OPTIONS = [(start_time + timedelta(minutes=15*i)).strftime("%I:%M %p") for i in range(42)]

def delete_patient(index):
    st.session_state.patient_list.pop(index)

# --- CLOUD DATABASE FUNCTIONS ---
def get_github_repo():
    g = Github(st.secrets["GITHUB_TOKEN"])
    return g.get_repo(st.secrets["GITHUB_REPO"])

def save_to_cloud(data_list):
    try:
        repo = get_github_repo()
        contents = repo.get_contents("database.json")
        json_string = json.dumps(data_list, indent=4)
        repo.update_file(contents.path, "Backup from App", json_string, contents.sha)
        return True
    except Exception as e:
        st.error(f"Cloud Save Error: {e}")
        return False

def load_from_cloud():
    try:
        repo = get_github_repo()
        contents = repo.get_contents("database.json")
        return json.loads(contents.decoded_content.decode("utf-8"))
    except Exception as e:
        st.error(f"Cloud Load Error: {e}")
        return []

# --- 🪄 NEW: THE POP-UP EDIT BOX ---
@st.dialog("✏️ Edit Patient Details")
def edit_patient_dialog(pt, index):
    st.markdown(f"**Editing:** {pt['Name']}")
    
    e_name = st.text_input("Name", pt['Name'])
    e_phone = st.text_input("Phone", pt['Phone'])
    e_branch = st.selectbox("Branch", BRANCHES, index=BRANCHES.index(pt['Branch']) if pt['Branch'] in BRANCHES else 0)
    
    saved_date = datetime.strptime(pt['Date'], "%d.%m.%Y").date()
    e_date = st.date_input("Date", saved_date)
    
    e_time = st.selectbox("Time", TIME_OPTIONS, index=TIME_OPTIONS.index(pt['Time']) if pt['Time'] in TIME_OPTIONS else 0)
    e_anes = st.radio("Anesthesia", ANESTHESIA_OPTS, index=ANESTHESIA_OPTS.index(pt['Anesthesia']) if pt['Anesthesia'] in ANESTHESIA_OPTS else 0)
    e_comorb = st.selectbox("Comorbidities", COMORB_OPTS, index=COMORB_OPTS.index(pt['Comorbidities']) if pt['Comorbidities'] in COMORB_OPTS else 0)
    
    if st.button("💾 Apply Changes", type="primary", use_container_width=True):
        st.session_state.patient_list[index].update({
            "Name": e_name, "Phone": e_phone, "Branch": e_branch,
            "Date": e_date.strftime("%d.%m.%Y"), "Time": e_time,
            "Anesthesia": e_anes, "Comorbidities": e_comorb,
            "version": pt["version"] + 1  # Forces the text box to refresh instantly
        })
        st.rerun()

# --- SIDEBAR: DATA ENTRY ---
with st.sidebar:
    st.header("➕ Add New Patient")
    
    with st.form("patient_form", clear_on_submit=True):
        patient_name = st.text_input("Patient Name*")
        phone_number = st.text_input("WhatsApp Number*", value="91", help="Country code + number") 
        branch = st.selectbox("Hospital Branch", BRANCHES)
        
        tomorrow = datetime.now() + timedelta(days=1)
        surgery_date = st.date_input("Date of Surgery", value=tomorrow)
        reporting_time = st.selectbox("Reporting Time", TIME_OPTIONS)
        
        st.markdown("### Clinical Details")
        anesthesia = st.radio("Anesthesia / Diet", ANESTHESIA_OPTS)
        comorbidities = st.selectbox("Comorbidities", COMORB_OPTS)
        
        submitted = st.form_submit_button("Add to Queue", type="primary", use_container_width=True)

        if submitted:
            if not patient_name or phone_number.strip() == "" or phone_number == "91":
                st.error("⚠️ Please provide a valid name and number.")
            else:
                st.session_state.patient_list.append({
                    "id": str(uuid.uuid4()), 
                    "version": 1, 
                    "Name": patient_name, "Phone": phone_number.replace("+", ""), "Branch": branch,
                    "Date": surgery_date.strftime("%d.%m.%Y"), "Time": reporting_time,
                    "Anesthesia": anesthesia, "Comorbidities": comorbidities
                })
                st.success(f"Added {patient_name}!")

    # --- CLOUD SYNC BUTTONS ---
    st.divider()
    st.header("☁️ Cloud Sync")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save", use_container_width=True):
            with st.spinner("Saving..."):
                if save_to_cloud(st.session_state.patient_list):
                    st.success("Saved!")
    with col2:
        if st.button("🔄 Load", use_container_width=True):
            with st.spinner("Loading..."):
                st.session_state.patient_list = load_from_cloud()
                st.rerun()

# --- MAIN DASHBOARD: THE QUEUE ---
st.title("📋 Surgery Dispatch Queue")

with st.expander("📲 Payment QR Code (Click here to open)", expanded=False):
    st.info("💡 Right-click the QR code below and select **'Copy Image'**. Paste (Ctrl+V) into WhatsApp before sending!")
    try:
        st.image("qrcode.jpg", width=300)
    except Exception:
        st.warning("⚠️ Cannot find 'qrcode.jpg'. Make sure it is on GitHub!")

if len(st.session_state.patient_list) == 0:
    st.info("👈 Your queue is empty. Start adding patients or click 'Load' in the sidebar.")
else:
    st.markdown(f"**Total Patients in Queue:** {len(st.session_state.patient_list)}")
    st.divider()

    for index, pt in enumerate(st.session_state.patient_list):
        
        # Backward compatibility
        if "id" not in pt: pt["id"] = str(uuid.uuid4())
        if "version" not in pt: pt["version"] = 1
        
        rep_time_obj = datetime.strptime(pt['Time'], "%I:%M %p")
        two_hours_prior = (rep_time_obj - timedelta(hours=2)).strftime("%I:%M %p")
        dos = pt['Date']
        
        # --- SURAJ EYE INSTITUTE MESSAGE LOGIC ---
        draft = f"Dear {pt['Name']},\nGreetings from Suraj Eye Institute, Nagpur.\nYour surgery has been scheduled on {dos}.\n\n"
        
        if pt['Anesthesia'] == "Local Anesthesia (LA)":
            if pt['Comorbidities'] == "None (No HTN, No DM)":
                draft += f"Have a light breakfast of sugarless tea and two Marie biscuits at {two_hours_prior}. Please bring all your reports. Also bring your fitness along."
            elif pt['Comorbidities'] == "Only DM":
                draft += f"You should have a very light breakfast at {two_hours_prior}. And have your Diabetes medication on {dos}. Please bring all your reports and your fitness. Kindly avoid taking aspirin and antiplatelet medication."
            elif pt['Comorbidities'] == "Only HTN":
                draft += f"Have a light breakfast at {two_hours_prior}. You need to take anti-hypertensive medication. Please bring all your reports and your fitness. Kindly avoid taking aspirin and antiplatelet medication."
            elif pt['Comorbidities'] == "Both HTN & DM":
                draft += f"You should have a very light breakfast at {two_hours_prior}. You need to take anti-hypertensive medication and Diabetes medication. Please bring all your reports and your fitness. Kindly avoid taking aspirin and antiplatelet medication."
                
        elif pt['Anesthesia'] == "Fasting (NPM)":
            if pt['Comorbidities'] == "None (No HTN, No DM)":
                draft += f"You should not eat anything after 12 am on {dos}. Please bring all your reports and your fitness. Kindly avoid taking aspirin and antiplatelet medication."
            elif pt['Comorbidities'] == "Only DM":
                draft += f"You should not eat anything after 12 am on {dos}. Do not have any Diabetes medication on {dos}. Please bring all your reports and your fitness. Kindly avoid taking aspirin and antiplatelet medication."
            elif pt['Comorbidities'] == "Only HTN":
                draft += f"You should not eat anything after 12 am on {dos}. You need to take anti-hypertensive medication with 50 ml (Quarter glass) water in the morning at {two_hours_prior} with 2 sips of water. Please bring all your reports and your fitness. Kindly avoid taking aspirin and antiplatelet medication."
            elif pt['Comorbidities'] == "Both HTN & DM":
                draft += f"You should not eat anything after 12 am on {dos}. You need to take anti-hypertensive medication with 50 ml (Quarter glass) water in the morning at {two_hours_prior} with 2 sips of water if taking, and not have any Diabetes medication on {dos}. Please bring all your reports and your fitness. Kindly avoid taking aspirin and antiplatelet medication."

        draft += f"\n\nReport to hospital at Suraj Eye Institute {pt['Branch']} branch at {pt['Time']}."
        draft += "\n\nKindly make your surgery payments using the UPI details above before surgery. Kind regards.\nSEI Services."

        # --- UI CARD ---
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                st.subheader(f"👤 {pt['Name']}")
                st.write(f"**{pt['Branch']}** | {dos} @ {pt['Time']}")
                st.caption(f"{pt['Anesthesia']} | {pt['Comorbidities']}")
                
                # Triggers the Pop-up Window!
                if st.button("✏️ Edit Details", key=f"edit_btn_{pt['id']}", use_container_width=True):
                    edit_patient_dialog(pt, index)

            with col2:
                # Text box updates instantly using the version key
                final_msg = st.text_area("Message Preview:", value=draft, height=280, key=f"msg_{pt['id']}_{pt['version']}", label_visibility="collapsed")
            with col3:
                encoded_message = urllib.parse.quote(final_msg)
                whatsapp_url = f"https://wa.me/{pt['Phone']}?text={encoded_message}"
                st.markdown(f"""<a href="{whatsapp_url}" target="_blank" style="text-decoration: none;"><button style="background-color:#25D366; color:white; padding:10px; border:none; border-radius:5px; cursor:pointer; width:100%; font-weight:bold; margin-bottom:10px;">💬 Send WhatsApp</button></a>""", unsafe_allow_html=True)
                st.button("❌ Remove", key=f"del_{pt['id']}", on_click=delete_patient, args=(index,), use_container_width=True)
            st.divider()

    if st.button("🗑️ Clear List (End of Day)"):
        st.session_state.patient_list = []
        save_to_cloud([]) 
        st.rerun()
