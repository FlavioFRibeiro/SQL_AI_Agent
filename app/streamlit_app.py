from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sql_ai_agent.config import load_settings  # noqa: E402
from sql_ai_agent.pipeline import qa_pipeline  # noqa: E402
from sql_ai_agent.storage.saved_queries import (  # noqa: E402
    get_query,
    init_db,
    list_queries,
    save_query,
)

st.set_page_config(page_title="SQL AI Agent", layout="centered")

settings = load_settings()
try:
    init_db(settings.saved_queries_db)
except Exception as exc:
    st.error(f"Failed to initialize saved queries database: {exc}")


def load_selected_query(query_id: int) -> None:
    selected = get_query(settings.saved_queries_db, query_id)
    if not selected:
        return
    st.session_state["question"] = selected.question
    st.session_state["last_question"] = selected.question
    st.session_state["generated_sql"] = selected.sql
    try:
        st.session_state["schema_context"] = qa_pipeline.get_schema_context()
    except Exception:
        st.session_state["schema_context"] = ""
    st.session_state["sql_explanation"] = ""
    st.session_state["save_name"] = selected.name
    st.session_state["save_tag"] = selected.tag or ""
    st.session_state["save_notes"] = selected.notes or ""

st.title("SQL AI Agent")
st.write("Ask a question about the books dataset (for example: 'What is the average price?').")

question = st.text_input("Question", "", key="question")

if "generated_sql" not in st.session_state:
    st.session_state["generated_sql"] = ""
if "last_question" not in st.session_state:
    st.session_state["last_question"] = ""
if "schema_context" not in st.session_state:
    st.session_state["schema_context"] = ""
if "sql_explanation" not in st.session_state:
    st.session_state["sql_explanation"] = ""
if "save_name" not in st.session_state:
    st.session_state["save_name"] = ""
if "save_tag" not in st.session_state:
    st.session_state["save_tag"] = ""
if "save_notes" not in st.session_state:
    st.session_state["save_notes"] = ""

if question != st.session_state["last_question"]:
    st.session_state["generated_sql"] = ""
    st.session_state["last_question"] = question
    st.session_state["schema_context"] = ""
    st.session_state["sql_explanation"] = ""
    if question.strip():
        st.session_state["save_name"] = question.strip()[:80]

with st.sidebar:
    st.header("Saved Queries")
    try:
        search = st.text_input("Search", "")
        saved = list_queries(settings.saved_queries_db, search=search.strip() or None)
        if saved:
            options = [item.id for item in saved]
            selected_id = st.selectbox(
                "Select a saved query",
                options,
                index=0,
                format_func=lambda query_id: next(
                    (f"{item.name}  ({item.created_at[:10]})" for item in saved if item.id == query_id),
                    str(query_id),
                ),
            )
            st.button("Load selected", on_click=load_selected_query, args=(selected_id,))
            st.caption(f"{len(saved)} saved queries")
        else:
            st.caption("No saved queries yet.")
    except Exception as exc:
        st.error(f"Failed to load saved queries: {exc}")

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

    st.subheader("Save details")
    st.text_input("Name", key="save_name")
    st.text_input("Tag (optional)", key="save_tag")
    st.text_area("Notes (optional)", key="save_notes")

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
            if not question.strip():
                st.warning("Enter a question before saving.")
            elif not st.session_state["generated_sql"]:
                st.warning("Generate SQL before saving.")
            elif not st.session_state["save_name"].strip():
                st.warning("Please provide a name for this query.")
            else:
                try:
                    save_query(
                        settings.saved_queries_db,
                        name=st.session_state["save_name"].strip(),
                        question=question.strip(),
                        sql=st.session_state["generated_sql"],
                        tag=st.session_state["save_tag"].strip() or None,
                        notes=st.session_state["save_notes"].strip() or None,
                    )
                    st.success("Saved.")
                except Exception as exc:
                    st.error(str(exc))

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
