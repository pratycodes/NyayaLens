from __future__ import annotations

from backend.app.agents.graph import run_analysis
from backend.app.agents.issue_spotter import spot_issue
from backend.app.core.display import display_label
from backend.app.core.schemas import DocumentAnalysis, UserContext
from backend.app.documents.clause_extractor import extract_document_analysis
from backend.app.explainability.key_facts import key_fact_clauses

FREELANCE_AGREEMENT = """
FREELANCING AGREEMENT

This Freelancing Agreement is made at Mumbai on 20th February, 2024.

BETWEEN
Acme Demo Services LLP, a limited liability partnership, hereinafter referred to as the Company/Client

AND
Demo Freelancer as a Freelancer, hereinafter referred to as the Freelancer.

The Freelancer's designation will be Project Manager.
The Freelancer will provide project management services as per the scope of work.

Consideration: Compensation details shall be paid for services rendered by the Freelancer.
Invoice shall be generated for the monthly billing 7 days prior to the end of the month.
Payment shall be made in the last week of the pro-rata data month after invoice approval.
Compensation details as per pro-rata compensation table.
Initial Compensation 100000 75000 50,000/-
TDS will be deducted as per applicable.

The relationship between the parties is that of independent contractors.
Either party may terminate this Agreement by giving one month's written notice.
Disputes shall be referred to arbitration in Mumbai.
This Agreement is subject to the exclusive jurisdiction of the Courts of Mumbai.

Monetary damages would not be adequate and injunctive relief may be appropriate for breach of agreement.
"""


def test_display_labels_are_human_readable() -> None:
    assert display_label("contract_payment_review") == "Contract payment review"
    assert display_label("unpaid_compensation") == "Unpaid compensation / pending payment"
    assert display_label("freelance_service_agreement") == "Freelance/service agreement"
    assert display_label("contract_payment") == "Contract payment"


def test_freelance_agreement_classified_as_service_agreement() -> None:
    analysis = extract_document_analysis(FREELANCE_AGREEMENT)
    assert analysis.document_type == "freelance_service_agreement"
    assert analysis.detected_domain == "contract_payment"


def test_party_extraction_freelance_agreement() -> None:
    analysis = extract_document_analysis(FREELANCE_AGREEMENT)
    assert analysis.structured_facts["company_or_client"] == "ACME DEMO SERVICES LLP"
    assert analysis.structured_facts["freelancer_name"] == "Demo Freelancer"
    assert analysis.structured_facts["role_or_designation"] == "Project Manager"
    assert analysis.structured_facts["agreement_date"] == "20th February, 2024"
    assert analysis.structured_facts["agreement_location"] == "Mumbai"
    assert analysis.parties == ["ACME DEMO SERVICES LLP", "Demo Freelancer"]
    assert analysis.inferred_context["counterparty"].value == "ACME DEMO SERVICES LLP"
    assert analysis.inferred_context["user_role"].value == "freelancer"


def test_auto_detect_unpaid_salary_with_freelance_agreement() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            user_role="contractor",
            selected_dispute_type="auto-detect",
            query="unpaid salary",
        ),
        persist=False,
    )
    assert report.extracted_facts.document_type == "freelance_service_agreement"
    assert report.issue_detected.issue_type in {"unpaid_compensation", "unpaid_salary"}
    assert report.issue_detected.domain in {"contract_payment", "employment"}
    assert report.expert_route.primary_expert == "UnpaidCompensationExpert"
    assert report.expert_route.secondary_experts == ["ContractClauseExpert", "VerifierExpert"]
    assert report.expert_route.route_reason == (
        "Unpaid payment issue for a contractor/freelancer based on a service agreement."
    )
    assert report.issue_detected.issue_type != "repair_dispute"
    assert report.issue_detected.domain != "tenancy"


def test_tds_deducted_not_deposit_deduction() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            user_role="contractor",
            selected_dispute_type="auto-detect",
        ),
        persist=False,
    )
    assert report.issue_detected.issue_type != "deposit_deduction"
    assert report.issue_detected.domain != "tenancy"


