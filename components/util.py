import streamlit as st


def links_toggle():
    with st.sidebar:
        st.write("Toggles")
        links = st.checkbox("Links to users? (will make dataframe ugly)", value=False)

    return links
