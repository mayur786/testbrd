import streamlit as st
from openai import OpenAI
from datetime import datetime

#MODEL = "google/gemini-3.5-flash"
MODEL = "deepseek/deepseek-chat"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=st.secrets["OPENROUTER_API_KEY"]
)

if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "system",
        "content": """
You are a Business Analyst for Ad Hoc Data Requests.

Collect:
1. Business objective and why data is needed.
2. Actions/decisions supported.
3. Required columns, descriptions, inclusion & exclusion criteria.
4. Previous Power BI/report/dashboard usage.
5. Previous Data Science/Analytics/Data Engineering SPOC.
6. One-time or recurring requirement.
7. Timeline and business impact.
8. Final consumers and regulatory usage.

Rules:
- business category - wheels passenger vehicle, commercial vehicle, business loan, sme, leasing , fixed deposit
 - Ask only one question at a time.
- minimum 30 words.
- Never ask the same question twice.
- Ask only for missing information.

When ALL information is collected, reply EXACTLY:

Discovery Complete. Click Generate BRD.
"""
    }]

if "question_count" not in st.session_state:
    st.session_state.question_count = 0

LOG_FILE = "conversation_log.txt"

st.title("Business Data Request Portal")

st.progress(min(st.session_state.question_count, 10) / 10)
st.write(f"Discovery Progress: {min(st.session_state.question_count,10)}/10")

for msg in st.session_state.messages:
    if msg["role"] == "system":
        continue
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("Describe your business problem...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.write(prompt)

    response = client.chat.completions.create(
        model=MODEL,
        messages=st.session_state.messages[-20:],
        max_tokens=300
    )

    answer = response.choices[0].message.content

    if "Discovery Complete" not in answer and st.session_state.question_count < 10:
        st.session_state.question_count += 1

    st.session_state.messages.append(
        {"role": "assistant", "content": answer}
    )

    with st.chat_message("assistant"):
        st.write(answer)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n\n[{datetime.now()}]\n")
        f.write(f"USER: {prompt}\n")
        f.write(f"BOT: {answer}\n")

discovery_complete = any(
    m["role"] == "assistant" and "Discovery Complete" in m["content"]
    for m in st.session_state.messages
)

if discovery_complete:

    if st.button("Generate BRD"):

        conversation = "\n".join(
            [
                f"{m['role'].upper()}: {m['content']}"
                for m in st.session_state.messages
                if m["role"] != "system"
            ]
        )

        brd_prompt = """
You are a Senior Business Analyst.

Generate a complete Business Requirements Document.

Do NOT ask questions.
Do NOT continue discovery.
Use available information only.

Structure:

# Executive Summary
# Business Objective
# Business Justification
# Actions / Decisions Supported
# Data Requirements
# Inclusion Criteria
# Exclusion Criteria
# Historical Data Consumption
# Previous SPOC Engagement
# Delivery Requirements
# Future Enhancements
# Timeline & Criticality
# End Consumers
# Regulatory / Compliance Impact
# Assumptions
# Risks
# Recommendations
# Sign-Off

Generate at least 1000 words.
"""

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": brd_prompt},
                {"role": "user", "content": conversation}
            ],
            max_tokens=3000,
            temperature=0.2
        )

        brd = response.choices[0].message.content

        st.subheader("Generated BRD")
        st.markdown(brd)

        st.download_button(
            "Download BRD",
            brd,
            "generated_brd.md",
            "text/markdown"
        )