def test_freelance_agreement_auto_detect_without_description() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            user_role="contractor",
            selected_dispute_type="auto-detect",
        ),
        persist=False,
    )
    assert report.issue_detected.issue_type == "contract_payment_review"
    assert report.issue_detected.domain == "contract_payment"
    assert report.expert_route.primary_expert == "ContractClauseExpert"
    assert report.expert_route.primary_expert != "TenancyExpert"


def test_freelance_agreement_unpaid_salary_auto_detect() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            user_role="contractor",
            selected_dispute_type="auto-detect",
            query="unpaid salary",
        ),
        persist=False,
    )
    assert report.issue_detected.issue_type in {"unpaid_compensation", "unpaid_salary"}
    assert report.issue_detected.domain in {"contract_payment", "employment"}
    assert report.expert_route.primary_expert == "UnpaidCompensationExpert"
    assert "itemized bills" not in set(report.missing_facts)
    assert "move-in/move-out condition" not in set(report.missing_facts)
    assert "rent payment proof" not in set(report.missing_facts)


def test_freelance_unpaid_text_uses_unpaid_compensation_expert() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            selected_dispute_type="auto-detect",
            query="I have not been paid",
        ),
        persist=False,
    )
    assert report.issue_detected.issue_type == "unpaid_compensation"
    assert report.issue_detected.domain == "contract_payment"
    assert report.expert_route.primary_expert == "UnpaidCompensationExpert"


def test_no_tenancy_missing_facts_for_freelance_payment() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            user_role="freelancer",
            selected_dispute_type="auto-detect",
            query="payment pending",
        ),
        persist=False,
    )
    missing = set(report.missing_facts)
    assert "itemized bills" not in missing
    assert "move-in/move-out condition" not in missing
    assert "rent payment proof" not in missing


def test_missing_facts_do_not_include_service_agreement_when_uploaded() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            user_role="freelancer",
            selected_dispute_type="auto-detect",
            query="payment pending",
        ),
        persist=False,
    )
    assert "contract/offer letter/service agreement" not in set(report.missing_facts)


def test_retrieval_domain_matches_contract_payment() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            user_role="contractor",
            selected_dispute_type="auto-detect",
            query="unpaid salary",
        ),
        persist=False,
    )
    assert report.retrieved_sources
    assert {source.citation.domain for source in report.retrieved_sources} <= {"employment"}


def test_issue_domain_consistency_guard_blocks_tenancy_false_positive() -> None:
    document = DocumentAnalysis(
        document_type="freelance_service_agreement",
        detected_domain="contract_payment",
    )
    corrected = spot_issue(
        "FREELANCING AGREEMENT. TDS will be deducted as per applicable.",
        document,
        UserContext(
            user_role="contractor",
            selected_dispute_type="auto-detect",
            query="deposit deduction",
        ),
    )
    assert corrected.issue_type in {"contract_payment_review", "unpaid_compensation"}
    assert corrected.domain == "contract_payment"


def test_security_deposit_still_detected_for_real_tenancy() -> None:
    document = DocumentAnalysis(document_type="tenancy_document", detected_domain="tenancy")
    issue = spot_issue(
        "Rent agreement between landlord and tenant. Security deposit refund was not returned.",
        document,
        UserContext(selected_dispute_type="auto-detect"),
    )
    assert issue.issue_type == "deposit_deduction"
    assert issue.domain == "tenancy"


def test_generic_damages_not_repairs_maintenance() -> None:
    analysis = extract_document_analysis(
        "Monetary damages would not be adequate and injunctive relief is appropriate for breach of agreement."
    )
    assert "repairs_maintenance" not in {clause.name for clause in analysis.extracted_clauses}


def test_tenancy_requires_strong_tenancy_terms() -> None:
    analysis = extract_document_analysis(
        "Agreement for services involving office premises access, damages, arbitration, and termination."
    )
    assert analysis.detected_domain != "tenancy"
    assert analysis.document_type != "tenancy_document"


