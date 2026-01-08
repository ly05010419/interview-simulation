import streamlit as st
from openai import OpenAI
import openai
import os
import re
import logging
import time
from typing import Optional, Tuple
from dotenv import load_dotenv

# ================== LOGGING ==================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ================== SETUP ==================

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set")

client = OpenAI(api_key=api_key)

MODEL_NAME = "gpt-4o-mini"
MAX_INPUT_LENGTH = 800
MAX_REQUESTS_PER_SESSION = 30
MAX_REQUESTS_PER_MINUTE = 10
API_TIMEOUT = 30

PRICE_INPUT_PER_M = 0.05
PRICE_OUTPUT_PER_M = 0.40

# ================== PROMPTS ==================

JD_ANALYSIS_PROMPT = """
You are a senior technical recruiter.

Analyze the following job description and output:

- Seniority
- Key Skills
- Soft Skills
- Interview Focus
- Interview Strategy
- Interviewer Guidelines
- Evaluation Criteria
"""

JD_GUARD_PROMPT = """
You are a validator for a job interview preparation app.

If the input is a real job description, respond:
VALID

Otherwise respond:
INVALID
"""

ANSWER_GUARD_PROMPT = """
You are a security guard for an AI interview application.

If the input is a valid interview answer respond:
VALID

Otherwise:
INVALID
"""

def build_interview_system_prompt(strategy, difficulty, persona):
    return f"""
You are a senior technical interviewer.

Interview Strategy:
{strategy}

Difficulty: {difficulty}
Persona: {persona}

Rules:
- Ask one question at a time
- Wait for the answer
- Give feedback
- At the end of every response, include exactly:
Score: X/5
"""

# ================== SECURITY ==================

def check_moderation(text: str) -> bool:
    """
    Check if text passes OpenAI moderation.

    Args:
        text: Text to check

    Returns:
        True if content is safe, False otherwise
    """
    try:
        logger.info(f"Checking moderation for text (length: {len(text)})")
        r = client.moderations.create(
            model="omni-moderation-latest",
            input=text,
            timeout=API_TIMEOUT
        )
        result = not r.results[0].flagged
        logger.info(f"Moderation result: {'safe' if result else 'flagged'}")
        return result
    except openai.APITimeoutError:
        logger.error("Moderation API timeout")
        st.error("⏱️ Request timeout - please try again")
        return False
    except openai.RateLimitError:
        logger.error("Moderation rate limit exceeded")
        st.error("🚫 Rate limit exceeded - please wait a moment")
        return False
    except openai.APIError as e:
        logger.error(f"Moderation API error: {e}")
        st.error(f"❌ API error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in moderation: {e}", exc_info=True)
        st.error("❌ An unexpected error occurred")
        return False

def validate_job_description(text: str) -> bool:
    """
    Validate if text is a legitimate job description.

    Args:
        text: Text to validate

    Returns:
        True if valid job description, False otherwise
    """
    try:
        logger.info("Validating job description")
        r = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": JD_GUARD_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0,
            timeout=API_TIMEOUT
        )
        result = r.choices[0].message.content.strip().startswith("VALID")
        logger.info(f"Job description validation: {'valid' if result else 'invalid'}")
        return result
    except openai.APITimeoutError:
        logger.error("Job description validation timeout")
        st.error("⏱️ Validation timeout - please try again")
        return False
    except openai.RateLimitError:
        logger.error("Job description validation rate limit")
        st.error("🚫 Rate limit exceeded - please wait")
        return False
    except openai.APIError as e:
        logger.error(f"Job description validation API error: {e}")
        st.error(f"❌ API error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in job description validation: {e}", exc_info=True)
        st.error("❌ Validation failed")
        return False

def validate_user_input(text: str) -> bool:
    """
    Validate if text is a valid interview answer (not prompt injection).

    Args:
        text: User input to validate

    Returns:
        True if valid answer, False otherwise
    """
    try:
        logger.info(f"Validating user input (length: {len(text)})")
        r = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": ANSWER_GUARD_PROMPT},
                {"role": "user", "content": text}
            ],
            temperature=0,
            timeout=API_TIMEOUT
        )
        result = r.choices[0].message.content.strip().startswith("VALID")
        logger.info(f"User input validation: {'valid' if result else 'invalid'}")
        return result
    except openai.APITimeoutError:
        logger.error("User input validation timeout")
        st.error("⏱️ Validation timeout - please try again")
        return False
    except openai.RateLimitError:
        logger.error("User input validation rate limit")
        st.error("🚫 Rate limit exceeded - please wait")
        return False
    except openai.APIError as e:
        logger.error(f"User input validation API error: {e}")
        st.error(f"❌ API error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in user input validation: {e}", exc_info=True)
        st.error("❌ Validation failed")
        return False

# ================== HELPERS ==================

