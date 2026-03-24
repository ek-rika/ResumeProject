import streamlit as st

st.set_page_config(
    page_title="Resume Assistant",
    page_icon="📄",
    layout="wide"
)

pg = st.navigation(
    [
        st.Page("resumeTesting.py", title="Rewrite Resume"),
        st.Page("resumeHelp.py", title="Resume Help"),
    ]
)  

pg.run()