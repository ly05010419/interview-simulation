import streamlit as st
from openai import OpenAI
import os
import re
from dotenv import load_dotenv

# ================== SETUP ==================

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set")

client = OpenAI(api_key=api_key)

MODEL_NAME = "gpt-4o-mini"
MAX_INPUT_LENGTH = 800

PRICE_INPUT_PER_M = 0.05
PRICE_OUTPUT_PER_M = 0.40

# ================== PROMPTS ==================

JD_ANALYSIS_PROMPT = """
You are a senior technical recruiter.

First, determine whether the input is a REAL job description.
If it is NOT a job description, respond ONLY with:
INVALID_JOB_DESCRIPTION

If it IS valid, analyze and output:

- Seniority
- Key Skills
- Soft Skills
- Interview Focus
- Interview Strategy
- Interviewer Guidelines
- Evaluation Criteria
"""

INPUT_GUARD_PROMPT = """
You are a security guard for an AI interview application.

If the input is a valid interview answer respond:
VALID

Otherwise:
INVALID
"""

def build_interview_system_prompt(strategy, difficulty, persona):
    persona_map = {
        "Friendly": "Be encouraging and supportive.",
        "Neutral": "Be professional and neutral.",
        "Strict": "Be strict and challenging."
    }

    difficulty_map = {
        "Easy": "Ask basic conceptual questions.",
        "Medium": "Ask practical and applied questions.",
        "Hard": "Ask deep and advanced questions."
    }

    return f"""
You are a senior technical interviewer.

Interview Strategy:
{strategy}

Persona:
{persona_map[persona]}

Difficulty:
{difficulty_map[difficulty]}

Rules:
- Ask one question at a time
- Wait for the answer
- Give feedback
- Always include: Score: X/5
"""

# ================== HELPERS ==================

def update_cost(usage):
    st.session_state.token_usage["prompt"] += usage.prompt_tokens
    st.session_state.token_usage["completion"] += usage.completion_tokens
    st.session_state.token_usage["cost"] += (
        usage.prompt_tokens / 1e6 * PRICE_INPUT_PER_M +
        usage.completion_tokens / 1e6 * PRICE_OUTPUT_PER_M
    )

def extract_score(text):
    m = re.search(r"Score:\s*([0-5])\s*/\s*5", text)
    return int(m.group(1)) if m else None

# ================== SESSION STATE ==================

defaults = {
    "job_analyzed": False,
    "interview_started": False,
    "messages": [],
    "scores": [],
    "difficulty": "Medium",
    "persona": "Neutral",
    "token_usage": {"prompt": 0, "completion": 0, "cost": 0.0},
    "interview_strategy": ""
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ================== SIDEBAR ==================

with st.sidebar:
    st.header("📌 Interview Panel")

    # ---- Strategy ----
    if st.session_state.job_analyzed:
        with st.expander("Interview Strategy", expanded=True):
            st.markdown(st.session_state.interview_strategy)
    else:
        st.info("Analyze a job description to see strategy.")

    st.divider()

    # ---- Performance (Horizontal) ----
    st.subheader("📊 Performance")
    p1, p2 = st.columns(2)

    if st.session_state.scores:
        avg = round(sum(st.session_state.scores) / len(st.session_state.scores), 2)
        p1.metric("Questions", len(st.session_state.scores))
        p2.metric("Avg Score", avg)
    else:
        p1.metric("Questions", 0)
        p2.metric("Avg Score", "-")

    st.divider()

    # ---- Cost (Horizontal) ----
    st.subheader("💰 Usage & Cost")
    c1, c2, c3 = st.columns(3)

    c1.metric("Prompt", st.session_state.token_usage["prompt"])
    c2.metric("Completion", st.session_state.token_usage["completion"])
    c3.metric("USD", f"${st.session_state.token_usage['cost']:.6f}")

    st.divider()

    # ---- Reset ----
    if st.button("🟢 Start New Interview", type="primary"):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()

# ================== UI ==================

st.title("🤖 AI Interview Preparation App")

# ---------- Job Description ----------

st.subheader("1️⃣ Job Description")

job_desc = st.text_area("Paste the job description", height=150)

if st.button("🔍 Analyze Job Description", type="primary"):
    with st.spinner("Analyzing job description..."):
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": JD_ANALYSIS_PROMPT},
                {"role": "user", "content": job_desc}
            ],
            temperature=0.3
        )

        content = resp.choices[0].message.content.strip()

        if content == "INVALID_JOB_DESCRIPTION":
            st.error("❌ This does not look like a job description.")
        else:
            st.session_state.interview_strategy = content
            st.session_state.job_analyzed = True

        if resp.usage:
            update_cost(resp.usage)

    st.rerun()

# ---------- Start Interview ----------

st.subheader("2️⃣ Start Interview")

if st.session_state.job_analyzed:

    st.session_state.difficulty = st.selectbox(
        "Difficulty",
        ["Easy", "Medium", "Hard"],
        disabled=st.session_state.interview_started
    )

    st.session_state.persona = st.selectbox(
        "Interviewer Persona",
        ["Friendly", "Neutral", "Strict"],
        disabled=st.session_state.interview_started
    )

    if st.button("🚀 Start Interview", type="primary", disabled=st.session_state.interview_started):
        system_prompt = build_interview_system_prompt(
            st.session_state.interview_strategy,
            st.session_state.difficulty,
            st.session_state.persona
        )

        st.session_state.messages = [{"role": "system", "content": system_prompt}]
        st.session_state.interview_started = True

        first_q = client.chat.completions.create(
            model=MODEL_NAME,
            messages=st.session_state.messages
        )

        st.session_state.messages.append(
            {"role": "assistant", "content": first_q.choices[0].message.content}
        )

        if first_q.usage:
            update_cost(first_q.usage)

        st.rerun()

else:
    st.info("Analyze the job description first.")

# ---------- Interview Session ----------

if st.session_state.interview_started:
    st.subheader("💬 Interview Session")

    for msg in st.session_state.messages[1:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Your answer")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.write(user_input)

        reply = client.chat.completions.create(
            model=MODEL_NAME,
            messages=st.session_state.messages
        )

        content = reply.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": content})

        score = extract_score(content)
        if score is not None:
            st.session_state.scores.append(score)

        if reply.usage:
            update_cost(reply.usage)

        st.rerun()