def check_rate_limit() -> Tuple[bool, str]:
    """
    Check if rate limits are exceeded.

    Returns:
        Tuple of (is_allowed, error_message)
    """
    # Initialize counters if not exist
    if "request_count" not in st.session_state:
        st.session_state.request_count = 0
    if "request_timestamps" not in st.session_state:
        st.session_state.request_timestamps = []

    current_time = time.time()

    # Check session total limit
    if st.session_state.request_count >= MAX_REQUESTS_PER_SESSION:
        logger.warning(f"Session request limit exceeded: {st.session_state.request_count}")
        return False, f"Session limit reached ({MAX_REQUESTS_PER_SESSION} requests). Please start a new interview."

    # Clean old timestamps (older than 1 minute)
    st.session_state.request_timestamps = [
        t for t in st.session_state.request_timestamps
        if current_time - t < 60
    ]

    # Check per-minute limit
    if len(st.session_state.request_timestamps) >= MAX_REQUESTS_PER_MINUTE:
        logger.warning(f"Per-minute rate limit exceeded: {len(st.session_state.request_timestamps)}")
        return False, f"Too many requests. Please wait a moment (max {MAX_REQUESTS_PER_MINUTE}/minute)."

    # Record this request
    st.session_state.request_count += 1
    st.session_state.request_timestamps.append(current_time)

    logger.info(f"Rate limit check passed. Total: {st.session_state.request_count}, Last minute: {len(st.session_state.request_timestamps)}")
    return True, ""

def update_cost(usage):
    st.session_state.token_usage["prompt"] += usage.prompt_tokens
    st.session_state.token_usage["completion"] += usage.completion_tokens
    st.session_state.token_usage["cost"] += (
        usage.prompt_tokens / 1e6 * PRICE_INPUT_PER_M +
        usage.completion_tokens / 1e6 * PRICE_OUTPUT_PER_M
    )

def extract_score(text: str) -> Optional[int]:
    """
    Extract score from AI response text.

    Args:
        text: Response text containing score

    Returns:
        Integer score 0-5, or None if not found
    """
    try:
        # Support multiple score formats
        patterns = [
            r"Score:\s*([0-5])\s*/\s*5",
            r"Score:\s*([0-5])/5",
            r"score:\s*([0-5])\s*/\s*5",
        ]

        for pattern in patterns:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                score = int(m.group(1))
                if 0 <= score <= 5:
                    logger.info(f"Extracted score: {score}")
                    return score

        logger.warning(f"Failed to extract score from response (length: {len(text)})")
        return None
    except Exception as e:
        logger.error(f"Error extracting score: {e}", exc_info=True)
        return None

# ================== SESSION STATE ==================

defaults = {
    "job_analyzed": False,
    "interview_started": False,
    "messages": [],
    "scores": [],
    "difficulty": "Medium",
    "persona": "Neutral",
    "token_usage": {"prompt": 0, "completion": 0, "cost": 0.0},
    "interview_strategy": "",
    "request_count": 0,
    "request_timestamps": []
}

for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ================== SIDEBAR ==================

with st.sidebar:
    st.header("📌 Interview Panel")

    if st.session_state.job_analyzed:
        with st.expander("Interview Strategy", expanded=True):
            st.markdown(st.session_state.interview_strategy)
    else:
        st.info("Analyze a job description first.")

    st.divider()

    st.subheader("📊 Performance")
    c1, c2 = st.columns(2)
    if st.session_state.scores:
        c1.metric("Questions", len(st.session_state.scores))
        c2.metric("Avg Score", round(sum(st.session_state.scores)/len(st.session_state.scores), 2))
    else:
        c1.metric("Questions", 0)
        c2.metric("Avg Score", "-")

    st.divider()

    st.subheader("💰 Usage & Cost")
    c1, c2, c3 = st.columns(3)
    c1.metric("Prompt", st.session_state.token_usage["prompt"])
    c2.metric("Completion", st.session_state.token_usage["completion"])
    c3.metric("USD", f"${st.session_state.token_usage['cost']:.6f}")

    st.divider()

    if st.button("🟢 Start New Interview", type="primary"):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()

# ================== UI ==================

st.title("🤖 AI Interview Preparation App")

# ---------- Job Description ----------

st.subheader("1️⃣ Job Description")

job_desc = st.text_area(
    "Paste the job description",
    height=150,
    disabled=st.session_state.interview_started
)

