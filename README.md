# 🤖 AI Interview Preparation App

An AI-powered interview preparation web application built with **Streamlit** and **OpenAI APIs**.  
The app analyzes a job description, derives an interview strategy, and conducts a realistic multi-turn interview while applying production-aware **security and safety mechanisms**.

---

## 🚀 Getting Started

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## 🌍 Deployment

Deployable on:
- Azure App Service
https://interview-chatbot-azhpdegcgcg2czhp.westeurope-01.azurewebsites.net/
- Streamlit Community Cloud
https://app7py-9jxge28hydsblebqsrbhbt.streamlit.app/

---

![image](https://github.com/ly05010419/interview-simulation/blob/main/screenshot.png?raw=true)



## 🧱 Architecture Overview

```
User
 ↓
Streamlit UI
 ↓
Input Guards (length, intent validation)
 ↓
OpenAI Moderation API (Input)
 ↓
AI Interviewer (Chat Completion)
 ↓
OpenAI Moderation API (Output)
 ↓
User
```

---

## ✨ Features

### 🧾 Job Description Analysis
- Paste a job description
- Automatically extracts:
  - Seniority level
  - Key technical & soft skills
  - Interview focus areas
  - Interview strategy & evaluation criteria
- Analysis runs in a **modal-style dialog** for better UX

---

### 🎯 Configurable Interview Setup
- **Difficulty levels**
  - Easy / Medium / Hard
- **Interviewer personas**
  - Strict
  - Neutral
  - Friendly
- Selections are **locked immediately** when the interview starts

---

### 💬 Full Interview Chat Experience
- One question at a time
- Candidate answers via chat
- AI provides:
  - Concise feedback
  - **Score (0–5)** for each answer

---

## 🔐 Testing & Security

This project applies a **defense-in-depth security strategy** to prevent misuse, prompt injection, and unsafe content.

### Security Layers

1. **Input Length Validation**  
   Prevents excessive or abusive inputs.

2. **Intent Validation (Prompt Injection Guard)**  
   An LLM-based guard ensures the input is a valid interview answer and not an attempt to override system instructions.

3. **OpenAI Moderation API – Input**  
   Blocks unsafe or policy-violating content before it reaches the interviewer model.

4. **OpenAI Moderation API – Output**  
   Filters unexpected or unsafe model responses before displaying them to the user.

5. **Rate Limiting (Session-based)**  
   Limits the number of requests per session to prevent API abuse and cost overruns.

---

### 🧪 Security Testing Strategy

Security mechanisms were validated using **black-box testing**, simulating misuse directly through the UI.

| Test Case | Example Input | Expected Result |
|----------|---------------|----------------|
| Normal Answer | Relevant technical explanation | Accepted |
| Prompt Injection | “Ignore previous instructions…” | Rejected |
| Unsafe Input | Violent or harmful text | Blocked |
| Long Input | >800 characters | Rejected |
| Rate Limit | >30 requests | Blocked |
| Unsafe Output | Model-generated unsafe text | Filtered |

---

### 📊 Performance & Cost Tracking
- Tracks:
  - Number of questions answered
  - Average score
  - Prompt & completion tokens
  - Estimated API cost (USD)

---

### 🔐 Safety & Misuse Protection
- Input and output moderation via OpenAI Moderation API
- Prompt-injection guard for user answers
- Rate limiting per session

---

### 🔄 Reset Without Losing Context
- **Start New Interview** resets:
  - Chat history
  - Scores
  - Cost
- Keeps job description analysis for reuse

---

## 🛠️ Tech Stack

- **Frontend / App Framework:** Streamlit
- **LLM API:** OpenAI
- **Language:** Python 3.9+
- **State Management:** Streamlit session_state

---

## 📂 Project Structure

```text
.
├── app.py
├── requirements.txt
├── .streamlit/
│   └── config.toml
└── README.md
```

---

## 🎨 Theme Customization

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#2ECC71"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F5F5F5"
textColor = "#262730"
```

Restart Streamlit after changes.

---

