from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sql_ai_agent.pipeline import qa_pipeline  # noqa: E402

st.set_page_config(page_title="SQL AI Agent", layout="centered")

st.title("SQL AI Agent")
st.write("Ask a question about the books dataset (for example: 'What is the average price?').")

question = st.text_input("Question", "")

if "generated_sql" not in st.session_state:
    st.session_state["generated_sql"] = ""
if "last_question" not in st.session_state:
    st.session_state["last_question"] = ""
if "schema_context" not in st.session_state:
    st.session_state["schema_context"] = ""
if "sql_explanation" not in st.session_state:
    st.session_state["sql_explanation"] = ""
if "saved_queries" not in st.session_state:
    st.session_state["saved_queries"] = []

if question != st.session_state["last_question"]:
    st.session_state["generated_sql"] = ""
    st.session_state["last_question"] = question
    st.session_state["schema_context"] = ""
    st.session_state["sql_explanation"] = ""

with st.sidebar:
    st.header("Saved Queries")
    saved = st.session_state["saved_queries"]
    if saved:
        options = list(range(len(saved)))
        selected_idx = st.selectbox(
            "Select a saved query",
            options,
            index=0,
            format_func=lambda idx: f"{saved[idx]['question']}  ({saved[idx]['sql'][:60]}...)",
        )
        if st.button("Load selected"):
            st.session_state["last_question"] = saved[selected_idx]["question"]
            st.session_state["generated_sql"] = saved[selected_idx]["sql"]
            st.session_state["schema_context"] = saved[selected_idx].get("schema_context", "")
            st.session_state["sql_explanation"] = saved[selected_idx].get("explanation", "")
            st.rerun()
    else:
        st.caption("No saved queries yet.")

if st.button("Generate SQL"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            result = qa_pipeline.prepare_question(question)
            st.session_state["generated_sql"] = result["sql"]
            st.session_state["schema_context"] = result.get("schema_context", "")
            st.session_state["sql_explanation"] = ""
            for note in result.get("notes", []):
                st.info(note)
        except Exception as exc:
            st.error(str(exc))

if st.session_state["generated_sql"]:
    st.subheader("Generated SQL")
    st.code(st.session_state["generated_sql"], language="sql")

    col_explain, col_save = st.columns(2)
    with col_explain:
        if st.button("Explain SQL"):
            try:
                explanation = qa_pipeline.explain(
                    st.session_state["generated_sql"],
                    st.session_state.get("schema_context", ""),
                )
                st.session_state["sql_explanation"] = explanation
            except Exception as exc:
                st.error(str(exc))

    with col_save:
        if st.button("Save query"):
            if question.strip():
                saved = st.session_state["saved_queries"]
                saved.append(
                    {
                        "question": question.strip(),
                        "sql": st.session_state["generated_sql"],
                        "schema_context": st.session_state.get("schema_context", ""),
                        "explanation": st.session_state.get("sql_explanation", ""),
                    }
                )
                st.success("Saved.")
            else:
                st.warning("Enter a question before saving.")

    if st.session_state["sql_explanation"]:
        st.subheader("Explanation")
        st.write(st.session_state["sql_explanation"])

    if st.button("Run query"):
        try:
            df = qa_pipeline.execute_sql(st.session_state["generated_sql"])
            df = df.reset_index(drop=True)
            st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(str(exc))
