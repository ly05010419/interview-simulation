
# 🤖 AI Interview Preparation App

An AI-powered interview preparation web application built with **Streamlit** and **OpenAI APIs**.  
The app analyzes a job description, derives an interview strategy, and conducts a realistic multi-turn interview while applying production-aware **security and safety mechanisms**.

---

## ✨ Features

- Job Description analysis → interview strategy generation
- AI interviewer with multi-turn conversation
- Dynamic system prompts based on role & JD
- Real-time feedback and scoring (0–5)
- Single-page Streamlit UI
- Ready for deployment on Streamlit Cloud

---

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

## 🚦 Cost & Risk Control

- Early rejection of unsafe inputs avoids unnecessary token usage
- Session-based limits protect against request flooding
- Moderation applied before and after LLM calls

---

## 🛠️ Tech Stack

- **Frontend / App Framework:** Streamlit
- **Language:** Python
- **LLM Provider:** OpenAI
- **Security:** OpenAI Moderation API + LLM-based input guards

## 📌 Project Goals

This project was created as part of an **AI Engineering / Prompt Engineering  sprint 1**, with a strong focus on:

- Prompt design
- Context management
- Safety & misuse prevention
- Production-aware AI system design

---

## Bonus Points:

Medium:

- Deploy your app to the Internet.
- Calculate and provide output to the user on the price of the prompt.
- Add a separate text field or another field to include the job description (the position) you are applying for and getting interview preparation for that particular position (RAG).

Hard:

- Using Streamlit (Python) or React (JS) components, implement a full-fledged chatbot application instead of a one-time call to the OpenAI API.
- Deploy your app to one of these cloud providers: Gemini, AWS, or Azure.