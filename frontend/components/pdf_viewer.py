from __future__ import annotations

import streamlit as st
from backend.app.explainability.report_view_model import DocumentCitation, ReportViewModel


def _citation_by_id(view_model: ReportViewModel, citation_id: str | None) -> DocumentCitation | None:
    if not citation_id:
        return None
    return next(
        (
            citation
            for citation in view_model.uploaded_document_citations
            if citation.citation_id == citation_id
        ),
        None,
    )


def find_quote_rects(document_bytes: bytes, page_number: int, quote: str) -> list[object]:
    import fitz  # type: ignore

    with fitz.open(stream=document_bytes, filetype="pdf") as pdf:
        if not pdf:
            return []
        page_index = max(0, min(page_number - 1, len(pdf) - 1))
        page = pdf[page_index]
        return list(page.search_for(quote[:120]))


def render_pdf_page_to_png(
    document_bytes: bytes,
    page_number: int,
    quote: str | None = None,
) -> tuple[bytes, bool]:
    import fitz  # type: ignore

    with fitz.open(stream=document_bytes, filetype="pdf") as pdf:
        if not pdf:
            raise ValueError("PDF has no readable pages.")
        page_index = max(0, min(page_number - 1, len(pdf) - 1))
        page = pdf[page_index]
        highlighted = False
        if quote:
            for rect in page.search_for(quote[:120]):
                highlighted = True
                page.draw_rect(
                    rect,
                    color=(1, 0.8, 0),
                    fill=(1, 1, 0),
                    fill_opacity=0.25,
                    overlay=True,
                )
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
        return pixmap.tobytes("png"), highlighted


def _render_pdf_page(document_bytes: bytes, page_number: int, quote: str | None) -> bool:
    try:
        png_bytes, highlighted = render_pdf_page_to_png(document_bytes, page_number, quote)
        st.image(png_bytes, use_container_width=True)
        if quote and not highlighted:
            st.caption("Exact highlight unavailable; showing cited page and extracted quote.")
        return True
    except ImportError:
        st.warning("PyMuPDF is unavailable, so the PDF page image cannot be rendered.")
        return False
    except Exception as exc:
        st.warning(f"Could not render PDF page locally: {exc}")
        return False


def _render_text_page(page_texts: list[tuple[int, str]], page_number: int, quote: str | None) -> None:
    page_map = dict(page_texts)
    text = page_map.get(page_number) or next(iter(page_map.values()), "")
    st.text_area("Document text page", text, height=520)
    if quote:
        st.caption("Selected quote")
        st.code(quote)


def render_document_viewer(
    view_model: ReportViewModel,
    *,
    document_bytes: bytes | None,
    content_type: str | None,
    page_texts: list[tuple[int, str]],
) -> None:
    selected_citation = _citation_by_id(
        view_model,
        st.session_state.get("nl_selected_document_citation_id"),
    )
    selected_page = selected_citation.page if selected_citation else st.session_state.get("nl_selected_page", 1)
    page_numbers = [page for page, _ in page_texts] or [1]
    selected_page = selected_page if selected_page in page_numbers else page_numbers[0]

    left, right = st.columns([2, 1])
    with right:
        st.subheader("Important Sections")
        preferred = [
            "Parties",
            "Payment",
            "Invoice",
            "Compensation",
            "TDS / deduction",
            "Relationship",
            "Termination",
            "Arbitration",
            "Jurisdiction",
            "Deposit",
            "Repairs",
            "Notice",
        ]
        existing = sorted({section.category for section in view_model.important_sections})
        categories = ["All", *[item for item in preferred if item in existing], *[item for item in existing if item not in preferred]]
        selected_category = st.selectbox("Filter", categories)
        sections = [
            section
            for section in view_model.important_sections
            if selected_category == "All" or section.category == selected_category
        ]
        for section in sections:
            with st.container(border=True):
                st.markdown(f"**{section.title}**")
                st.caption(f"{section.category} | Document p.{section.page or 1} | {section.confidence}")
                st.write(section.why_it_matters)
                if st.button("View section", key=f"section-{section.section_id}"):
                    if section.citation_id:
                        st.session_state["nl_selected_document_citation_id"] = section.citation_id
                    st.session_state["nl_selected_page"] = section.page or 1
                    st.session_state["nl_document_view_message"] = (
                        f"Selected citation: Document p.{section.page or 1}"
                    )
                    st.rerun()

        if selected_citation:
            st.subheader("Selected Citation")
            st.caption(f"Document p.{selected_citation.page or 1}")
            st.code(selected_citation.quote)

    with left:
        st.subheader("Document Page")
        if message := st.session_state.pop("nl_document_view_message", None):
            st.info(message)
        page = st.selectbox(
            "Page",
            page_numbers,
            index=page_numbers.index(selected_page),
            key="nl_document_page_selector",
        )
        col_prev, col_next = st.columns(2)
        if col_prev.button("Previous page", disabled=page_numbers.index(page) == 0):
            st.session_state.pop("nl_selected_document_citation_id", None)
            st.session_state["nl_selected_page"] = page_numbers[max(0, page_numbers.index(page) - 1)]
            st.rerun()
        if col_next.button("Next page", disabled=page_numbers.index(page) == len(page_numbers) - 1):
            st.session_state.pop("nl_selected_document_citation_id", None)
            st.session_state["nl_selected_page"] = page_numbers[min(len(page_numbers) - 1, page_numbers.index(page) + 1)]
            st.rerun()

        quote = selected_citation.quote if selected_citation and selected_citation.page == page else None
        is_pdf = bool(document_bytes) and (
            (content_type or "").lower() == "application/pdf"
            or st.session_state.get("nl_document_filename", "").lower().endswith(".pdf")
        )
        rendered = _render_pdf_page(document_bytes, page, quote) if is_pdf and document_bytes else False
        if not rendered:
            _render_text_page(page_texts, page, quote)
