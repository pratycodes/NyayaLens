from __future__ import annotations

import streamlit as st
from backend.app.core.schemas import RiskFlag, RuleResult


def render_risks(risks: list[RiskFlag], rules: list[RuleResult]) -> None:
    st.subheader("Risk Flags")
    if not risks:
        st.info("No blocking risk flags were produced by the deterministic rules.")
    for risk in risks:
        with st.container(border=True):
            st.markdown(f"**{risk.title}**")
            st.write(f"Severity: `{risk.severity}` | Confidence: `{risk.confidence}`")
            st.write(risk.explanation)
            st.write(f"Next step: {risk.suggested_next_step}")
            if risk.triggering_evidence:
                st.caption("Triggering evidence")
                for item in risk.triggering_evidence:
                    st.code(item)

    with st.expander("Rule Checks", expanded=False):
        for rule in rules:
            st.write(f"**{rule.title}** - {'passed' if rule.passed else 'flagged'}")
            st.caption(rule.explanation)
