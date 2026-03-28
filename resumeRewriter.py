import streamlit as st
from openai import OpenAI
import time
import os

st.set_page_config(page_title="Resume Rewriter")

if 'assistant_id' not in st.session_state:
    st.session_state.assistant_id = None

st.title("Resume Rewriter")
st.markdown("---")

api_key = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=api_key)

if st.session_state.assistant_id is None:
    with st.spinner("Initializing AI assistant..."):
        try:
            vector_store = client.vector_stores.create(name="Resume help")
            st.session_state.vector_store_id = vector_store.id
            
            assistant = client.beta.assistants.create(
                name="Resume Rewriter Assistant",
                instructions="""You are an expert resume writer and career coach. Your task is to rewrite resumes to match job descriptions perfectly.
                
Key instructions:
1. Analyze the resume and job description carefully
2. Highlight relevant skills and experiences that match the job
3. Use professional language and active verbs
4. Format the resume clearly with sections
5. Include quantifiable achievements when possible
6. Ensure the final output is a complete, usable resume
7. Maintain the original resume's integrity while optimizing for the specific job

Output format:
- Clear section headers
- Bullet points for achievements
- Professional formatting""",
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

Please rewrite the resume to match the job description perfectly while following the customization preferences.
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
        instructions=f"Rewrite the resume for the job description. Use {tone_style} tone and make it {length_style} in length."
    )
    
    return thread.id, run.id

if st.button("Generate Refined Resume", type="primary", use_container_width=True):
    if not resume.strip():
        st.error("Please enter your resume")
    elif not jobDescription.strip():
        st.error("Please enter the job description")
    else:
        with st.spinner("AI is rewriting your resume..."):
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
                    st.success("Resume generated successfully!")
                    st.markdown("---")
                    st.subheader("Your Refined Resume")
                    
                    for message in messages.data:
                        if message.role == "assistant":
                            st.markdown(message.content[0].text.value)
                            break
                    
            except Exception as e:
                st.stop();