if st.button(
    "🔍 Analyze Job Description",
    type="primary",
    disabled=st.session_state.interview_started
):
    # Rate limit check
    rate_ok, rate_msg = check_rate_limit()
    if not rate_ok:
        st.error(rate_msg)
        st.stop()

    if not check_moderation(job_desc):
        st.error("Job description violates safety policy.")
        st.stop()

    if not validate_job_description(job_desc):
        st.warning("This does not look like a job description.")
        st.stop()

    with st.spinner("Analyzing job description..."):
        try:
            logger.info("Starting job description analysis")
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": JD_ANALYSIS_PROMPT},
                    {"role": "user", "content": job_desc}
                ],
                temperature=0.3,
                timeout=API_TIMEOUT
            )

            st.session_state.interview_strategy = resp.choices[0].message.content
            st.session_state.job_analyzed = True

            if resp.usage:
                update_cost(resp.usage)

            logger.info("Job description analysis completed successfully")
        except openai.APITimeoutError:
            logger.error("Job analysis timeout")
            st.error("⏱️ Request timeout - please try again")
            st.stop()
        except openai.RateLimitError:
            logger.error("Job analysis rate limit")
            st.error("🚫 Rate limit exceeded - please wait")
            st.stop()
        except openai.APIError as e:
            logger.error(f"Job analysis API error: {e}")
            st.error(f"❌ API error: {str(e)}")
            st.stop()
        except Exception as e:
            logger.error(f"Unexpected error in job analysis: {e}", exc_info=True)
            st.error("❌ Analysis failed - please try again")
            st.stop()

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

    if st.button(
        "🚀 Start Interview",
        type="primary",
        disabled=st.session_state.interview_started
    ):
        # Rate limit check
        rate_ok, rate_msg = check_rate_limit()
        if not rate_ok:
            st.error(rate_msg)
            st.stop()

        system_prompt = build_interview_system_prompt(
            st.session_state.interview_strategy,
            st.session_state.difficulty,
            st.session_state.persona
        )

        st.session_state.messages = [{"role": "system", "content": system_prompt}]
        st.session_state.interview_started = True

        try:
            logger.info("Starting interview - generating first question")
            first_q = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.messages,
                timeout=API_TIMEOUT
            )

            st.session_state.messages.append(
                {"role": "assistant", "content": first_q.choices[0].message.content}
            )

            if first_q.usage:
                update_cost(first_q.usage)

            logger.info("First question generated successfully")
        except openai.APITimeoutError:
            logger.error("Start interview timeout")
            st.session_state.interview_started = False
            st.error("⏱️ Request timeout - please try again")
            st.stop()
        except openai.RateLimitError:
            logger.error("Start interview rate limit")
            st.session_state.interview_started = False
            st.error("🚫 Rate limit exceeded - please wait")
            st.stop()
        except openai.APIError as e:
            logger.error(f"Start interview API error: {e}")
            st.session_state.interview_started = False
            st.error(f"❌ API error: {str(e)}")
            st.stop()
        except Exception as e:
            logger.error(f"Unexpected error starting interview: {e}", exc_info=True)
            st.session_state.interview_started = False
            st.error("❌ Failed to start interview - please try again")
            st.stop()

        st.rerun()

# ---------- Interview ----------

if st.session_state.interview_started:
    st.subheader("💬 Interview Session")

    for msg in st.session_state.messages[1:]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Your answer")

    if user_input:
        # Rate limit check
        rate_ok, rate_msg = check_rate_limit()
        if not rate_ok:
            st.error(rate_msg)
            st.stop()

        # Input validation
        if len(user_input) > MAX_INPUT_LENGTH:
            st.warning(f"Answer too long ({len(user_input)}/{MAX_INPUT_LENGTH} characters).")
            st.stop()

        if len(user_input.strip()) < 5:
            st.warning("Answer too short. Please provide a more detailed response.")
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

        try:
            logger.info(f"Processing user answer (length: {len(user_input)})")
            reply = client.chat.completions.create(
                model=MODEL_NAME,
                messages=st.session_state.messages,
                timeout=API_TIMEOUT
            )

            content = reply.choices[0].message.content

            # Validate AI output
            if not check_moderation(content):
                logger.error("AI output flagged by moderation")
                st.error("❌ Response validation failed - please try again")
                st.session_state.messages.pop()  # Remove user message
                st.stop()

            st.session_state.messages.append({"role": "assistant", "content": content})

            score = extract_score(content)
            if score is not None:
                st.session_state.scores.append(score)

            if reply.usage:
                update_cost(reply.usage)

            logger.info("Answer processed successfully")
        except openai.APITimeoutError:
            logger.error("Answer processing timeout")
            st.session_state.messages.pop()  # Remove user message
            st.error("⏱️ Request timeout - please try again")
            st.stop()
        except openai.RateLimitError:
            logger.error("Answer processing rate limit")
            st.session_state.messages.pop()  # Remove user message
            st.error("🚫 Rate limit exceeded - please wait")
            st.stop()
        except openai.APIError as e:
            logger.error(f"Answer processing API error: {e}")
            st.session_state.messages.pop()  # Remove user message
            st.error(f"❌ API error: {str(e)}")
            st.stop()
        except Exception as e:
            logger.error(f"Unexpected error processing answer: {e}", exc_info=True)
            st.session_state.messages.pop()  # Remove user message
            st.error("❌ Failed to process answer - please try again")
            st.stop()

        st.rerun()
