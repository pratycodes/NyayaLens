from __future__ import annotations

import streamlit as st
from backend.app.core.schemas import Citation, RetrievedSource


def render_sources(sources: list[RetrievedSource], citations: list[Citation]) -> None:
    st.subheader("Retrieved Sources")
    if not sources:
        st.warning("No local corpus source was retrieved.")
    for source in sources:
        citation = source.citation
        with st.container(border=True):
            st.markdown(f"**{citation.title or citation.source_file}**")
            st.caption(
                f"{citation.source_file} | domain={citation.domain} | jurisdiction={citation.jurisdiction} | score={source.score:.2f}"
            )
            st.write(citation.excerpt)

    with st.expander("Citation List", expanded=False):
        for citation in citations:
            st.write(f"- {citation.source_file}::{citation.chunk_id or 'chunk'}")
