import streamlit as st
import urllib.parse
from datetime import datetime, timedelta

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Pre-Op Dispatcher", page_icon="👁️", layout="wide")

# --- DR. AZYGOS WATERMARK ---
st.markdown(
    """
    <style>
    .watermark {
        position: fixed;
        bottom: 20px;
        left: 20px;
        font-size: 16px;
        color: #888888;
        z-index: 999999;
        pointer-events: none;
        font-style: italic;
        font-weight: bold;
    }
    </style>
    <div class="watermark">Designed by dr.azygos</div>
    """,
    unsafe_allow_html=True
)

# --- 🔒 SECURITY GATE ---
HOSPITAL_PASSWORD = "2026" 

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

# --- INITIALIZE MEMORY ---
if 'patient_list' not in st.session_state:
    st.session_state.patient_list = []

def delete_patient(index):
    st.session_state.patient_list.pop(index)

# --- SIDEBAR: DATA ENTRY ---
with st.sidebar:
    st.header("➕ Add New Patient")
    
    with st.form("patient_form", clear_on_submit=True):
        patient_name = st.text_input("Patient Name*")
        phone_number = st.text_input("WhatsApp Number*", value="91", help="Country code + number (e.g., 919876543210)") 
        
        branch = st.selectbox("Hospital Branch", ["New Colony", "Mihan"])
        
        # --- NEW: DATE PICKER ---
        # Defaults to tomorrow, but lets you select any date
        tomorrow = datetime.now() + timedelta(days=1)
        surgery_date = st.date_input("Date of Surgery", value=tomorrow)
        
        # Foolproof Time Selector
        start_time = datetime.strptime("07:45 AM", "%I:%M %p")
        time_options = [(start_time + timedelta(minutes=15*i)).strftime("%I:%M %p") for i in range(42)]
        reporting_time = st.selectbox("Reporting Time", time_options)
        
        st.markdown("### Clinical Details")
        anesthesia = st.radio("Anesthesia / Diet", ["Local Anesthesia (LA)", "Fasting (NPM)"])
        comorbidities = st.selectbox("Comorbidities", [
            "None (No HTN, No DM)", 
            "Only HTN", 
            "Only DM", 
            "Both HTN & DM"
        ])
        
        submitted = st.form_submit_button("Add to Queue", type="primary", use_container_width=True)

        if submitted:
            if not patient_name or phone_number.strip() == "" or phone_number == "91":
                st.error("⚠️ Please provide a valid name and number.")
            else:
                st.session_state.patient_list.append({
                    "Name": patient_name,
                    "Phone": phone_number.replace("+", ""), 
                    "Branch": branch,
                    "Date": surgery_date.strftime("%d.%m.%Y"), # Formats the date to match your template
                    "Time": reporting_time,
                    "Anesthesia": anesthesia,
                    "Comorbidities": comorbidities
                })
                st.success(f"Added {patient_name}!")

# --- MAIN DASHBOARD: THE QUEUE ---
st.title("📋 Surgery Dispatch Queue")

if len(st.session_state.patient_list) == 0:
    st.info("👈 Your queue is empty. Start adding patients from the sidebar menu.")
else:
    st.markdown(f"**Total Patients in Queue:** {len(st.session_state.patient_list)}")
    st.divider()

    # --- INDIVIDUAL PATIENT CARDS ---
    for index, pt in enumerate(st.session_state.patient_list):
        
        # Calculate 2 hours prior to reporting time for medications/breakfast
        rep_time_obj = datetime.strptime(pt['Time'], "%I:%M %p")
        two_hours_prior = (rep_time_obj - timedelta(hours=2)).strftime("%I:%M %p")
        
        # Pull the specific date saved for this patient
        dos = pt['Date']
        
        # --- THE SURAJ EYE INSTITUTE LOGIC MATRIX ---
        # 1. Standard Greeting with Date
        draft = f"Dear {pt['Name']},\nGreetings from Suraj Eye Institute, Nagpur.\nYour surgery has been scheduled on {dos}.\n\n"
        
        # 2. Clinical Instructions
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

        # 3. Standard Footer
        draft += f"\n\nReport to hospital at Suraj Eye Institute {pt['Branch']} branch at {pt['Time']}.\n\nThank you.\nTeam Suraj Eye Institute."
        
        # Optional: Add QR Link at the very bottom
        draft += "\n\n(View location & payment QR: [Insert Link Here])"

        # --- UI CARD ---
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.subheader(f"👤 {pt['Name']}")
                # Now displays both the date and time clearly
                st.write(f"**{pt['Branch']}** | {dos} @ {pt['Time']}")
                st.caption(f"{pt['Anesthesia']} | {pt['Comorbidities']}")
            
            with col2:
                final_msg = st.text_area("Message Preview:", value=draft, height=240, key=f"msg_{index}", label_visibility="collapsed")
            
            with col3:
                encoded_message = urllib.parse.quote(final_msg)
                whatsapp_url = f"https://wa.me/{pt['Phone']}?text={encoded_message}"
                
                st.markdown(f"""
                    <a href="{whatsapp_url}" target="_blank" style="text-decoration: none;">
                        <button style="background-color:#25D366; color:white; padding:10px; border:none; border-radius:5px; cursor:pointer; width:100%; font-weight:bold; margin-bottom:10px;">
                            💬 Send WhatsApp
                        </button>
                    </a>
                    """, unsafe_allow_html=True)
                
                st.button("❌ Remove", key=f"del_{index}", on_click=delete_patient, args=(index,), use_container_width=True)
            
            st.divider()

    if st.button("🗑️ Clear Entire List (End of Day)"):
        st.session_state.patient_list = []
        st.rerun()
