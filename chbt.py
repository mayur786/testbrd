import streamlit as st
from openai import OpenAI
from datetime import datetime
import json
import os

# -------------------
# CONFIG
# -------------------

API_KEY = "YOUR_OPENROUTER_KEY"

MODEL = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=st.secrets["OPENROUTER_API_KEY"] 
)

# -------------------
# SESSION
# -------------------

if "messages" not in st.session_state:

    st.session_state.messages = [
     {
    "role": "system",
    "content": """
You are a Business Analyst for Ad Hoc Data Requests.

Your objective is to collect ONLY these 10 items:

1. Is this the first time this data is requested?
2. Did you check existing Power BI dashboards?
3. Problem Statement
4. Business Requirement
5. Senior Management Consumer
6. ETA Required
7. Data Science Dependency
8. Has similar data been delivered before?
9. Is PII data required?
10. Success Criteria

Rules:

- Ask only ONE question at a time.
- Maximum 15 words.
- Never ask the same question twice.
- Infer answers whenever possible.
- Maintain internal progress.
- If user already provided information, mark it completed.
- Once all 10 items are captured:
    - Stop asking questions.
    - Reply only:
      "Discovery Complete. Click Generate BRD."
- Do not ask unnecessary follow-up questions.
- Be concise.
"""
}    ]

# -------------------
# FILE
# -------------------

LOG_FILE = "conversation_log.txt"
if "question_count" not in st.session_state:
    st.session_state.question_count = 0
    
# -------------------
# UI
# -------------------

st.title(" Lets Discover Your Requirement. This is only for Adhoc ;) ")
st.progress(min(st.session_state.question_count, 10) / 10)

st.write(
    f"Discovery Progress: "
    f"{min(st.session_state.question_count,10)}/10"
)
# display history

for msg in st.session_state.messages:

    if msg["role"] == "system":
        continue

    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# -------------------
# INPUT
# -------------------

prompt = st.chat_input(
    "Describe your business problem..."
)

if prompt:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt
        }
    )

    with st.chat_message("user"):
        st.write(prompt)

    response = client.chat.completions.create(
        model=MODEL,
        messages=st.session_state.messages[-20:],
        max_tokens=700
    )

    answer = response.choices[0].message.content
    content = response.choices[0].message.content
    
    if isinstance(content, str):
        answer = content
    elif isinstance(content, list):
        answer = " ".join(
            item.get("text", "")
            for item in content
            if isinstance(item, dict)
        )
    else:
        answer = str(content)
        
    st.session_state.question_count += 1

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    with st.chat_message("assistant"):
        st.write(answer)

    # save conversation

    with open(LOG_FILE, "a", encoding="utf-8") as f:

        f.write(
            f"\n\n[{datetime.now()}]\n"
        )

        f.write(
            f"USER: {prompt}\n"
        )

        f.write(
            f"BOT: {answer}\n"
        )

# -------------------
# EXPORT BRD
# -------------------
if st.session_state.question_count >= 10:
    if st.button("Generate BRD"):
        ...   
    if st.button("Generate BRD"):
    
        brd_prompt = """
    Using the entire conversation,
    create a BRD with:
    1 Is this first time data requirement
    2 Did you check any powerBI dashboad 
    3 Problem Statement
    4 Business Requirements
    5 Who need this data in senior management
    6 What is ETA
    7 did you work closely with any Data Science Team
    8 Has anyone delivered this data in past
    9 Do you need PII information
    10 Success Criteria
    """
    
        response = client.chat.completions.create(
            model=MODEL,
            messages=
            st.session_state.messages +
            [
                {
                    "role": "user",
                    "content": brd_prompt
                }
            ],
            max_tokens=700
        )
    
        brd = response.choices[0].message.content
    
        st.subheader("Generated BRD")
    
        st.write(brd)
        st.download_button(
            label=" Download BRD",
            data=brd,
            file_name="generated_brd.txt",
            mime="text/plain"
        )
