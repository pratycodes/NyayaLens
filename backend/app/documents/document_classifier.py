from __future__ import annotations

from backend.app.core.schemas import Confidence

FREELANCE_SERVICE_INDICATORS = [
    "freelancing agreement",
    "freelancer",
    "service agreement",
    "scope of work",
    "consideration",
    "invoice",
    "payment shall be made",
    "pro-rata compensation",
    "project manager",
    "independent contractors",
    "independent contractor",
    "tds",
    "contract renewal",
]

FREELANCE_SUPPORTING_INDICATORS = [
    "termination notice",
    "arbitration",
    "jurisdiction",
    "consulting",
    "services",
    "client",
]

STRONG_TENANCY_INDICATORS = [
    "tenant",
    "landlord",
    "rent agreement",
    "lease agreement",
    "security deposit",
    "monthly rent",
    "eviction",
    "premises let out",
    "lessor",
    "lessee",
    "rent increase",
]


def classify_document(text: str) -> tuple[str, str, Confidence]:
    lowered = text.lower()
    freelance_hits = sum(indicator in lowered for indicator in FREELANCE_SERVICE_INDICATORS)
    freelance_support_hits = sum(indicator in lowered for indicator in FREELANCE_SUPPORTING_INDICATORS)
    if freelance_hits >= 2 or (freelance_hits >= 1 and freelance_support_hits >= 2):
        return (
            "freelance_service_agreement",
            "contract_payment",
            "high" if freelance_hits >= 3 else "medium",
        )

    employment_hits = sum(
        word in lowered
        for word in [
            "employee",
            "employer",
            "salary",
            "notice period",
            "relieving",
            "full and final",
            "non-compete",
            "training bond",
        ]
    )
    tenancy_hits = sum(
        word in lowered
        for word in [
            *STRONG_TENANCY_INDICATORS,
            "maintenance charges",
        ]
    )
    if employment_hits > tenancy_hits and employment_hits >= 2:
        return "employment_document", "employment", "high" if employment_hits >= 4 else "medium"
    if tenancy_hits > employment_hits and tenancy_hits >= 2:
        return "tenancy_document", "tenancy", "high" if tenancy_hits >= 4 else "medium"
    if "agreement" in lowered or "contract" in lowered:
        return "contract_document", "unknown", "low"
    return "plain_text_description", "unknown", "low"
