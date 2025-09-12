import os
from dotenv import load_dotenv
import re
import sqlite3
from datetime import datetime
from typing import List, Tuple
from pathlib import Path

import streamlit as st
from langchain.agents import Tool, initialize_agent
from langchain.agents.agent_types import AgentType
from langchain_openai import ChatOpenAI
# Load environment variables from .env file
load_dotenv()

# Access the keys
# api_key = os.getenv("API_KEY")

# CONFIG 
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")  # <-- put your OpenAI key here
DB_FILE = "augustina.db"

# Branding / avatars
ASSISTANT_NAME = "Augustina Medical Assistant"
ICON_PATH = Path("images/augustina_icon.png")
ASSISTANT_AVATAR = str(ICON_PATH) if ICON_PATH.exists() else "👩🏽‍⚕️"
USER_AVATAR = "👤"

# UI SETUP (global) 
st.set_page_config(page_title="Augustina Medical Assistant", layout="centered")
st.title("👩🏽‍⚕️ Augustina Medical Assistant")

# DB SETUP 
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS professionals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, category TEXT, role TEXT, created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT, age INTEGER, sex TEXT, history TEXT, created_at TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER, professional_id INTEGER,
    sender TEXT, message TEXT, timestamp TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS soap_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER, professional_id INTEGER,
    note TEXT, timestamp TEXT
)
""")
conn.commit()

#  LLM Large Language Model
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.5)

# TOOLS 
def symptom_checker(text: str) -> str:
    t = text.lower()
    if "fever" in t:
        return "Likely causes: Infection, flu, or COVID-19."
    if "headache" in t:
        return "Possible causes: Migraine, tension, high blood pressure."
    return "Please provide more symptoms for accurate suggestions."

def generate_clinical_note(text: str) -> str:
    note = (
        f"📝 **SOAP Note**\n"
        f"- **Subjective:** {text}\n"
        f"- **Objective:** Pending\n"
        f"- **Assessment:** Based on symptom analysis\n"
        f"- **Plan:** Follow-up or further testing."
    )
    st.session_state.setdefault("soap_buffer", []).append(note)
    return note

def drug_interaction_checker(text: str) -> str:
    drugs = [d.strip().lower() for d in text.split(",")]
    if "aspirin" in drugs and "warfarin" in drugs:
        return "⚠️ Aspirin + Warfarin = increased bleeding risk."
    return "✅ No major interactions found."

def differential_diagnosis(text: str) -> str:
    if "chest pain" in text.lower():
        return "Differentials: MI, angina, GERD, anxiety."
    return "Need more details for differential diagnosis."

def lab_test_recommendation(text: str) -> str:
    if "fatigue" in text.lower():
        return "Recommended tests: CBC, Iron studies, TSH."
    return "Consider basic labs: CBC, BMP."

tools = [
    Tool("Symptom Checker", symptom_checker, "Check likely causes of symptoms."),
    Tool("Clinical Note Generator", generate_clinical_note, "Generate a SOAP note."),
    Tool("Drug Interaction Checker", drug_interaction_checker, "Check for drug interactions."),
    Tool("Differential Diagnosis", differential_diagnosis, "Suggest possible conditions."),
    Tool("Lab Test Recommendation", lab_test_recommendation, "Suggest lab tests.")
]

# AGENT WITH STRICT MEDICAL SCOPE
SYSTEM_PROMPT = (
    "You are Augustina, an AI-powered clinical assistant for healthcare professionals and patients. "
    "You must ONLY answer questions related to healthcare, medicine, patient care, diagnostics, "
    "treatment, drugs, symptoms, anatomy, and clinical workflows. "
    "If the question is outside this scope (e.g., politics, sports, universities, technology unrelated to healthcare), "
    "respond ONLY with:\n"
    "1) '[Topic] is an irrelevant question I can’t answer to that.'\n"
    "2) 'Please ask a medical or healthcare-related question.'\n"
    "3) 'For accuracy, include patient details if available.'\n"
    "TOOLS YOU MAY USE: 'Symptom Checker', 'Clinical Note Generator', "
    "'Drug Interaction Checker', 'Differential Diagnosis', 'Lab Test Recommendation'.\n"
    "Rules for ACCURACY & SAFETY:\n"
    "1) Be cautious and evidence-minded; never guess. If uncertain, say so.\n"
    "2) Prefer structured output (bullet points) and next steps; do not give definitive diagnoses.\n"
    "3) Never fabricate tool names or facts. Use only provided tools.\n"
    "4) Include a brief safety reminder when appropriate (e.g., seek urgent care if red flags)."
)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=False,
    handle_parsing_errors=True,
    agent_kwargs={"system_message": SYSTEM_PROMPT}
)

# HELPERS 
def log_msg(pid: int, profid: int, sender: str, msg: str):
    cursor.execute(
        "INSERT INTO chat_logs VALUES (NULL, ?, ?, ?, ?, ?)",
        (pid, profid, sender, msg, datetime.now().isoformat())
    )
    conn.commit()

def fetch_history(pid: int) -> List[Tuple[str, str]]:
    cursor.execute("SELECT sender, message FROM chat_logs WHERE patient_id=?", (pid,))
    return cursor.fetchall()

def fetch_soap(pid: int) -> List[str]:
    cursor.execute("SELECT note FROM soap_notes WHERE patient_id=?", (pid,))
    return [n[0] for n in cursor.fetchall()]

def save_soap(pid: int, profid: int):
    for note in st.session_state.get("soap_buffer", []):
        cursor.execute(
            "INSERT INTO soap_notes VALUES (NULL, ?, ?, ?, ?)",
            (pid, profid, note, datetime.now().isoformat())
        )
    conn.commit()
    st.session_state["soap_buffer"] = []

def find_patient(name: str, age: int, sex: str):
    cursor.execute(
        "SELECT id, name, age, sex, history FROM patients WHERE name=? AND age=? AND sex=?",
        (name.strip(), int(age), sex.strip())
    )
    return cursor.fetchone()

# Scope validator (medical only) 
MEDICAL_HINTS = [
    "symptom","symptoms","pain","fever","headache","nausea","vomit","rash","bleeding",
    "cough","sore throat","diarrhea","shortness of breath","chest pain","heart rate",
    "blood pressure","bp","pulse","temperature","drug","medication","tablet","capsule",
    "dose","prescription","side effect","interaction","allergy","diabetes","hypertension",
    "infection","virus","bacteria","antibiotic","lab","cbc","mri","ct scan","x-ray",
    "ultrasound","treatment","therapy","surgery","operation","diagnosis","triage",
    "soap note","vitals","anatomy","organ","disease","condition","wound","fracture",
    "injury","medical history","patient","doctor","nurse","hospital","clinic"
]
NON_MEDICAL_CLUES = [
    "university","school","college","football","soccer","basketball","movie","celebrity",
    "actor","singer","music","bitcoin","cryptocurrency","stock market","recipe","travel",
    "holiday","politics","election","car review","technology"
]

def is_medical_query(text: str) -> bool:
    t = text.lower()
    if any(k in t for k in NON_MEDICAL_CLUES):
        return False
    return any(k in t for k in MEDICAL_HINTS)

def validate_question(text: str) -> (bool, str):
    if not text or not text.strip():
        return False, "Please enter a medical or healthcare-related question."
    if len(text.strip()) < 3:
        return False, "Your question is too short. Please add more detail."
    if not is_medical_query(text):
        return False, (
            f"{text} is an irrelevant question I can’t answer to that.\n"
            "Please ask a medical or healthcare-related question.\n"
            "For accuracy, include patient details if available."
        )
    return True, ""

# STAGES 
if "stage" not in st.session_state:
    st.session_state.stage = "pro_greeting"

# Stage 1: Healthcare professional selection
if st.session_state.stage == "pro_greeting":
    st.write("Hello! This is **Augustina Medical Chatbot**. How can I help you today?")

    category = st.selectbox(
        "Category",
        ["Medical Professionals", "Allied Health Professionals", "Other Healthcare Professionals", "Support Staff"]
    )
    role_map = {
        "Medical Professionals": ["Doctor", "Nurse", "Midwife", "Dentist"],
        "Allied Health Professionals": ["Physiotherapy", "Occupational Therapy"],
        "Other Healthcare Professionals": ["Clinical Scientist", "Hearing Aid Dispenser"],
        "Support Staff": ["Technician", "Administrative Staff", "Medical Secretaries", "Receptionist"],
    }
    role = st.selectbox("Role", role_map[category])
    name = st.text_input("Your Name")

    if st.button("Continue") and name.strip():
        cursor.execute(
            "INSERT INTO professionals VALUES (NULL, ?, ?, ?, ?)",
            (name.strip(), category, role, datetime.now().isoformat())
        )
        conn.commit()
        st.session_state.professional_id = cursor.lastrowid
        st.session_state.professional_name = name.strip()
        st.session_state.stage = "patient_form"
        st.rerun()

# Stage 2: Patient intake with confirmation flow 
elif st.session_state.stage == "patient_form":
    st.subheader("Patient Details")

    # New-patient confirmation substage
    if st.session_state.get("show_new_patient_confirm"):
        cand = st.session_state["new_patient_candidate"]
        st.info("No existing patient found. Please confirm the new patient details before continuing.")
        st.write(f"**Name:** {cand['name']}")
        st.write(f"**Age:** {cand['age']}")
        st.write(f"**Sex:** {cand['sex']}")
        st.write(f"**History:** {cand['history'] or '—'}")

        colA, colB = st.columns(2)
        with colA:
            if st.button("✅ Confirm & Continue"):
                cursor.execute(
                    "INSERT INTO patients VALUES (NULL, ?, ?, ?, ?, ?)",
                    (cand["name"].strip(), int(cand["age"]), cand["sex"], cand["history"].strip(), datetime.now().isoformat())
                )
                conn.commit()
                st.session_state.patient_id = cursor.lastrowid
                st.session_state.chat_mode = "new"
                st.session_state.show_new_patient_confirm = False
                st.session_state.new_patient_candidate = {}
                st.session_state.stage = "chat"
                st.rerun()
        with colB:
            if st.button("✏️ Edit Details"):
                st.session_state.show_new_patient_confirm = False
                st.session_state.new_patient_candidate = {}
                st.rerun()

        if st.button("← Back"):
            st.session_state.stage = "pro_greeting"
            st.rerun()

        st.stop()

    # Default editable form
    pname = st.text_input("Patient Name", value=st.session_state.get("tmp_pname", ""))
    page = st.number_input("Age", 0, 120, value=int(st.session_state.get("tmp_page", 0)))
    psex = st.selectbox(
        "Sex",
        ["Male", "Female", "Other"],
        index=["Male", "Female", "Other"].index(st.session_state.get("tmp_psex", "Male"))
    )
    phist = st.text_area("History", value=st.session_state.get("tmp_phist", ""))

    if st.button("Check / Continue"):
        # Keep form values (used if we show confirm/review)
        st.session_state.tmp_pname = pname
        st.session_state.tmp_page = page
        st.session_state.tmp_psex = psex
        st.session_state.tmp_phist = phist

        match = find_patient(pname, page, psex)

        if match:
            pid, nm, ag, sx, hist = match
            # hand off to a dedicated review stage so buttons work reliably
            st.session_state.stage = "patient_review"
            st.session_state.review_patient = {
                "id": pid, "name": nm, "age": ag, "sex": sx, "history": (hist or "—")
            }
            st.rerun()

        else:
            # Show confirmation before creating a brand-new patient
            st.session_state.new_patient_candidate = {
                "name": pname, "age": page, "sex": psex, "history": phist
            }
            st.session_state.show_new_patient_confirm = True
            st.rerun()

    if st.button("← Back"):
        st.session_state.stage = "pro_greeting"
        st.rerun()

# Stage 2b: Existing patient review (separate stage so buttons fire) 
elif st.session_state.stage == "patient_review":
    prof_name = st.session_state.get("professional_name", "User")
    data = st.session_state.get("review_patient", {})
    pid = data.get("id")

    st.subheader("Existing patient found")
    st.write(f"**Name:** {data.get('name')}")
    st.write(f"**Age:** {data.get('age')}")
    st.write(f"**Sex:** {data.get('sex')}")
    st.write(f"**History:** {data.get('history')}")

    st.markdown("**Previous SOAP Notes:**")
    notes = fetch_soap(pid)
    if notes:
        for n in notes:
            st.markdown(n)
    else:
        st.write("— None recorded —")

    st.markdown("**Previous Chat History:**")
    chats = fetch_history(pid)
    if chats:
        for sender, msg in chats:
            if sender == "user":
                with st.chat_message(prof_name, avatar=USER_AVATAR):
                    st.markdown(msg)
            else:
                with st.chat_message(ASSISTANT_NAME, avatar=ASSISTANT_AVATAR):
                    st.markdown(msg)
    else:
        st.write("— No chat history —")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➡️ Continue with this patient"):
            st.session_state.patient_id = pid
            st.session_state.chat_mode = "existing"
            st.session_state.stage = "chat"
            st.session_state.pop("review_patient", None)
            st.rerun()

    with col2:
        if st.button("🆕 Register as new patient"):
            pname = st.session_state.get("tmp_pname", data.get("name", ""))
            page = int(st.session_state.get("tmp_page", data.get("age", 0)))
            psex  = st.session_state.get("tmp_psex", data.get("sex", "Other"))
            phist = st.session_state.get("tmp_phist", data.get("history", ""))

            cursor.execute(
                "INSERT INTO patients VALUES (NULL, ?, ?, ?, ?, ?)",
                (pname.strip(), page, psex, phist.strip(), datetime.now().isoformat())
            )
            conn.commit()
            st.session_state.patient_id = cursor.lastrowid
            st.session_state.chat_mode = "new"
            st.session_state.stage = "chat"
            st.session_state.pop("review_patient", None)
            st.rerun()

    if st.button("← Back"):
        st.session_state.stage = "patient_form"
        st.rerun()

# Stage 3: Chatbot 
elif st.session_state.stage == "chat":
    professional_name = st.session_state.get("professional_name", "User")

    # Patient name for header + welcome
    cursor.execute("SELECT name FROM patients WHERE id=?", (st.session_state.patient_id,))
    patient_name = cursor.fetchone()[0]

    # Welcome banner
    if st.session_state.get("chat_mode") == "existing":
        st.success(f"📂 Continuing consultation for **{patient_name}**.")
    else:
        st.info(f"🆕 Starting new consultation for **{patient_name}**.")

    # History hidden by default; available on demand
    with st.expander("Show previous conversation (optional)", expanded=False):
        prev = fetch_history(st.session_state.patient_id)
        if not prev:
            st.caption("No previous messages saved.")
        else:
            for sender, msg in prev:
                if sender == "user":
                    with st.chat_message(professional_name, avatar=USER_AVATAR):
                        st.markdown(msg)
                else:
                    with st.chat_message(ASSISTANT_NAME, avatar=ASSISTANT_AVATAR):
                        st.markdown(msg)

    # Fresh chat starts here
    user_input = st.chat_input("Your message...")
    if user_input:
        # Show & log user message
        with st.chat_message(professional_name, avatar=USER_AVATAR):
            st.markdown(user_input)
        log_msg(st.session_state.patient_id, st.session_state.professional_id, "user", user_input)

        # MEDICAL-ONLY VALIDATION
        is_ok, reason = validate_question(user_input)
        if not is_ok:
            reply = reason  # fixed out-of-scope message
        else:
            try:
                reply = agent.run(user_input)
            except Exception as e:
                reply = f"⚠️ Could not process: {e}"

        # Show & log assistant reply
        with st.chat_message(ASSISTANT_NAME, avatar=ASSISTANT_AVATAR):
            st.markdown(reply)
        log_msg(st.session_state.patient_id, st.session_state.professional_id, "assistant", reply)

        # Persist any generated SOAP notes
        save_soap(st.session_state.patient_id, st.session_state.professional_id)
