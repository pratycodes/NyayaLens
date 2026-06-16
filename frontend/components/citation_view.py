from __future__ import annotations

import streamlit as st
from backend.app.config import get_settings
from backend.app.core.schemas import Citation, RetrievedSource


def _dedupe_sources(sources: list[RetrievedSource]) -> list[RetrievedSource]:
    seen: set[tuple[str | None, str, str]] = set()
    deduped: list[RetrievedSource] = []
    for source in sources:
        citation = source.citation
        key = (
            citation.title,
            citation.source_file,
            citation.excerpt[:120],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(source)
    return deduped


def render_sources(sources: list[RetrievedSource], citations: list[Citation]) -> None:
    st.subheader("Retrieved Sources")
    if not sources:
        st.warning("No local corpus source was retrieved.")
    if get_settings().embedding_backend.lower() == "hash":
        st.info(
            "Offline demo retrieval mode is active. Results use lightweight hashing retrieval for reproducibility."
        )
    display_sources = _dedupe_sources(sources)
    for source in display_sources:
        citation = source.citation
        with st.container(border=True):
            st.markdown(f"**{citation.title or citation.source_file}**")
            st.caption(f"{citation.source_file} | domain={citation.domain} | jurisdiction={citation.jurisdiction}")
            st.write(citation.excerpt)

    with st.expander("Debug retrieval metadata", expanded=False):
        for source in display_sources:
            citation = source.citation
            st.write(
                f"- `{citation.source_file}` `{citation.chunk_id or 'chunk'}` "
                f"domain={citation.domain} jurisdiction={citation.jurisdiction} score={source.score:.4f}"
            )

    with st.expander("Citation List", expanded=False):
        for citation in citations:
            st.write(f"- {citation.source_file}::{citation.chunk_id or 'chunk'}")
