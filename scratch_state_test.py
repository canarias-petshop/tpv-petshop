import streamlit as st

if "backup" not in st.session_state:
    st.session_state.backup = {}

# Backup all widget keys at the start (keys not in backup)
for k, v in st.session_state.items():
    if k != "backup" and not k.startswith("FormSubmitter"):
        st.session_state.backup[k] = v

page = st.radio("Page", ["Page 1", "Page 2"], key="page_selector")

# Restore state for ALL widgets from backup back into session_state
for k, v in st.session_state.backup.items():
    if k not in st.session_state:
        st.session_state[k] = v

if page == "Page 1":
    st.text_input("Input 1", key="input_1")
    st.number_input("Num 1", key="num_1")
else:
    st.text_input("Input 2", key="input_2")
    st.number_input("Num 2", key="num_2")

st.write("Session State:", st.session_state)
st.write("Backup:", st.session_state.backup)
