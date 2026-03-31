import streamlit as st
import urllib.parse

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Pre-Op Dispatcher", page_icon="👁️", layout="wide")

# --- 🔒 SECURITY GATE ---
# Change this to whatever password you want your staff to use
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
            
    st.stop() # Stops the rest of the app from loading until unlocked


# --- DR. AZYGOS WATERMARK ---
st.markdown(
    """
    <style>
    .watermark {
        position: fixed;
        bottom: 20px;
        left: 20px; /* Moved to the left side */
        font-size: 16px; /* Made slightly larger */
        color: #888888; /* Solid grey */
        z-index: 999999; /* Forced to the very front */
        pointer-events: none;
        font-style: italic;
        font-weight: bold;
    }
    </style>
    <div class="watermark">Designed by dr.azygos</div>
    """,
    unsafe_allow_html=True
)

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
        # Standard WhatsApp links work best with just the country code and number, no '+'
        phone_number = st.text_input("WhatsApp Number*", value="91", help="Country code + number (e.g., 919876543210)") 
        
        branch = st.selectbox("Hospital Branch", ["New Colony", "Mihan"])
        reporting_time = st.time_input("Reporting Time")
        
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
                    "Phone": phone_number.replace("+", ""), # Strips the + if accidentally typed
                    "Branch": branch,
                    "Time": reporting_time.strftime("%I:%M %p"),
                    "Anesthesia": anesthesia,
                    "Comorbidities": comorbidities
                })
                st.success(f"Added {patient_name}!")

# --- MAIN DASHBOARD: THE QUEUE ---
st.title("📋 Tomorrow's Surgery Dispatch Queue")

# Add your hospital's payment/location link here instead of the image file
STANDARD_FOOTER = """

---
🏥 *Hospital Administration*
View our location and payment QR code here: [Insert Link Here]
For any emergencies, call 0495-XXXXXXX."""

if len(st.session_state.patient_list) == 0:
    st.info("👈 Your queue is empty. Start adding patients from the sidebar menu.")
else:
    st.markdown(f"**Total Patients in Queue:** {len(st.session_state.patient_list)}")
    st.divider()

    # --- INDIVIDUAL PATIENT CARDS ---
    for index, pt in enumerate(st.session_state.patient_list):
        
        # --- LOGIC MATRIX ---
        draft = f"Dear {pt['Name']},\n\nThis is a reminder regarding your eye surgery tomorrow at our {pt['Branch']} branch.\nPlease report to the hospital at exactly {pt['Time']}.\n\n"
        
        if pt['Anesthesia'] == "Local Anesthesia (LA)":
            if pt['Comorbidities'] == "Both HTN & DM":
                draft += "Instruction: Have a light breakfast with sugarless tea and 2 biscuits. Take your DM and HTN medication 2 hours prior to reporting."
            else:
                draft += f"[Insert LA + {pt['Comorbidities']} instructions here]"
        elif pt['Anesthesia'] == "Fasting (NPM)":
            draft += f"[Insert NPM + {pt['Comorbidities']} logic here]"
        
        draft += STANDARD_FOOTER

        # --- UI CARD ---
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.subheader(f"👤 {pt['Name']}")
                st.write(f"**{pt['Branch']}** @ {pt['Time']}")
                st.caption(f"{pt['Anesthesia']} | {pt['Comorbidities']}")
            
            with col2:
                final_msg = st.text_area("Message Preview:", value=draft, height=150, key=f"msg_{index}", label_visibility="collapsed")
            
            with col3:
                # --- SAFE CLICK-TO-CHAT BUTTON ---
                encoded_message = urllib.parse.quote(final_msg)
                whatsapp_url = f"https://wa.me/{pt['Phone']}?text={encoded_message}"
                
                # Creates a hyperlink disguised as a button
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
