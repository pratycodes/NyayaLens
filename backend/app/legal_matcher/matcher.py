from __future__ import annotations

from datetime import date

from backend.app.core.schemas import (
    Citation,
    DocumentAnalysis,
    IssueAnalysis,
    JurisdictionResult,
    PotentialProvisionMatch,
    UserContext,
)
from backend.app.law_packs.law_pack_loader import load_law_sections
from backend.app.law_packs.schemas import LawSection
from backend.app.legal_matcher.consistency_filters import (
    has_criminal_screening_facts,
    has_public_law_context,
    should_exclude_legal_area,
)
from backend.app.legal_matcher.element_checker import (
    clause_present,
    matched_facts_for_area,
    missing_facts_after_matching,
)
from backend.app.legal_matcher.provision_ranker import rank_sections
from backend.app.legal_ontology.issue_taxonomy import legal_areas_for_issue
from backend.app.legal_ontology.issue_to_law_map import tags_for_legal_area


def _parse_dispute_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _areas_for_context(issue: IssueAnalysis, document: DocumentAnalysis, context: UserContext, user_text: str) -> list[str]:
    areas = legal_areas_for_issue(issue.issue_type)
    if document.document_type == "freelance_service_agreement":
        if "contract_payment" not in areas:
            areas.append("contract_payment")
        if clause_present(document, "independent_contractor_clause") and "labour_classification" not in areas:
            areas.append("labour_classification")
        if (
            clause_present(document, "arbitration_clause")
            or clause_present(document, "jurisdiction_clause")
        ) and "contract_payment" not in areas:
            areas.append("contract_payment")
    if has_criminal_screening_facts(user_text) and "criminal_screening" not in areas:
        areas.append("criminal_screening")
    if has_public_law_context(context, user_text) and "constitution_public_law" not in areas:
        areas.append("constitution_public_law")
    return areas


def _candidate_sections(sections: list[LawSection], legal_area: str) -> list[LawSection]:
    tags = set(tags_for_legal_area(legal_area))
    return [
        section
        for section in sections
        if section.domain == legal_area or tags.intersection(section.issue_tags)
    ]


def _has_specific_relief_context(user_text: str, document: DocumentAnalysis) -> bool:
    haystack = " ".join(
        [
            user_text,
            " ".join(clause.raw_text for clause in document.extracted_clauses),
        ]
    ).lower()
    return any(
        term in haystack
        for term in {
            "injunction",
            "injunctive relief",
            "specific performance",
            "specific relief",
            "equitable relief",
            "remedy enforcement",
            "enforce the agreement",
            "court order",
        }
    )


def _implication_level(legal_area: str, matched_facts: list[str]) -> str:
    if not matched_facts:
        return "not_enough_facts"
    if legal_area == "criminal_screening":
        return "possible_criminal_allegation"
    if legal_area in {"contract_payment", "tenancy_deposit", "tenancy_repairs", "employment_contract", "restraint_review"}:
        return "possible_civil_breach"
    if legal_area in {"labour_wage", "employment", "labour_classification", "constitution_public_law", "grievance"}:
        return "possible_statutory_non_compliance"
    return "relevant_provision_found"


def _why_relevant(legal_area: str, section: LawSection) -> str:
    if legal_area == "contract_payment":
        return "Potentially relevant to payment, invoice, deduction, or dispute-process review; this is not a finding that any law was broken."
    if legal_area == "labour_classification":
        return "Potentially relevant to worker-classification review; the system does not assume employee or contractor status."
    if legal_area == "criminal_screening":
        return "Potentially relevant only because user text contains fraud, forgery, threat, blackmail, or similar allegation facts."
    if legal_area == "constitution_public_law":
        return "Potentially relevant only because a government/public authority or state-action style issue is present."
    if legal_area == "tenancy_deposit":
        return "Potentially relevant to security deposit and itemized deduction review."
    return f"Potentially relevant to {legal_area.replace('_', ' ')}."


def _top_sections_for_area(legal_area: str, ranked: list[LawSection]) -> list[LawSection]:
    if legal_area != "criminal_screening":
        return ranked[:2]
    selected: list[LawSection] = []
    seen_acts: set[str] = set()
    for section in ranked:
        if section.act_name in seen_acts:
            continue
        selected.append(section)
        seen_acts.add(section.act_name)
        if len(selected) == 2:
            break
    return selected


def match_potential_provisions(
    *,
    issue: IssueAnalysis,
    document: DocumentAnalysis,
    context: UserContext,
    jurisdiction: JurisdictionResult,
    user_text: str,
    sections: list[LawSection] | None = None,
) -> list[PotentialProvisionMatch]:
    all_sections = sections if sections is not None else load_law_sections()
    dispute_date = _parse_dispute_date(context.dispute_date)
    state = jurisdiction.state or context.state
    matches: list[PotentialProvisionMatch] = []
    for legal_area in _areas_for_context(issue, document, context, user_text):
        if should_exclude_legal_area(legal_area, document=document, context=context, user_text=user_text):
            continue
        ranked = rank_sections(
            _candidate_sections(all_sections, legal_area),
            legal_area=legal_area,
            state=state,
            dispute_date=dispute_date,
            remedy_context=_has_specific_relief_context(user_text, document),
        )
        for section in _top_sections_for_area(legal_area, ranked):
            matched = matched_facts_for_area(
                legal_area,
                document=document,
                context=context,
                user_text=user_text,
            )
            missing = missing_facts_after_matching(legal_area, matched)
            citation = Citation(
                source_file=section.source_file or section.act_id,
                title=f"{section.act_name} - {section.section_title}",
                domain=section.domain,
                jurisdiction=section.jurisdiction,
                excerpt=section.text[:600],
                corpus_mode=section.corpus_mode,
            )
            human_review = (
                legal_area in {"criminal_screening", "constitution_public_law"}
                or clause_present(document, "arbitration_clause")
                or clause_present(document, "jurisdiction_clause")
                or section.corpus_mode == "demo"
            )
            matches.append(
                PotentialProvisionMatch(
                    match_id=f"{legal_area}-{section.act_id}-{section.section_number}",
                    legal_area=legal_area,
                    act_name=section.act_name,
                    section_number=section.section_number,
                    section_title=section.section_title,
                    source_quote=section.text[:600],
                    why_relevant=_why_relevant(legal_area, section),
                    matched_facts=matched,
                    missing_facts=missing,
                    confidence="medium" if matched else "low",
                    implication_level=_implication_level(legal_area, matched),  # type: ignore[arg-type]
                    human_review_needed=human_review,
                    citations=[citation],
                    corpus_mode=section.corpus_mode,
                    effective_from=section.effective_from,
                    effective_to=section.effective_to,
                    version_date=section.version_date,
                    source_authority=section.source_authority,
                    source_url=section.source_url,
                )
            )
    return matches
