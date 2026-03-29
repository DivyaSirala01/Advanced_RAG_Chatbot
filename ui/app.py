import streamlit as st
import requests

st.title("RAG Chatbot")

# Role selector (from Step 2)
role = st.selectbox("Select Domain", ["RAG", "Agent"])

# Use form for controlled submission
with st.form("chat_form"):
    query = st.text_input("Ask something:")
    submitted = st.form_submit_button("Submit")

if submitted and query:
    response = requests.post(
        "http://localhost:8000/chat",
        json={
            "query": query,
            "role": role
        }
    )
    
    st.write(response.json()["answer"])