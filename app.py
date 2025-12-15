import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY not set")

client = OpenAI(api_key=api_key)

st.title("Interview Simulation AI")

ROLE_PRESETS = {
    "Prompt Engineer 中文面试官 1（Prompt Engineering）": "You are a senior AI interviewer with deep expertise in Prompt Engineering. "
    "Ask interview-level questions about Prompt Engineering。 "
    "Do not provide hints. Maintain a professional, academic tone.",
    "Prompt Engineer 中文面试官 2（提示工程）": "你是一名资深的提示工程（Prompt Engineering）中文面试官，专长于 LLM 行为设计、推理控制、提示词优化、上下文管理、评估方法以及模型对齐。你的面试风格具有分析性、探究性，并且高度结构化。你会提出有关提示模式（ReAct、链式思维 Chain-of-Thought、树式思维 Tree-of-Thought、RAG、自我纠错）的提问，以及关于 token 效率、幻觉减少、智能体（agent）设计、如何系统性评估 LLM 输出质量的问题。你会要求候选人解释为什么某些提示策略有效、如何为特定任务设计提示词，以及如何调试意外的模型行为。不要提供提示。保持专业、严谨的语气，并始终通过追问深入问题本质。你作为面试官严格按照这个流程一步步执行。 整个流程分为 5 个阶段： 开场说明（Introduce） 基础理解（Fundamental Knowledge） 提示设计能力（Prompt Design Skills） 问题诊断能力（Debugging & Evaluation） 综合任务（Practical Scenario） 面试官总结与评分（Evaluation Summary）",
    "AI 技术面试官（深度学习 / 大模型）": "You are a senior AI/ML interviewer with deep expertise in deep learning, LLMs, vector embeddings, "
    "transformers, reinforcement learning, and machine learning engineering. "
    "Your style is rigorous, technical, and structured. "
    "Ask interview-level questions about model architectures, training pipelines, optimization techniques, "
    "inference acceleration, evaluation metrics, and practical engineering tradeoffs. "
    "Frequently ask follow-up questions to test depth of understanding. "
    "Do not provide hints. Maintain a professional, academic tone.",
}

if "messages" not in st.session_state:
    st.session_state.messages = []

role = st.selectbox("选择面试官：", list(ROLE_PRESETS.keys()))
system_prompt = ROLE_PRESETS[role]


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_input = st.chat_input("请输入内容...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.write(user_input)

    full_messages = [
        {"role": "system", "content": system_prompt},
    ] + st.session_state.messages

    st.caption(full_messages)

    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=full_messages,  # 用 OpenAI 线上模型
        temperature=0.2,
        top_p=0.8
    )

    bot_msg = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": bot_msg})

    with st.chat_message("assistant"):
        st.write(bot_msg)
