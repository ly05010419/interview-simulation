import streamlit as st
from openai import OpenAI
import openai
import os
import IPython
import json

from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# 使用 OpenAI 官方在线 API
client = OpenAI(api_key=api_key)


# -----------------------------
# 面试官角色定义
# -----------------------------
ROLE_PRESETS = {
    "AI 技术面试官": "You are a senior AI/ML interviewer with deep expertise in deep learning, LLMs, transformers, optimization, "
    "vector embeddings, training pipelines, and inference engineering. Ask challenging interview questions. "
    "Analyze candidate responses with technical rigor.",
    "Python 技术面试官": "You are a senior Python engineering interviewer. Ask questions about language fundamentals, async, OOP, "
    "decorators, generators, memory model, and performance optimization. Evaluate code quality and reasoning.",
    "JavaScript 技术面试官": "You are a senior JavaScript and frontend engineering interviewer. Ask questions about event loop, closures, "
    "Promise, React/Vue reactivity, browser internals, async behavior, Node.js, and performance optimization.",
    "Java 技术面试官": "You are a senior Java backend interviewer experienced in concurrency, JVM memory model, GC, Spring framework, "
    "transaction management, and distributed systems. Ask deep questions and require structured reasoning.",
    "Prompt Engineer 面试官（提示工程 / 大模型行为控制）": "你是一名资深的提示工程（Prompt Engineering）中文面试官，专长于 LLM 行为设计、推理控制、提示词优化、上下文管理、评估方法以及模型对齐。你的面试风格具有分析性、探究性，并且高度结构化。你会提出有关提示模式（ReAct、链式思维 Chain-of-Thought、树式思维 Tree-of-Thought、RAG、自我纠错）的提问，以及关于 token 效率、幻觉减少、智能体（agent）设计、如何系统性评估 LLM 输出质量的问题。你会要求候选人解释为什么某些提示策略有效、如何为特定任务设计提示词，以及如何调试意外的模型行为。不要提供提示。保持专业、严谨的语气，并始终通过追问深入问题本质。你作为面试官严格按照这个流程一步步执行。 整个流程分为 5 个阶段： 开场说明（Introduce） 基础理解（Fundamental Knowledge） 提示设计能力（Prompt Design Skills） 问题诊断能力（Debugging & Evaluation） 综合任务（Practical Scenario） 面试官总结与评分（Evaluation Summary）",
}

# -----------------------------
# 评分系统 Prompt
# -----------------------------
SCORING_PROMPT = """
You are an expert interviewer. Your task is to evaluate the candidate's answer strictly and fairly.

Score from 0 to 5 based on:
1. Technical correctness
2. Depth of reasoning
3. Clarity and structure
4. Practical relevance
5. Confidence and communication

Return JSON only in this format:
{
  "score": 0-5,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "summary": "..."
}
Be objective. Do not score too high.
"""


# -----------------------------
# AI 评分函数
# -----------------------------
def evaluate_answer(question, user_answer, model="gpt-4o-mini"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SCORING_PROMPT},
            {"role": "user", "content": f"Question: {question}\nAnswer: {user_answer}"},
        ],
    )
    return json.loads(response.choices[0].message.content)


# -----------------------------
# 生成面试官问题
# -----------------------------
def generate_question(role, model="gpt-4o-mini"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": ROLE_PRESETS[role]},
            {"role": "user", "content": "Ask one challenging interview question."},
        ],
    )
    return response.choices[0].message.content


# ============================================================
#                  Streamlit APP UI
# ============================================================

st.title("🧑‍🏫 AI 模拟技术面试系统")
st.caption("支持：AI / Python / JavaScript / Java  | 自动提问 + 自动评分 + 面试报告")

# -----------------------------
# 选择面试官
# -----------------------------
role = st.selectbox("请选择面试官：", list(ROLE_PRESETS.keys()))
st.info(f"当前面试官角色：{role}")

# -----------------------------
# 初始化会话状态
# -----------------------------
if "current_question" not in st.session_state:
    st.session_state.current_question = ""

if "history" not in st.session_state:
    st.session_state.history = []  # 保存所有问答

# -----------------------------
# 生成面试问题按钮
# -----------------------------
if st.button("🎤 生成下一道面试题"):
    st.session_state.current_question = generate_question(role)
    st.session_state.history.append(
        {"role": "interviewer", "content": st.session_state.current_question}
    )
    st.success("面试官已提出下一道面试题！")

# 显示当前问题
if st.session_state.current_question:
    st.subheader("📌 当前面试题：")
    st.write(st.session_state.current_question)

# -----------------------------
# 候选人回答输入
# -----------------------------
answer = st.text_area("请在此输入你的回答：")

# -----------------------------
# 评分按钮
# -----------------------------
if st.button("⭐ AI 自动评分"):
    if not answer:
        st.warning("请先输入回答")
    else:
        st.session_state.history.append({"role": "candidate", "content": answer})
        result = evaluate_answer(st.session_state.current_question, answer)

        st.subheader(f"评分结果：⭐ {result['score']} / 5")

        st.write("### 👍 优点")
        for s in result["strengths"]:
            st.write("- " + s)

        st.write("### ⚠️ 不足")
        for w in result["weaknesses"]:
            st.write("- " + w)

        st.write("### 📝 总结")
        st.info(result["summary"])

# -----------------------------
# 展示完整对话历史
# -----------------------------
st.subheader("📚 面试对话记录")

for chat in st.session_state.history:
    if chat["role"] == "interviewer":
        st.markdown(f"**👨‍🏫 面试官：** {chat['content']}")
    else:
        st.markdown(f"**🧑‍💼 候选人：** {chat['content']}")
