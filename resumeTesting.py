import streamlit as st
from openai import OpenAI, AssistantEventHandler

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


client = OpenAI()

vector_store = client.vector_stores.create(name="Resume help")

assistant = client.beta.assistants.create(
    name="Financial Analyst Assistant",
    instructions="You are a research assistant that rewrite users resumes for job applications, "
                 "make sure to allign the users resume with the job description provided," \
                 "Make sure your output is a USABLE resume",
    model="gpt-4o",
    tools=[{"type": "file_search"}],  # Use 'file_search' tool type
)

assistant = client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)



# ------------------------- START -------------------------------


st.title("This is a resume rewrite page")


resume = st.text_area(
    "please enter your resume",
)

jobDescription = st.text_area(
    "please enter your job desctiption here",
)

user_input = resume + jobDescription


# st.button("generate your refined resume")

if st.button("generate your refined resume"):
    if user_input:
        st.session_state.chat_history.append(f"user > {user_input}")
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": user_input,
                }
            ]
        )

        class EventHandler(AssistantEventHandler):
            def on_text_created(self, text) -> None:
                st.session_state.chat_history.append(f"assistant > {text}")

            def on_tool_call_created(self, tool_call):
                pass  # No file search tool used here

            def on_message_done(self, message) -> None:
                # print a citation to the file searched (not applicable)
                st.text(message.content[0].text.value)  # Only display response

        # Then, we use the stream SDK helper
        # with the EventHandler class to create the Run
        # and stream the response.
        with client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant.id,  # Assuming the assistant already exists
            instructions="You are a research assistant that rewrite users resumes for job applications, "
                 "make sure to allign the users resume with the job description provided," \
                 "Make sure your output is a USABLE resume",
            event_handler=EventHandler(),
        ) as stream:
            stream.until_done()