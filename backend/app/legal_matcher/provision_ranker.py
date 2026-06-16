from __future__ import annotations

from datetime import date

from backend.app.law_packs.schemas import LawSection

CRIMINAL_CURRENT_DATE = date(2024, 7, 1)


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


def rank_sections(
    sections: list[LawSection],
    *,
    legal_area: str,
    state: str | None,
    dispute_date: date | None,
) -> list[LawSection]:
    effective = [section for section in sections if _is_effective(section, dispute_date)]

    def score(section: LawSection) -> tuple[int, str]:
        value = 0
        if section.state and state and section.state.lower() == state.lower():
            value += 20
        if section.corpus_mode == "official":
            value += 10
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
