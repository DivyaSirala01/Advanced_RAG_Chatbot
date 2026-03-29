import streamlit as st
import requests

st.set_page_config(page_title="RAG Chatbot", layout="wide")

st.title("RAG Chatbot")

if "last_answer" not in st.session_state:
    st.session_state.last_answer = None
if "last_evaluation" not in st.session_state:
    st.session_state.last_evaluation = None
if "last_error" not in st.session_state:
    st.session_state.last_error = None


def _overall_score(evaluation: dict) -> float | None:
    """Average of comparable 1–10 signals plus precision on the same scale."""
    if not evaluation:
        return None
    faith = evaluation.get("faithfulness") or {}
    recall = evaluation.get("context_recall") or {}
    parts = [
        float(faith.get("score", 0)),
        float(evaluation.get("relevance", 0)),
        float(evaluation.get("correctness", 0)),
        float(evaluation.get("completeness", 0)),
        float(recall.get("score", 0)),
        float(evaluation.get("context_precision", 0)) * 10.0,
    ]
    if evaluation.get("helpfulness") is not None:
        parts.insert(-2, float(evaluation["helpfulness"]))
    if not any(parts):
        return None
    return sum(parts) / len(parts)


role = st.selectbox("Select Domain", ["RAG", "Agent"])

with st.form("chat_form"):
    query = st.text_input("Ask something:")
    submitted = st.form_submit_button("Submit")

if submitted and query:
    st.session_state.last_error = None
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json={"query": query, "role": role},
            timeout=120,
        )
        response.raise_for_status()
        payload = response.json()
        st.session_state.last_answer = payload.get("answer")
        st.session_state.last_evaluation = payload.get("evaluation")
    except requests.RequestException as e:
        st.session_state.last_answer = None
        st.session_state.last_evaluation = None
        st.session_state.last_error = str(e)

# Sidebar after fetch so the same run shows fresh scores (Streamlit runs top to bottom).
with st.sidebar:
    st.header("Evaluation")
    if st.session_state.last_error:
        st.error(st.session_state.last_error)
    elif st.session_state.last_evaluation is None and st.session_state.last_answer is not None:
        st.info("No scores for this reply (served from cache).")
    elif st.session_state.last_evaluation is not None:
        ev = st.session_state.last_evaluation
        overall = _overall_score(ev)
        if overall is not None:
            st.metric("Overall (avg / 10)", f"{overall:.1f}")

        faith = ev.get("faithfulness") or {}
        st.subheader("Grounding")
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Faithfulness", f"{faith.get('score', '—')}/10")
        with c2:
            grounded = faith.get("grounded")
            st.metric("Grounded", "Yes" if grounded else "No" if grounded is False else "—")

        st.subheader("Answer quality")
        j1, j2 = st.columns(2)
        with j1:
            st.metric("Relevance", f"{ev.get('relevance', '—')}/10")
        with j2:
            st.metric("Correctness", f"{ev.get('correctness', '—')}/10")
        j3, j4 = st.columns(2)
        with j3:
            st.metric("Completeness", f"{ev.get('completeness', '—')}/10")
        with j4:
            st.metric("Helpfulness", f"{ev.get('helpfulness', '—')}/10")

        st.subheader("Retrieval")
        prec = ev.get("context_precision")
        if prec is not None:
            st.metric("Context precision", f"{prec * 100:.0f}%")
        recall = ev.get("context_recall") or {}
        if recall.get("score") is not None:
            st.metric("Context coverage", f"{recall['score']}/10")

        feedback = ev.get("judge_feedback")
        reasoning = faith.get("reasoning")
        recall_reason = recall.get("reasoning")
        if feedback or reasoning or recall_reason:
            with st.expander("Details"):
                if feedback:
                    st.markdown("**Judge**")
                    st.caption(feedback)
                if reasoning:
                    st.markdown("**Faithfulness**")
                    st.caption(reasoning)
                if recall_reason:
                    st.markdown("**Coverage**")
                    st.caption(recall_reason)
    else:
        st.caption("Submit a question to see evaluation scores here.")

if st.session_state.last_answer is not None:
    st.subheader("Answer")
    st.write(st.session_state.last_answer)
