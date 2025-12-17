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

# ===== Pricing (USD per 1M tokens) =====
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

def build_interview_system_prompt(strategy: str, difficulty: str, persona: str) -> str:
    return f"""
You are a senior technical interviewer.

Interview persona: {persona}

Persona behavior:
- Strict: Critical, challenging, conservative scoring
- Neutral: Objective and professional
- Friendly: Encouraging and supportive

Interview difficulty: {difficulty}

Difficulty levels:
- Easy: Fundamentals, junior level
- Medium: Practical experience, reasoning
- Hard: Deep knowledge, edge cases, trade-offs

Use the following interview strategy:
{strategy}

Rules:
- Ask one question at a time
- Wait for the candidate's answer
- Give concise feedback aligned with persona
- Always include: Score: X/5
- Do NOT ignore difficulty or persona
- After feedback, ask the next question
"""

# ================== SECURITY ==================

def check_moderation(text: str) -> bool:
    response = client.moderations.create(
        model="omni-moderation-latest",
        input=text,
    )
    return not response.results[0].flagged


def validate_user_input(user_text: str) -> bool:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": INPUT_GUARD_PROMPT},
            {"role": "user", "content": user_text}
        ],
        temperature=0.0,
    )
    return response.choices[0].message.content.startswith("VALID")

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

def analyze_job_description(jd_text: str) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": JD_ANALYSIS_PROMPT},
            {"role": "user", "content": jd_text}
        ],
        temperature=0.3,
    )
    if response.usage:
        update_cost(response.usage)
    return response.choices[0].message.content


def call_interviewer(messages: list) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.7,
    )
    if response.usage:
        update_cost(response.usage)

    reply = response.choices[0].message.content
    if not check_moderation(reply):
        return "⚠️ Response filtered for safety."
    return reply


def extract_score(text: str):
    match = re.search(r"Score:\s*([0-5])\s*/\s*5", text)
    return int(match.group(1)) if match else None


def reset_interview():
    st.session_state.messages = []
    st.session_state.scores = []
    st.session_state.interview_started = False
    st.session_state.request_count = 0
    st.session_state.token_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "cost_usd": 0.0
    }

# ================== SESSION STATE ==================

if "job_analyzed" not in st.session_state:
    st.session_state.job_analyzed = False

if "difficulty" not in st.session_state:
    st.session_state.difficulty = "Medium"

if "persona" not in st.session_state:
    st.session_state.persona = "Neutral"

if "messages" not in st.session_state:
    st.session_state.messages = []

if "scores" not in st.session_state:
    st.session_state.scores = []

if "token_usage" not in st.session_state:
    st.session_state.token_usage = {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "cost_usd": 0.0
    }

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

if "request_count" not in st.session_state:
    st.session_state.request_count = 0

# ================== UI ==================

st.title("🤖 AI Interview Preparation App")

# --- Job Description ---
st.subheader("1️⃣ Job Description")
job_desc = st.text_area("Paste the job description", height=160)

if st.button("🔍 Analyze Job Description") and job_desc:
    st.session_state.interview_strategy = analyze_job_description(job_desc)
    st.session_state.job_analyzed = True

if "interview_strategy" in st.session_state:
    st.markdown("### 📌 Interview Strategy")
    st.markdown(st.session_state.interview_strategy)

# --- Difficulty ---
st.subheader("🎯 Difficulty")
st.session_state.difficulty = st.radio(
    "Select difficulty",
    ["Easy", "Medium", "Hard"],
    horizontal=True
)

# --- Persona ---
st.subheader("🎭 Interviewer Persona")
st.session_state.persona = st.radio(
    "Select persona",
    ["Strict", "Neutral", "Friendly"],
    horizontal=True
)

# --- Start Interview ---
st.subheader("2️⃣ Start Interview")

if st.session_state.job_analyzed:
    if st.button("🚀 Start Interview") and not st.session_state.interview_started:
        system_prompt = build_interview_system_prompt(
            st.session_state.interview_strategy,
            st.session_state.difficulty,
            st.session_state.persona
        )
        st.session_state.messages = [{"role": "system", "content": system_prompt}]
        st.session_state.interview_started = True

        first_q = call_interviewer(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": first_q})
else:
    st.info("Please analyze the Job Description first.")

# --- Interview Session ---
if st.session_state.interview_started:
    st.subheader("💬 Interview Session")

    for msg in st.session_state.messages[1:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Type your answer...")

    if user_input:
        if st.session_state.request_count >= MAX_REQUESTS_PER_SESSION:
            st.error("Request limit reached.")
            st.stop()

        st.session_state.request_count += 1

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
        reply = call_interviewer(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": reply})

        score = extract_score(reply)
        if score is not None:
            st.session_state.scores.append(score)

        with st.chat_message("assistant"):
            st.write(reply)

# --- Performance (ONLY when scores exist) ---
if st.session_state.scores:
    st.subheader("📊 Performance")

    avg_score = round(sum(st.session_state.scores) / len(st.session_state.scores), 2)
    c1, c2 = st.columns(2)
    c1.metric("Questions Answered", len(st.session_state.scores))
    c2.metric("Average Score", avg_score)

# --- Usage & Cost (ONLY when tokens > 0) ---
if st.session_state.token_usage["prompt_tokens"] > 0:
    st.subheader("💰 Usage & Cost")

    c1, c2, c3 = st.columns(3)
    c1.metric("Prompt Tokens", st.session_state.token_usage["prompt_tokens"])
    c2.metric("Completion Tokens", st.session_state.token_usage["completion_tokens"])
    c3.metric(
        "Estimated Cost (USD)",
        f"${st.session_state.token_usage['cost_usd']:.6f}"
    )

# --- Reset ---
st.divider()
st.subheader("🔄 Interview Reset")

if st.button("🆕 Start New Interview"):
    reset_interview()
    st.success(
        "Interview reset. Session, score, and cost cleared. "
        "You can now start a new interview."
    )
    st.rerun()
