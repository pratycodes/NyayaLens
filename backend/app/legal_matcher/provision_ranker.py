from __future__ import annotations

from datetime import date

from backend.app.law_packs.schemas import LawSection

CRIMINAL_CURRENT_DATE = date(2024, 7, 1)
LOW_QUALITY_SECTION_TERMS = (
    "arrangement of sections",
    "table of contents",
    "subs. by act",
    "subs. by s.",
    "substituted by act",
    "ins. by act",
    "ins. by s.",
    "inserted by act",
    "omitted",
    "repealed",
    "schedule only",
    "footnote",
    "see ss.",
    "infra",
    "supra",
    "w.e.f.",
    "ibid",
)
CONTRACT_RELEVANT_SECTION_NUMBERS = {"37", "39", "55", "70", "73", "74"}
ARBITRATION_RELEVANT_SECTION_NUMBERS = {"7", "8", "21"}
CONTRACT_RELEVANCE_TERMS = (
    "breach",
    "compensation",
    "loss or damage",
    "performance",
    "payment",
    "consideration",
    "obligation",
    "arbitration agreement",
    "limitation",
)


def _parse_date(value: str | None) -> date | None:
    if not value or value == "unknown":
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _is_effective(section: LawSection, dispute_date: date | None) -> bool:
    if dispute_date is None:
        return True
    start = _parse_date(section.effective_from)
    end = _parse_date(section.effective_to)
    if start and dispute_date < start:
        return False
    return not (end and dispute_date > end)


def _looks_low_quality(section: LawSection) -> bool:
    title = section.section_title.strip().lower()
    if title.startswith("see ") or title.endswith(" and"):
        return True
    haystack = f"{section.section_title}\n{section.text[:1200]}".lower()
    return any(term in haystack for term in LOW_QUALITY_SECTION_TERMS)


def rank_sections(
    sections: list[LawSection],
    *,
    legal_area: str,
    state: str | None,
    dispute_date: date | None,
    remedy_context: bool = False,
) -> list[LawSection]:
    effective = [section for section in sections if _is_effective(section, dispute_date)]
    precise_section_exists = {
        section.act_id: any(
            candidate.act_id == section.act_id
            and candidate.section_number.lower() not in {"full_act", "unknown"}
            for candidate in effective
        )
        for section in effective
    }

    def score(section: LawSection) -> tuple[int, str]:
        value = 0
        act_name = section.act_name.lower()
        if section.state and state and section.state.lower() == state.lower():
            value += 20
        if section.corpus_mode == "official":
            value += 10
        if _looks_low_quality(section):
            value -= 200
        if (
            section.section_number.lower() == "full_act"
            and precise_section_exists.get(section.act_id)
        ):
            value -= 120
        if legal_area in {"contract_payment", "employment_contract"}:
            if "indian contract act" in act_name:
                value += 90
                if section.section_number in CONTRACT_RELEVANT_SECTION_NUMBERS:
                    value += 120
            elif "arbitration and conciliation" in act_name:
                value += 45
                if section.section_number in ARBITRATION_RELEVANT_SECTION_NUMBERS:
                    value += 70
            elif "limitation act" in act_name:
                value += 40
            elif "specific relief act" in act_name:
                value += 170 if remedy_context else -90
            relevant_text = f"{section.section_title} {section.text[:800]}".lower()
            if any(term in relevant_text for term in CONTRACT_RELEVANCE_TERMS):
                value += 25
        if (
            legal_area == "constitution_public_law"
            and section.act_name == "Constitution of India"
        ):
            value += 60
        if legal_area == "criminal_screening":
            if dispute_date is None or dispute_date >= CRIMINAL_CURRENT_DATE:
                if section.act_name == "Bharatiya Nyaya Sanhita, 2023":
                    value += 70
                elif section.act_name == "Bharatiya Nagarik Suraksha Sanhita, 2023":
                    value += 50
                elif section.act_name == "Bharatiya Sakshya Adhiniyam, 2023":
                    value += 40
                if "Indian Penal Code" in section.act_name:
                    value -= 50
            elif "Indian Penal Code" in section.act_name:
                value += 50
        return value, section.act_name

    return sorted(effective, key=score, reverse=True)
