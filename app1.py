import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set")

client = OpenAI(api_key=api_key)

MODEL_NAME = "gpt-4o-mini"

# ================== CONFIG ==================
st.set_page_config(
    page_title="AI Interview Preparation",
    layout="centered"
)

# ================== PROMPTS ==================

JD_ANALYSIS_PROMPT = """
You are a senior technical recruiter and interviewer.

Analyze the following job description and extract:

1. Seniority level (Junior / Mid / Senior)
2. Key technical skills
3. Soft skills
4. Interview focus areas
5. Suggested interview strategy

Output format (strict):
- Seniority:
- Key Skills:
- Soft Skills:
- Interview Focus:
- Interview Strategy:
"""

def build_interview_system_prompt(strategy: str) -> str:
    return f"""
You are a senior technical interviewer.

Use the following interview strategy:
{strategy}

Rules:
- Ask one interview question at a time
- Wait for the candidate's answer
- Give concise feedback
- Rate the answer from 0 to 5
- Adjust difficulty dynamically
- After feedback, ask the next question
"""

# ================== FUNCTIONS ==================

def analyze_job_description(jd_text: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": JD_ANALYSIS_PROMPT},
            {"role": "user", "content": jd_text}
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


def call_interviewer(messages: list) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.7,
    )

    return response.choices[0].message.content


# ================== SESSION STATE ==================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

# ================== UI ==================

st.title("AI Interview Preparation App")

st.markdown(
    "Practice realistic interviews powered by **Job Description analysis + AI interviewer**."
)

# ---------- Job Description ----------
st.subheader("1️⃣ Job Description")

job_desc = st.text_area(
    "Paste the job description (optional but recommended)",
    height=180,
    placeholder="Paste the job description here..."
)

analyze_btn = st.button("🔍 Analyze Job Description")

# ---------- JD Analysis ----------
if analyze_btn and job_desc.strip():
    with st.spinner("Analyzing job description..."):
        strategy = analyze_job_description(job_desc)
        st.session_state.interview_strategy = strategy



if "interview_strategy" in st.session_state:
    st.subheader("📌 Interview Strategy")
    st.markdown(st.session_state.interview_strategy)

# ---------- Start Interview ----------
st.subheader("2️⃣ Start Interview")

start_btn = st.button("🚀 Start Interview")

if start_btn and not st.session_state.interview_started:
    system_prompt = build_interview_system_prompt(
        st.session_state.get(
            "interview_strategy",
            "General software engineering interview"
        )
    )

    st.info(system_prompt)

    st.session_state.messages = [
        {"role": "system", "content": system_prompt}
    ]

    st.session_state.interview_started = True

    # Ask first question
    first_question = call_interviewer(st.session_state.messages)
    st.session_state.messages.append(
        {"role": "assistant", "content": first_question}
    )

# ---------- Chat History ----------
if st.session_state.interview_started:
    st.subheader("💬 Interview Session")

    for msg in st.session_state.messages[1:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

# ---------- User Input ----------
if st.session_state.interview_started:
    user_input = st.chat_input("Type your answer here...")

    if user_input:
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )

        with st.chat_message("user"):
            st.write(user_input)

        with st.spinner("Interviewer is thinking..."):
            reply = call_interviewer(st.session_state.messages)

        st.session_state.messages.append(
            {"role": "assistant", "content": reply}
        )

        with st.chat_message("assistant"):
            st.write(reply)
