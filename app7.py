import streamlit as st
from openai import OpenAI
import re
import os
from dotenv import load_dotenv

# ================== ENV ==================
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set")

client = OpenAI(api_key=api_key)

MODEL_NAME = "gpt-4o-mini"
MAX_INPUT_LENGTH = 800
MAX_REQUESTS_PER_SESSION = 30

PRICE_INPUT_PER_M = 0.05
PRICE_OUTPUT_PER_M = 0.40

# ================== PROMPTS ==================

JD_ANALYSIS_PROMPT = """
You are a senior technical recruiter and interviewer.

Analyze the following job description and extract:
1. Seniority level
2. Key technical skills
3. Soft skills
4. Interview focus areas
5. Interview strategy
6. Interviewer guidelines
7. Evaluation criteria

Output format:
- Seniority:
- Key Skills:
- Soft Skills:
- Interview Focus:
- Interview Strategy:
- Interviewer Guidelines:
- Evaluation Criteria:
"""

INPUT_GUARD_PROMPT = """
You are a security guard for an AI interview application.

If the input is a valid interview answer respond:
VALID

Otherwise respond:
INVALID
"""

def build_interview_system_prompt(strategy, difficulty, persona):
    return f"""
You are a senior technical interviewer.

Interviewer persona: {persona}
Interview difficulty: {difficulty}

Persona behavior:
- Strict: Critical, challenging, conservative scoring
- Neutral: Objective and professional
- Friendly: Encouraging and supportive

Difficulty levels:
- Easy: Fundamentals
- Medium: Practical experience
- Hard: Deep knowledge

Use the following interview strategy:
{strategy}

Rules:
- Ask one question at a time
- Wait for the answer
- Give concise feedback
- Always include: Score: X/5
- Ask the next question
"""

# ================== SECURITY ==================

def check_moderation(text):
    r = client.moderations.create(
        model="omni-moderation-latest",
        input=text,
    )
    return not r.results[0].flagged


def validate_user_input(text):
    r = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": INPUT_GUARD_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0.0,
    )
    return r.choices[0].message.content.startswith("VALID")

# ================== COST ==================

def update_cost(usage):
    cost = (
        usage.prompt_tokens / 1_000_000 * PRICE_INPUT_PER_M +
        usage.completion_tokens / 1_000_000 * PRICE_OUTPUT_PER_M
    )
    st.session_state.token_usage["prompt_tokens"] += usage.prompt_tokens
    st.session_state.token_usage["completion_tokens"] += usage.completion_tokens
    st.session_state.token_usage["cost_usd"] += cost

# ================== CORE ==================

def analyze_job_description(text):
    r = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": JD_ANALYSIS_PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0.3,
    )
    if r.usage:
        update_cost(r.usage)
    return r.choices[0].message.content


def call_interviewer(messages):
    r = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.7,
    )
    if r.usage:
        update_cost(r.usage)

    reply = r.choices[0].message.content
    if not check_moderation(reply):
        return "⚠️ Response filtered for safety."
    return reply


def extract_score(text):
    m = re.search(r"Score:\s*([0-5])\s*/\s*5", text)
    return int(m.group(1)) if m else None


def reset_interview_only():
    st.session_state.interview_started = False
    st.session_state.starting_interview = False
    st.session_state.messages = []
    st.session_state.scores = []
    st.session_state.request_count = 0
    st.session_state.token_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "cost_usd": 0.0
    }

# ================== SESSION STATE ==================

st.session_state.setdefault("job_analyzed", False)
st.session_state.setdefault("interview_started", False)
st.session_state.setdefault("starting_interview", False)

st.session_state.setdefault("difficulty", "Medium")
st.session_state.setdefault("persona", "Neutral")

st.session_state.setdefault("messages", [])
st.session_state.setdefault("scores", [])
st.session_state.setdefault("request_count", 0)

st.session_state.setdefault("show_jd_dialog", False)

st.session_state.setdefault("token_usage", {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "cost_usd": 0.0
})

