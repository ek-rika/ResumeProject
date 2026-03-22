import streamlit as st

pg = st.navigation(
    [
        st.Page("resumeTesting.py", title = "rewrite page"),
        st.Page("resumeHelp.py", title = "resume help page"),
    ]
)

pg.run()