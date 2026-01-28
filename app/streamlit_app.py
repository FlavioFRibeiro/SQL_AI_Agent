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
    delete_query,
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

st.markdown(
    """
    <style>
    .stButton > button {
        border-radius: 6px;
        padding: 0.35rem 0.9rem;
    }
    .btn-run button {
        background-color: #dcfce7 !important;
        border: 1px solid #86efac !important;
        color: #0f172a !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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


def delete_selected_query() -> None:
    query_id = st.session_state.get("selected_query_id")
    if query_id is None:
        return
    deleted = delete_query(settings.saved_queries_db, int(query_id))
    st.session_state["delete_status"] = "deleted" if deleted else "not_found"
    st.rerun()

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
if "show_save_details" not in st.session_state:
    st.session_state["show_save_details"] = False
if "last_sql" not in st.session_state:
    st.session_state["last_sql"] = ""
if "show_sql" not in st.session_state:
    st.session_state["show_sql"] = False
if "show_explanation" not in st.session_state:
    st.session_state["show_explanation"] = False
if "delete_status" not in st.session_state:
    st.session_state["delete_status"] = ""
if "result_df" not in st.session_state:
    st.session_state["result_df"] = None
if "has_results" not in st.session_state:
    st.session_state["has_results"] = False

if question != st.session_state["last_question"]:
    st.session_state["generated_sql"] = ""
    st.session_state["last_question"] = question
    st.session_state["schema_context"] = ""
    st.session_state["sql_explanation"] = ""
    st.session_state["show_save_details"] = False
    st.session_state["last_sql"] = ""
    st.session_state["show_sql"] = False
    st.session_state["show_explanation"] = False
    st.session_state["result_df"] = None
    st.session_state["has_results"] = False
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
                key="selected_query_id",
                format_func=lambda query_id: next(
                    (f"{item.name}  ({item.created_at[:10]})" for item in saved if item.id == query_id),
                    str(query_id),
                ),
            )
            col_load, col_delete = st.columns(2)
            with col_load:
                st.button("Load selected", on_click=load_selected_query, args=(selected_id,))
            with col_delete:
                st.button("Delete selected", on_click=delete_selected_query)
            if st.session_state["delete_status"] == "deleted":
                st.success("Deleted.")
                st.session_state["delete_status"] = ""
            elif st.session_state["delete_status"] == "not_found":
                st.warning("Query not found.")
                st.session_state["delete_status"] = ""
            st.caption(f"{len(saved)} saved queries")
        else:
            st.caption("No saved queries yet.")
    except Exception as exc:
        st.error(f"Failed to load saved queries: {exc}")

with st.container():
    st.markdown('<div class="btn-run">', unsafe_allow_html=True)
    run_clicked = st.button("Run query")
    st.markdown("</div>", unsafe_allow_html=True)

if run_clicked:
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            result = qa_pipeline.prepare_question(question)
            st.session_state["generated_sql"] = result["sql"]
            st.session_state["schema_context"] = result.get("schema_context", "")
            st.session_state["sql_explanation"] = ""
            st.session_state["show_save_details"] = False
            st.session_state["show_sql"] = False
            for note in result.get("notes", []):
                st.info(note)

            df = qa_pipeline.execute_sql(st.session_state["generated_sql"])
            df = df.reset_index(drop=True)
            st.session_state["result_df"] = df
            st.session_state["has_results"] = True
        except Exception as exc:
            st.session_state["has_results"] = False
            st.error(str(exc))

if st.session_state["has_results"] and st.session_state["result_df"] is not None:
    st.dataframe(st.session_state["result_df"], use_container_width=True, hide_index=True)
    st.divider()

    col_save, col_explain, col_sql = st.columns(3)
    with col_save:
        if st.button("Save query"):
            st.session_state["show_save_details"] = True
    with col_explain:
        st.session_state["show_explanation"] = st.toggle(
            "Explain SQL",
            value=st.session_state["show_explanation"],
        )
    with col_sql:
        st.session_state["show_sql"] = st.toggle(
            "See SQL query",
            value=st.session_state["show_sql"])

    with st.expander("Generated SQL", expanded=st.session_state["show_sql"]):
        st.code(st.session_state["generated_sql"], language="sql")

    if st.session_state["show_explanation"] and not st.session_state["sql_explanation"]:
        try:
            explanation = qa_pipeline.explain(
                st.session_state["generated_sql"],
                st.session_state.get("schema_context", ""),
            )
            st.session_state["sql_explanation"] = explanation
        except Exception as exc:
            st.error(str(exc))
            st.session_state["show_explanation"] = False

    with st.expander("Explanation", expanded=st.session_state["show_explanation"]):
        if st.session_state["sql_explanation"]:
            st.write(st.session_state["sql_explanation"])
        else:
            st.caption("Toggle 'Explain SQL' to generate a short explanation.")

    if st.session_state["show_save_details"]:
        st.subheader("Save details")
        st.text_input("Name", key="save_name")
        st.text_input("Tag (optional)", key="save_tag")
        st.text_area("Notes (optional)", key="save_notes")

        col_confirm, col_cancel = st.columns(2)
        with col_confirm:
            if st.button("Confirm save"):
                if not question.strip():
                    st.warning("Enter a question before saving.")
                elif not st.session_state["generated_sql"]:
                    st.warning("Run the query before saving.")
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
                        st.session_state["show_save_details"] = False
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))
        with col_cancel:
            if st.button("Cancel"):
                st.session_state["show_save_details"] = False
