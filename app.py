import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def review_code(code, language):
    prompt = f"""You are an expert senior software engineer conducting a thorough code review.

Review the following {language} code and provide structured feedback in these exact sections:

## 🐛 Bugs & Errors
List any bugs, logical errors, or incorrect behavior. If none, say "No bugs found."

## 🔒 Security Issues  
List any security vulnerabilities (SQL injection, XSS, hardcoded secrets, etc). If none, say "No security issues found."

## ⚡ Performance Issues
List any performance problems or inefficiencies. If none, say "No performance issues found."

## 📝 Code Style & Best Practices
List style issues, naming conventions, missing docstrings, etc.

## ✅ Improved Code
Provide the improved version of the code with all issues fixed and comments explaining changes.

## 📊 Overall Score
Give a score out of 10 and a one-line summary.

Code to review:
```{language}
{code}
```"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2048,
    )
    return response.choices[0].message.content


st.set_page_config(
    page_title="AI Code Review Assistant",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 AI Code Review Assistant")
st.markdown("Paste your code below and get instant expert feedback powered by LLaMA 3.3 70B via Groq.")

col1, col2 = st.columns([1, 2])

with col1:
    language = st.selectbox(
        "Select Language",
        ["Python", "JavaScript", "Java", "C++", "TypeScript", "Go", "Rust", "SQL"]
    )

    code_input = st.text_area(
        "Paste your code here",
        height=400,
        placeholder="def calculate_total(items):\n    total = 0\n    for item in items:\n        total += item\n    return total"
    )

    review_button = st.button("🔍 Review Code", type="primary", use_container_width=True)

with col2:
    if review_button:
        if not code_input.strip():
            st.error("Please paste some code first!")
        else:
            with st.spinner("Reviewing your code..."):
                review = review_code(code_input, language)
            st.markdown(review)
    else:
        st.info("👈 Paste your code on the left and click Review Code to get started!")