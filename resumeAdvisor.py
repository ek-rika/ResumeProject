import streamlit as st
from openai import OpenAI
import time
import os

st.set_page_config(page_title="Resume Helping")

if 'assistant_id' not in st.session_state:
    st.session_state.assistant_id = None

st.title("Resume Helping")
st.markdown("---")

api_key = os.environ["OPENAI_API_KEY"]

client = OpenAI(api_key=api_key)

if st.session_state.assistant_id is None:
    with st.spinner("Initializing AI assistant..."):
        try:
            vector_store = client.vector_stores.create(name="Resume help")
            st.session_state.vector_store_id = vector_store.id
            
            assistant = client.beta.assistants.create(
                name="Resume Assistant",
                instructions="""You are an expert resume coach. Your goal is to help users improve their resume WITHOUT rewriting it.

CRITICAL RULES (STRICT):
- DO NOT rewrite or generate improved resume sentences.
- DO NOT summarize the resume.
- DO NOT give general advice that could apply to any resume.
- EVERY piece of feedback MUST reference a specific role, project, or bullet point.

FAIL CONDITION:
If your feedback could be copy-pasted to another resume, it is INVALID. You must revise it to be more specific.

OUTPUT FORMAT (MANDATORY):

1. FOCUS AREA
Choose ONLY ONE section (e.g., Experience)

2. WHAT WORKS (max 2 bullets)
- Must reference specific roles

3. LINE-BY-LINE IMPROVEMENTS
For EACH issue:
- Quote or reference the EXACT bullet (or closely paraphrase it)
- State what is missing
- Provide 2–3 DISTINCT ways to improve it

Format:
- In [Role: X] → “[bullet content]”
  Issue: [specific missing element]

  Improve it by:
  1. Add [specific type of detail: number, tool, scale, outcome]
  2. Clarify [specific dimension: complexity, challenge, ownership]
  3. Show impact by including [specific measurable or observable result]

❗ Do NOT write example sentences. Only describe WHAT to add.

4. TO-DO LIST (ACTIONABLE ONLY)
Each bullet must start with a verb and be directly executable.

GOOD:
- Add the number of users impacted for your app project
- Specify which APIs you used in your backend project

BAD:
- Improve clarity
- Add more detail

5. QUESTIONS (2–3 ONLY)
- Must refer to specific roles/projects
- Must help uncover missing metrics or impact

ANTI-VAGUENESS RULES:
- You must include at least 3 references to specific roles or projects
- You must include at least 5 concrete actions in the To-Do list
- Avoid words like: "improve", "enhance", "better" unless followed by HOW

FINAL CHECK:
Before answering, ask yourself:
"Did I point to exact resume content and give multiple ways to improve it?"
If not, revise.
""",
                model="gpt-4o",
                tools=[{"type": "file_search"}],
            )
            
            assistant = client.beta.assistants.update(
                assistant_id=assistant.id,
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
            )
            
            st.session_state.assistant_id = assistant.id
            
        except Exception as e:
            st.stop()

# ----------------------------START-------------------------------- #
col1, col2 = st.columns(2)

with col1:
    st.subheader("Your Resume")
    resume = st.text_area(
        "Paste your current resume here:",
        height=300,
    )

with col2:
    st.subheader("Job Description")
    jobDescription = st.text_area(
        "Paste the job description here:",
        height=300,
    )

st.subheader("Customization Options")
col3, col4 = st.columns(2)
with col3:
    tone = st.selectbox("Tone", ["Professional", "Creative", "Technical", "Executive"])
with col4:
    length = st.selectbox("Length", ["Concise (1 page)", "Standard (2 pages)", "Detailed (3 pages)"])


def generate_resume(resume_text, job_text, tone_style, length_style):
    user_input = f"""
RESUME:
{resume_text}

JOB DESCRIPTION:
{job_text}

CUSTOMIZATION:
- Tone: {tone_style}
- Length: {length_style}
You are an expert resume coach. Your goal is to help users improve their resume WITHOUT rewriting it.

CRITICAL RULES (STRICT):
- DO NOT rewrite or generate improved resume sentences.
- DO NOT summarize the resume.
- DO NOT give general advice that could apply to any resume.
- EVERY piece of feedback MUST reference a specific role, project, or bullet point.

FAIL CONDITION:
If your feedback could be copy-pasted to another resume, it is INVALID. You must revise it to be more specific.

OUTPUT FORMAT (MANDATORY):

1. FOCUS AREA
Choose ONLY ONE section (e.g., Experience)

2. WHAT WORKS (max 2 bullets)
- Must reference specific roles

3. LINE-BY-LINE IMPROVEMENTS
For EACH issue:
- Quote or reference the EXACT bullet (or closely paraphrase it)
- State what is missing
- Provide 2–3 DISTINCT ways to improve it

Format:
- In [Role: X] → “[bullet content]”
  Issue: [specific missing element]

  Improve it by:
  1. Add [specific type of detail: number, tool, scale, outcome]
  2. Clarify [specific dimension: complexity, challenge, ownership]
  3. Show impact by including [specific measurable or observable result]

❗ Do NOT write example sentences. Only describe WHAT to add.

4. TO-DO LIST (ACTIONABLE ONLY)
Each bullet must start with a verb and be directly executable.

GOOD:
- Add the number of users impacted for your app project
- Specify which APIs you used in your backend project

BAD:
- Improve clarity
- Add more detail

5. QUESTIONS (2–3 ONLY)
- Must refer to specific roles/projects
- Must help uncover missing metrics or impact

ANTI-VAGUENESS RULES:
- You must include at least 3 references to specific roles or projects
- You must include at least 5 concrete actions in the To-Do list
- Avoid words like: "improve", "enhance", "better" unless followed by HOW

FINAL CHECK:
Before answering, ask yourself:
"Did I point to exact resume content and give multiple ways to improve it?"
If not, revise.
"""
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": user_input,
            }
        ]
    )
    
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=st.session_state.assistant_id,
        instructions=f"Provide feedback. Use {tone_style} tone and make it {length_style} in length."
    )
    
    return thread.id, run.id

if st.button("Get feedback", type="primary", use_container_width=True):
    if not resume.strip():
        st.error("Please enter your resume")
    elif not jobDescription.strip():
        st.error("Please enter the job description")
    else:
        with st.spinner("AI is analyzing the resume..."):
            try:
                thread_id, run_id = generate_resume(resume, jobDescription, tone, length)
                
                while True:
                    time.sleep(1)
                    run = client.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=run_id
                    )
                    if run.status in ['completed', 'failed', 'cancelled']:
                        break
                
                if run.status == 'completed':
                    messages = client.beta.threads.messages.list(
                        thread_id=thread_id
                    )
                    st.success("Feedback generated successfully!")
                    st.markdown("---")
                    st.subheader("Your feedback")
                    
                    for message in messages.data:
                        if message.role == "assistant":
                            st.markdown(message.content[0].text.value)
                            break
                    
            except Exception as e:
                st.stop();
