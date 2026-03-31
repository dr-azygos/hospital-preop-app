import streamlit as st
import pywhatkit as kit
import time

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Pre-Op Dispatcher", page_icon="👁️", layout="wide")

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
        phone_number = st.text_input("WhatsApp Number*", value="+91", help="Must include + and country code")

        # --- NEW: BRANCH SELECTION ---
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
            if not patient_name or phone_number.strip() == "" or phone_number == "+91":
                st.error("⚠️ Please provide a valid name and number.")
            else:
                st.session_state.patient_list.append({
                    "Name": patient_name,
                    "Phone": phone_number,
                    "Branch": branch,  # Saves the selected branch
                    "Time": reporting_time.strftime("%I:%M %p"),
                    "Anesthesia": anesthesia,
                    "Comorbidities": comorbidities
                })
                st.success(f"Added {patient_name} for {branch} branch!")

# --- MAIN DASHBOARD: THE QUEUE ---
st.title("📋 Tomorrow's Surgery Dispatch Queue")

# Define your standard footer message here
STANDARD_FOOTER = """

---
🏥 *Hospital Administration*
Please scan the QR code above for location details / payment.
For any emergencies, call 0495-XXXXXXX."""

if len(st.session_state.patient_list) == 0:
    st.info("👈 Your queue is empty. Start adding patients from the sidebar menu.")
else:
    st.markdown(f"**Total Patients in Queue:** {len(st.session_state.patient_list)}")
    st.divider()

    for index, pt in enumerate(st.session_state.patient_list):

        # --- UPDATED LOGIC MATRIX (Now includes Branch) ---
        draft = f"Dear {pt['Name']},\n\nThis is a reminder regarding your eye surgery tomorrow at our {pt['Branch']} branch.\nPlease report to the hospital at exactly {pt['Time']}.\n\n"

        if pt['Anesthesia'] == "Local Anesthesia (LA)":
            if pt['Comorbidities'] == "Both HTN & DM":
                draft += "Instruction: Have a light breakfast with sugarless tea and 2 biscuits. Take your DM and HTN medication 2 hours prior to reporting."
            else:
                draft += f"[Insert LA + {pt['Comorbidities']} instructions here]"
        elif pt['Anesthesia'] == "Fasting (NPM)":
            draft += f"[Insert NPM + {pt['Comorbidities']} logic here]"

        # Add the standard message to the very end
        draft += STANDARD_FOOTER

        # --- UI CARD ---
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])

            with col1:
                st.subheader(f"👤 {pt['Name']}")
                st.write(f"**{pt['Branch']}** @ {pt['Time']}")
                st.caption(f"{pt['Anesthesia']} | {pt['Comorbidities']}")

            with col2:
                final_msg = st.text_area("Message Preview:", value=draft, height=150, key=f"msg_{index}",
                                         label_visibility="collapsed")

            with col3:
                if st.button("🚀 Auto-Send with QR", key=f"send_{index}", use_container_width=True, type="primary"):
                    with st.spinner("Opening WhatsApp... Do not touch mouse/keyboard!"):
                        try:
                            safe_phone = pt['Phone'] if pt['Phone'].startswith("+") else f"+{pt['Phone']}"

                            # THE IMAGE AUTOMATION COMMAND
                            kit.sendwhats_image(
                                receiver=safe_phone,
                                img_path="qrcode.png",  # Ensure this image is in your project folder
                                caption=final_msg,
                                wait_time=15,
                                tab_close=True,
                                close_time=3
                            )
                            st.success("Message Sent Successfully!")
                            time.sleep(2)

                        except Exception as e:
                            st.error(f"Error sending message: {e}")

                st.button("❌ Remove", key=f"del_{index}", on_click=delete_patient, args=(index,),
                          use_container_width=True)

            st.divider()

    if st.button("🗑️ Clear Entire List (End of Day)"):
        st.session_state.patient_list = []
        st.rerun()