import streamlit as st
from openai import OpenAI
import time
import os

st.set_page_config(page_title="Resume Helping")

if 'assistant_id' not in st.session_state:
    st.session_state.assistant_id = None

st.title("Resume Helping")
st.markdown("---")

api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)

if st.session_state.assistant_id is None:
    with st.spinner("Initializing AI assistant..."):
        try:
            vector_store = client.vector_stores.create(name="Resume help")
            st.session_state.vector_store_id = vector_store.id
            
            assistant = client.beta.assistants.create(
                name="Resume Assistant",
                instructions="""You are an expert resume assistant. Your task is to help users improve their resumes through thoughtful questions and feedback.

Key instructions:
1. DO NOT rewrite the resume. Instead, provide suggestions that help users improve it themselves.
2. Ask 2-3 thought-provoking questions at a time
3. Focus on one area at a time
4. Encourage users to add numbers and specific achievements
5. Provide constructive feedback on strengths and areas for improvement
6. Help users identify relevant keywords for their industry

Example questions:
- "What specific results did you achieve in that role?"
- "How can you quantify that achievement?"
- "What keywords from the job description match your experience?"
- "Can you provide more details about your leadership experience?""",
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

As a resume assistant, please help the user improve this resume by:
1. Identifying 2-3 strengths
2. Pointing out 2-3 areas for improvement
3. Asking 3 specific, thought-provoking questions that will help the user think critically about their experience
4. Suggesting one concrete action the user can take to improve my resume

DO NOT rewrite the resume for the user. Instead, guide the user to improve it myself.
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
