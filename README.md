📘 Augustina Medical Assistant

An AI-powered clinical chatbot designed to support healthcare professionals in real-time decision support, patient documentation, and interactive consultation.

This system integrates LangChain, OpenAI GPT models, and SQLite to create a conversational assistant that provides safe, guided, and medically relevant interactions between healthcare providers and patients.

🚀 Features

Healthcare professional login: Doctors, nurses, midwives, allied health professionals, and support staff can use the system.

Patient registration & retrieval: Enter patient details (name, age, sex, medical history). Existing patients are detected, with the option to continue previous consultations or start new ones.

Conversational AI Assistant: GPT-powered responses limited to medical and healthcare-related queries.

Clinical Tools (extensible):

🧠 Symptom Checker: Suggests possible conditions.

📝 SOAP Note Generator: Creates structured medical notes.

💊 Drug Interaction Checker: Checks for risky drug combinations.

🧮 BMI Calculator: Calculates and interprets BMI.

Guardrails:

Rejects irrelevant questions (e.g., “What is Northumbria University?”).

Restricts scope to healthcare.

Database Logging:

Stores user roles, patient data, and chat history in SQLite.

Option to view past consultations or start fresh.

Conversational Tone:

Responses simulate a human-like healthcare professional.

Encourages follow-ups: “Do you also experience dizziness along with your headache?”

🛠️ Tech Stack

Frontend/UI: Streamlit

Backend/AI: LangChain
, OpenAI API

Database: SQLite (persistent storage for users, patients, and chat logs)

Models Supported: gpt-3.5-turbo and gpt-4o (switchable)

📂 Project Structure
augustina-medical-assistant/
│── augustina_chatbot_upgrade.py   # Main Streamlit app
│── requirements.txt               # Dependencies
│── README.md                      # Project documentation
│── data/
│    └── chatbot.db                # SQLite database (auto-created)

⚙️ Installation

Clone the repository:

git clone https://github.com/your-repo/augustina-medical-assistant.git
cd augustina-medical-assistant


Install dependencies:

pip install -r requirements.txt


Set up OpenAI API key:

export OPENAI_API_KEY="your_api_key_here"   # Mac/Linux
setx OPENAI_API_KEY "your_api_key_here"     # Windows (cmd)


Run the chatbot:

streamlit run augustina_chatbot_upgrade.py

💡 Usage Flow

Greeted with: “This is Augustina Medical Assistant. How can I help you today?”

Select Healthcare Role → Enter your name.

Enter Patient Data → Name, Age, Sex, Medical History.

If patient exists → Continue consultation or register as new.

Chatbot Page:

Ask medical questions.

Get symptom analysis, lab test suggestions, and SOAP notes.

Conversations logged in SQLite.

🔒 Guardrails

Rejects irrelevant queries:

“Northumbria University is an irrelevant question. I can’t answer that.”

Detects only health-related inputs.

Filters outputs to avoid unsafe, speculative, or non-medical advice.

🏥 Example Interaction

User (Doctor):
“I am feeling headache, nausea, and sweating. What possibly can it be?”

Assistant (Augustina):
“Possible causes of your symptoms could be migraine, tension headache, or high blood pressure.
To be more precise, may I ask: Do you also experience dizziness or blurred vision?

I would recommend checking your blood pressure and considering basic lab tests such as CBC and BMP.”

📊 Academic Value (For Dissertation)

This project supports your dissertation:
“Design and Development of an AI-Powered Clinical Chatbot for Real-Time Decision Support and Documentation in Healthcare” by:
✔ Implementing decision support (symptom checker, test recommendations, drug interaction checker).
✔ Providing documentation support (SOAP notes, patient logs).
✔ Enhancing realism with conversational, doctor-like interactions.
✔ Ensuring safe AI deployment through medical guardrails.

✅ Future Improvements

Multi-patient simultaneous support.

Integration with FHIR/EHR systems.

More advanced tools: risk scoring, lab test interpretation.

Speech-to-text voice input for doctors/patients.
 