# ================== UI ==================

st.title("🤖 AI Interview Preparation App")

# ---------- Job Description ----------
st.subheader("1️⃣ Job Description")

job_desc = st.text_area(
    "Paste the job description",
    height=160,
    disabled=st.session_state.interview_started
)

if st.button(
    "🔍 Analyze Job Description",
    type="primary",
    disabled=st.session_state.interview_started
) and job_desc:
    st.session_state.show_jd_dialog = True
    st.rerun()

# ---------- Dialog ----------
if st.session_state.show_jd_dialog:
    st.dialog("Job Analysis")
    st.markdown("### ⏳ Analyzing job description…")

    st.session_state.interview_strategy = analyze_job_description(job_desc)
    st.session_state.job_analyzed = True
    st.session_state.show_jd_dialog = False
    st.rerun()

# ---------- Strategy ----------
if st.session_state.job_analyzed:
    st.markdown("### 📌 Interview Strategy")
    st.markdown(st.session_state.interview_strategy)

# ---------- Start Interview ----------
st.subheader("2️⃣ Start Interview")

if st.session_state.job_analyzed:

    st.markdown("#### 🎯 Difficulty")
    st.session_state.difficulty = st.radio(
        "Difficulty",
        ["Easy", "Medium", "Hard"],
        horizontal=True,
        disabled=st.session_state.interview_started
    )

    st.markdown("#### 🎭 Interviewer Persona")
    st.session_state.persona = st.radio(
        "Persona",
        ["Strict", "Neutral", "Friendly"],
        horizontal=True,
        disabled=st.session_state.interview_started
    )

    if st.button(
        "🚀 Start Interview",
        type="primary",
        disabled=st.session_state.interview_started
    ):
        st.session_state.interview_started = True
        st.session_state.starting_interview = True
        st.rerun()

# ---------- Phase 2 ----------
if st.session_state.starting_interview:
    system_prompt = build_interview_system_prompt(
        st.session_state.interview_strategy,
        st.session_state.difficulty,
        st.session_state.persona
    )
    st.session_state.messages = [{"role": "system", "content": system_prompt}]
    first_q = call_interviewer(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": first_q})
    st.session_state.starting_interview = False
    st.rerun()

# ---------- Interview ----------
if st.session_state.interview_started and st.session_state.messages:
    st.subheader("💬 Interview Session")

    for msg in st.session_state.messages[1:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Type your answer...")

    if user_input:
        if len(user_input) > MAX_INPUT_LENGTH:
            st.warning("Answer too long.")
            st.stop()

        if not check_moderation(user_input):
            st.error("Unsafe input.")
            st.stop()

        if not validate_user_input(user_input):
            st.warning("Invalid interview answer.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        reply = call_interviewer(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": reply})

        score = extract_score(reply)
        if score is not None:
            st.session_state.scores.append(score)

        with st.chat_message("assistant"):
            st.write(reply)

# ---------- Performance ----------
if st.session_state.scores:
    st.subheader("📊 Performance")
    avg = round(sum(st.session_state.scores) / len(st.session_state.scores), 2)
    c1, c2 = st.columns(2)
    c1.metric("Questions Answered", len(st.session_state.scores))
    c2.metric("Average Score", avg)

# ---------- Cost ----------
if st.session_state.token_usage["prompt_tokens"] > 0:
    st.subheader("💰 Usage & Cost")
    c1, c2, c3 = st.columns(3)
    c1.metric("Prompt Tokens", st.session_state.token_usage["prompt_tokens"])
    c2.metric("Completion Tokens", st.session_state.token_usage["completion_tokens"])
    c3.metric("Estimated Cost (USD)", f"${st.session_state.token_usage['cost_usd']:.6f}")

# ---------- Reset ----------
st.divider()
st.subheader("🔄 Interview Reset")

if st.button("🆕 Start New Interview", type="primary"):
    reset_interview_only()
    st.success("Interview reset. Job analysis is kept.")
    st.rerun()