def test_payment_clauses_extracted_from_freelance_agreement() -> None:
    analysis = extract_document_analysis(FREELANCE_AGREEMENT)
    names = {clause.name for clause in analysis.extracted_clauses}
    assert "invoice_clause" in names
    assert "payment_timing_clause" in names
    assert {"compensation_clause", "consideration_clause"}.intersection(names)
    assert "pro_rata_compensation_clause" in names
    assert "tds_clause" in names
    assert "independent_contractor_clause" in names
    assert "termination_notice_clause" in names
    assert "jurisdiction_clause" in names
    assert "arbitration_clause" in names
    values = {clause.name: clause.value for clause in analysis.extracted_clauses}
    assert values["invoice_clause"] == "monthly billing invoice generated 7 days prior to month end"
    assert values["payment_timing_clause"] == "last week of the pro-rata month"


def test_freelance_key_facts_prioritize_payment() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            user_role="freelancer",
            selected_dispute_type="auto-detect",
        ),
        persist=False,
    )
    names = [clause.name for clause in key_fact_clauses(report)]
    assert "invoice_clause" in names
    assert "payment_timing_clause" in names
    assert "compensation_clause" in names
    assert "tds_clause" in names
    assert "independent_contractor_clause" in names
    assert "arbitration_clause" in names
    assert "jurisdiction_clause" in names
    assert "freelancer_role" not in names


def test_amount_extractor_handles_compensation_table() -> None:
    analysis = extract_document_analysis("Compensation details. Initial Compensation 100000 75000 50,000/-")
    assert "100000" in analysis.amounts
    assert "75000" in analysis.amounts
    assert "50,000/-" in analysis.amounts
    assert "rs," not in {amount.lower() for amount in analysis.amounts}


def test_clause_dedup_removes_repeated_termination_fragments() -> None:
    analysis = extract_document_analysis(
        """
        Service Agreement. Freelancer services.
        Termination of this Agreement.
        Termination of this Agreement may occur by notice.
        Either party may terminate this Agreement if breach continues.
        """
    )
    termination = [
        clause for clause in analysis.extracted_clauses if clause.name == "termination_clause"
    ]
    assert len(termination) <= 1


def test_unpaid_compensation_missing_facts_specific() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            user_role="freelancer",
            selected_dispute_type="auto-detect",
            query="unpaid salary",
        ),
        persist=False,
    )
    missing = set(report.missing_facts)
    assert "amount unpaid" in missing
    assert "payment due date" in missing
    assert "copy of invoice/payment request" in missing
    assert "proof of work delivered" in missing
    assert "written follow-up sent or not" in missing
    assert "dispute domain" not in missing


def test_freelance_contract_review_uses_contract_clause_expert() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            selected_dispute_type="auto-detect",
        ),
        persist=False,
    )
    assert report.issue_detected.issue_type == "contract_payment_review"
    assert report.expert_route.primary_expert == "ContractClauseExpert"
    assert report.expert_route.secondary_experts == ["UnpaidCompensationExpert", "VerifierExpert"]
    assert report.expert_route.route_reason == (
        "Freelance/service agreement detected; reviewing payment and dispute-resolution clauses."
    )


def test_freelance_remedy_not_hr_payroll_by_default() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            selected_dispute_type="auto-detect",
        ),
        persist=False,
    )
    assert "Company/Client/Accounts Team" in (report.remedy_plan.draft_message or "")
    assert "HR/Payroll Team" not in (report.remedy_plan.draft_message or "")


def test_freelance_risk_flags_include_payment_terms() -> None:
    report = run_analysis(
        text=FREELANCE_AGREEMENT,
        filename="freelance_agreement.txt",
        context=UserContext(
            state="Maharashtra",
            city="Mumbai",
            selected_dispute_type="auto-detect",
        ),
        persist=False,
    )
    titles = {risk.title for risk in report.risk_flags}
    assert "Payment terms found; unpaid status not specified" in titles
    assert "Invoice/payment timing clause should be matched against actual unpaid period" in titles
    assert "TDS/deduction clause may need clarification" in titles
    assert "Independent contractor relationship may affect remedy route" in titles
    assert "Arbitration/jurisdiction clause may affect dispute path" in titles
