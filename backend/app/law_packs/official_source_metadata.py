from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class InferredLawMetadata:
    act_name: str
    act_id: str
    section_number: str
    section_title: str
    domain: str
    issue_tags: list[str]
    effective_from: str
    effective_to: str | None
    version_date: str
    source_authority: str
    jurisdiction: str = "India"
    state: str | None = None
    source_url: str | None = None


def _clean(value: str) -> str:
    return " ".join(value.replace("_", " ").replace("-", " ").split()).strip()


def _normalize_title_text(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()


def _default_tags_for_folder(domain: str) -> tuple[str, list[str]]:
    if domain == "contract":
        return "contract_payment", [
            "contract_payment",
            "employment_contract",
            "payment_deduction",
            "unpaid_compensation",
        ]
    if domain == "labour":
        return "labour_wage", ["labour_wage", "employment", "unpaid_salary", "labour_classification"]
    if domain == "criminal":
        return "criminal_screening", ["criminal_screening"]
    if domain == "constitution":
        return "constitution_public_law", ["constitution_public_law", "public_authority_abuse"]
    if domain == "tenancy":
        return "tenancy_deposit", [
            "tenancy_deposit",
            "tenancy_repairs",
            "deposit_deduction",
            "repair_dispute",
            "eviction_notice",
            "rent_increase",
        ]
    if domain == "legal_aid":
        return "grievance", ["grievance", "legal_aid", "constitution_public_law"]
    return domain, [domain]


KNOWN_SOURCE_URLS = {
    "250883_english_01042024": "https://www.mha.gov.in/sites/default/files/250883_english_01042024.pdf",
    "250884_2_english_01042024": "https://www.mha.gov.in/sites/default/files/250884_2_english_01042024.pdf",
    "250882_english_01042024": "https://www.mha.gov.in/sites/default/files/250882_english_01042024.pdf",
    "THE-INDIAN-PENAL-CODE-1860": "https://www.indiacode.nic.in/bitstream/123456789/4219/1/THE-INDIAN-PENAL-CODE-1860.pdf",
    "delhi_rent_control_act_1958": "https://www.indiacode.nic.in/bitstream/123456789/19223/1/a1958-59.pdf",
    "bihar_government_premises_rent_recovery_eviction_act_1956": "https://www.indiacode.nic.in/bitstream/123456789/12209/1/20-1956_revenue.pdf",
    "punjab_rent_act_1995": "https://www.indiacode.nic.in/bitstream/123456789/22097/1/the_punjab_rent_act_1995.pdf",
    "up_urban_premises_tenancy_act_2021": "https://www.indiacode.nic.in/bitstream/123456789/21157/1/english_16_of_2021.pdf",
    "up_urban_premises_tenancy_act_2021_ocr": "https://www.indiacode.nic.in/bitstream/123456789/21157/1/english_16_of_2021.pdf",
    "west_bengal_premises_tenancy_act_1997": "https://www.indiacode.nic.in/bitstream/123456789/14542/1/1997-37.pdf",
    "rajasthan_rent_control_act_2001": "https://www.indiacode.nic.in/bitstream/123456789/18822/1/rajasthan_rent_control_act_2001_with_amendments.pdf",
}

TENANCY_ISSUE_TAGS = [
    "tenancy_deposit",
    "tenancy_repairs",
    "deposit_deduction",
    "repair_dispute",
    "eviction_notice",
    "rent_increase",
]


def infer_law_metadata(filename_stem: str, folder_domain: str, text: str) -> InferredLawMetadata:
    upper = text[:120000].upper()
    title_window = upper[:10000]
    cleaned_name = _clean(filename_stem).title()
    domain, tags = _default_tags_for_folder(folder_domain)
    metadata = InferredLawMetadata(
        act_name=cleaned_name,
        act_id=filename_stem,
        section_number=filename_stem,
        section_title=cleaned_name,
        domain=domain,
        issue_tags=tags,
        effective_from="1900-01-01",
        effective_to=None,
        version_date="unknown",
        source_authority="User supplied local official-source file",
        source_url=KNOWN_SOURCE_URLS.get(filename_stem),
    )

    def with_values(**updates: object) -> InferredLawMetadata:
        return InferredLawMetadata(**{**metadata.__dict__, **updates})

    title_candidates = {
        "THE BHARATIYA NYAYA SANHITA, 2023": "bns",
        "THE BHARATIYA NAGARIK SURAKSHA SANHITA, 2023": "bnss",
        "THE BHARATIYA SAKSHYA ADHINIYAM, 2023": "bsa",
        "THE INDIAN PENAL CODE": "ipc",
        "THE CODE OF CRIMINAL PROCEDURE, 1973": "crpc",
        "THE INDIAN EVIDENCE ACT, 1872": "evidence",
        "THE INDIAN CONTRACT ACT, 1872": "contract",
        "THE SPECIFIC RELIEF ACT, 1963": "specific_relief",
        "THE ARBITRATION AND CONCILIATION ACT, 1996": "arbitration",
        "THE CODE ON WAGES, 2019": "code_on_wages",
        "THE INDUSTRIAL RELATIONS CODE, 2020": "industrial_relations",
        "THE CODE ON SOCIAL SECURITY, 2020": "social_security",
        "THE OCCUPATIONAL SAFETY, HEALTH AND WORKING": "osh",
        "THE MAHARASHTRA RENT CONTROL ACT, 1999": "maharashtra_rent",
        "THE KARNATAKA RENT ACT, 1999": "karnataka_rent",
        "THE DELHI RENT CONTROL ACT, 1958": "delhi_rent",
        "THE BIHAR GOVERNMENT PREMISES (RENT RECOVERY AND EVICTION) ACT, 1956": "bihar_government_premises_rent",
        "THE PUNJAB RENT ACT, 1995": "punjab_rent",
        "THE UTTAR PRADESH REGULATION OF URBAN PREMISES TENANCY ACT, 2021": "up_urban_premises_tenancy",
        "THE WEST BENGAL PREMISES TENANCY ACT, 1997": "west_bengal_premises_tenancy",
        "THE RAJASTHAN RENT CONTROL ACT, 2001": "rajasthan_rent",
        "THE LEGAL SERVICES AUTHORITIES ACT, 1987": "legal_services",
        "THE CONSTITUTION OF INDIA": "constitution",
    }
    normalized_title_window = _normalize_title_text(title_window)
    found_titles = []
    for phrase, key in title_candidates.items():
        position = title_window.find(phrase)
        normalized_position = normalized_title_window.find(_normalize_title_text(phrase))
        if position >= 0 or normalized_position >= 0:
            found_titles.append((position if position >= 0 else normalized_position, key))
    tenancy_title_keys = {
        "maharashtra_rent",
        "karnataka_rent",
        "delhi_rent",
        "bihar_government_premises_rent",
        "punjab_rent",
        "up_urban_premises_tenancy",
        "west_bengal_premises_tenancy",
        "rajasthan_rent",
    }
    # State gazettes often mention Article 348/Constitution before the Act title.
    # In tenancy folders, prefer a tenancy Act title over an earlier generic reference.
    title_pool = (
        [item for item in found_titles if item[1] in tenancy_title_keys]
        if folder_domain == "tenancy"
        else found_titles
    )
    detected_title = min(title_pool or found_titles, default=(None, None))[1]

    if detected_title == "bns":
        return with_values(
            act_name="Bharatiya Nyaya Sanhita, 2023",
            act_id="bns_2023",
            section_number="full_act",
            section_title="Bharatiya Nyaya Sanhita, 2023",
            domain="criminal_screening",
            issue_tags=["criminal_screening", "forged_document", "threat_blackmail", "fraud"],
            effective_from="2024-07-01",
            version_date="2024-04-01",
            source_authority="Ministry of Home Affairs",
        )
    if detected_title == "bnss":
        return with_values(
            act_name="Bharatiya Nagarik Suraksha Sanhita, 2023",
            act_id="bnss_2023",
            section_number="full_act",
            section_title="Bharatiya Nagarik Suraksha Sanhita, 2023",
            domain="criminal_screening",
            issue_tags=["criminal_screening", "procedure", "threat_blackmail", "fraud"],
            effective_from="2024-07-01",
            version_date="2024-04-01",
            source_authority="Ministry of Home Affairs",
        )
    if detected_title == "bsa":
        return with_values(
            act_name="Bharatiya Sakshya Adhiniyam, 2023",
            act_id="bsa_2023",
            section_number="full_act",
            section_title="Bharatiya Sakshya Adhiniyam, 2023",
            domain="criminal_screening",
            issue_tags=["criminal_screening", "evidence", "forged_document", "fraud"],
            effective_from="2024-07-01",
            version_date="2024-04-01",
            source_authority="Ministry of Home Affairs",
        )
    if detected_title == "ipc":
        return with_values(
            act_name="Indian Penal Code, 1860",
            act_id="ipc_1860",
            section_number="full_act",
            section_title="Indian Penal Code, 1860",
            domain="criminal_screening",
            issue_tags=["criminal_screening", "forged_document", "threat_blackmail", "fraud"],
            effective_from="1860-10-06",
            effective_to="2024-06-30",
            version_date="historical",
            source_authority="India Code / Legislative Department",
        )
    if detected_title == "crpc":
        return with_values(
            act_name="Code of Criminal Procedure, 1973",
            act_id="crpc_1973",
            section_number="full_act",
            section_title="Code of Criminal Procedure, 1973",
            domain="criminal_screening",
            issue_tags=["criminal_screening", "procedure"],
            effective_from="1974-04-01",
            effective_to="2024-06-30",
            version_date="historical",
            source_authority="India Code / Legislative Department",
        )
    if detected_title == "evidence":
        return with_values(
            act_name="Indian Evidence Act, 1872",
            act_id="evidence_act_1872",
            section_number="full_act",
            section_title="Indian Evidence Act, 1872",
            domain="criminal_screening",
            issue_tags=["criminal_screening", "evidence", "forged_document", "fraud"],
            effective_from="1872-09-01",
            effective_to="2024-06-30",
            version_date="historical",
            source_authority="India Code / Legislative Department",
        )
    if detected_title == "contract":
        return with_values(
            act_name="Indian Contract Act, 1872",
            act_id="indian_contract_act_1872",
            section_number="full_act",
            section_title="Indian Contract Act, 1872",
            domain="contract_payment",
            issue_tags=["contract_payment", "employment_contract", "unpaid_compensation", "payment_deduction"],
            effective_from="1872-09-01",
            version_date="official_local_file",
            source_authority="India Code / Legislative Department",
        )
    if detected_title == "specific_relief":
        return with_values(
            act_name="Specific Relief Act, 1963",
            act_id="specific_relief_act_1963",
            section_number="full_act",
            section_title="Specific Relief Act, 1963",
            domain="contract_payment",
            issue_tags=["contract_payment", "employment_contract", "restraint_review"],
            effective_from="1964-03-01",
            version_date="official_local_file",
            source_authority="India Code / Legislative Department",
        )
    if detected_title == "arbitration":
        return with_values(
            act_name="Arbitration and Conciliation Act, 1996",
            act_id="arbitration_conciliation_act_1996",
            section_number="full_act",
            section_title="Arbitration and Conciliation Act, 1996",
            domain="contract_payment",
            issue_tags=["contract_payment", "employment_contract", "tenancy_deposit", "dispute_process"],
            effective_from="1996-08-22",
            version_date="official_local_file",
            source_authority="India Code / Legislative Department",
        )
    if detected_title == "code_on_wages":
        return with_values(
            act_name="Code on Wages, 2019",
            act_id="code_on_wages_2019",
            section_number="full_act",
            section_title="Code on Wages, 2019",
            domain="labour_wage",
            issue_tags=["labour_wage", "unpaid_salary", "full_and_final", "employment"],
            effective_from="2019-08-08",
            version_date="official_local_file",
            source_authority="India Code / Legislative Department",
        )
    if detected_title == "industrial_relations":
        return with_values(
            act_name="Industrial Relations Code, 2020",
            act_id="industrial_relations_code_2020",
            section_number="full_act",
            section_title="Industrial Relations Code, 2020",
            domain="employment",
            issue_tags=["employment", "labour_classification", "full_and_final"],
            effective_from="2020-09-29",
            version_date="official_local_file",
            source_authority="India Code / Legislative Department",
        )
    if detected_title == "social_security":
        return with_values(
            act_name="Code on Social Security, 2020",
            act_id="code_on_social_security_2020",
            section_number="full_act",
            section_title="Code on Social Security, 2020",
            domain="employment",
            issue_tags=["employment", "labour_classification", "unpaid_salary"],
            effective_from="2020-09-29",
            version_date="official_local_file",
            source_authority="India Code / Legislative Department",
        )
    if detected_title == "osh":
        return with_values(
            act_name="Occupational Safety, Health and Working Conditions Code, 2020",
            act_id="osh_working_conditions_code_2020",
            section_number="full_act",
            section_title="Occupational Safety, Health and Working Conditions Code, 2020",
            domain="employment",
            issue_tags=["employment", "labour_classification"],
            effective_from="2020-09-29",
            version_date="official_local_file",
            source_authority="India Code / Legislative Department",
        )
    if detected_title == "maharashtra_rent":
        return with_values(
            act_name="Maharashtra Rent Control Act, 1999",
            act_id="maharashtra_rent_control_act_1999",
            section_number="full_act",
            section_title="Maharashtra Rent Control Act, 1999",
            domain="tenancy_deposit",
            issue_tags=TENANCY_ISSUE_TAGS,
            effective_from="2000-03-31",
            version_date="official_local_file",
            source_authority="Maharashtra government / India Code",
            state="Maharashtra",
        )
    if detected_title == "karnataka_rent":
        return with_values(
            act_name="Karnataka Rent Act, 1999",
            act_id="karnataka_rent_act_1999",
            section_number="full_act",
            section_title="Karnataka Rent Act, 1999",
            domain="tenancy_deposit",
            issue_tags=TENANCY_ISSUE_TAGS,
            effective_from="2001-12-31",
            version_date="official_local_file",
            source_authority="Karnataka government / India Code",
            state="Karnataka",
        )
    if detected_title == "delhi_rent":
        return with_values(
            act_name="Delhi Rent Control Act, 1958",
            act_id="delhi_rent_control_act_1958",
            section_number="full_act",
            section_title="Delhi Rent Control Act, 1958",
            domain="tenancy_deposit",
            issue_tags=TENANCY_ISSUE_TAGS,
            effective_from="1958-12-31",
            version_date="official_local_file",
            source_authority="India Code / Legislative Department",
            jurisdiction="Delhi",
            state="Delhi",
        )
    if detected_title == "bihar_government_premises_rent":
        return with_values(
            act_name="Bihar Government Premises (Rent Recovery and Eviction) Act, 1956",
            act_id="bihar_government_premises_rent_recovery_eviction_act_1956",
            section_number="full_act",
            section_title="Bihar Government Premises (Rent Recovery and Eviction) Act, 1956",
            domain="tenancy_deposit",
            issue_tags=["tenancy_deposit", "eviction_notice", "public_premises", "rent_recovery"],
            effective_from="1956-10-01",
            version_date="official_local_file",
            source_authority="Bihar government / India Code",
            jurisdiction="Bihar",
            state="Bihar",
        )
    if detected_title == "punjab_rent":
        return with_values(
            act_name="Punjab Rent Act, 1995",
            act_id="punjab_rent_act_1995",
            section_number="full_act",
            section_title="Punjab Rent Act, 1995",
            domain="tenancy_deposit",
            issue_tags=TENANCY_ISSUE_TAGS,
            effective_from="2012-11-28",
            version_date="2025-09-15",
            source_authority="Punjab government / India Code",
            jurisdiction="Punjab",
            state="Punjab",
        )
    if detected_title == "up_urban_premises_tenancy":
        return with_values(
            act_name="Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021",
            act_id="up_urban_premises_tenancy_act_2021",
            section_number="full_act",
            section_title="Uttar Pradesh Regulation of Urban Premises Tenancy Act, 2021",
            domain="tenancy_deposit",
            issue_tags=TENANCY_ISSUE_TAGS,
            effective_from="2021-08-24",
            version_date="official_local_file",
            source_authority="Uttar Pradesh government / India Code",
            jurisdiction="Uttar Pradesh",
            state="Uttar Pradesh",
        )
    if detected_title == "west_bengal_premises_tenancy":
        return with_values(
            act_name="West Bengal Premises Tenancy Act, 1997",
            act_id="west_bengal_premises_tenancy_act_1997",
            section_number="full_act",
            section_title="West Bengal Premises Tenancy Act, 1997",
            domain="tenancy_deposit",
            issue_tags=TENANCY_ISSUE_TAGS,
            effective_from="1998-12-28",
            version_date="official_local_file",
            source_authority="West Bengal government / India Code",
            jurisdiction="West Bengal",
            state="West Bengal",
        )
    if detected_title == "rajasthan_rent":
        return with_values(
            act_name="Rajasthan Rent Control Act, 2001",
            act_id="rajasthan_rent_control_act_2001",
            section_number="full_act",
            section_title="Rajasthan Rent Control Act, 2001",
            domain="tenancy_deposit",
            issue_tags=TENANCY_ISSUE_TAGS,
            effective_from="2001-11-30",
            version_date="official_local_file",
            source_authority="Rajasthan government / India Code",
            jurisdiction="Rajasthan",
            state="Rajasthan",
        )
    if detected_title == "legal_services":
        return with_values(
            act_name="Legal Services Authorities Act, 1987",
            act_id="legal_services_authorities_act_1987",
            section_number="full_act",
            section_title="Legal Services Authorities Act, 1987",
            domain="grievance",
            issue_tags=["grievance", "legal_aid", "constitution_public_law"],
            effective_from="1995-11-09",
            version_date="official_local_file",
            source_authority="India Code / Legislative Department",
        )
    if detected_title == "constitution":
        return with_values(
            act_name="Constitution of India",
            act_id="constitution_of_india",
            section_number="full_text",
            section_title="Constitution of India",
            domain="constitution_public_law",
            issue_tags=["constitution_public_law", "public_authority_abuse", "state_action"],
            effective_from="1950-01-26",
            version_date="official_local_file",
            source_authority="Legislative Department",
        )
    return metadata


OFFICIAL_SOURCE_SUGGESTIONS = {
    "criminal": [
        {
            "name": "Bharatiya Nyaya Sanhita, 2023",
            "authority": "India Code / Legislative Department",
            "target_dir": "data/raw/official/criminal/",
        },
        {
            "name": "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "authority": "India Code / Legislative Department",
            "target_dir": "data/raw/official/criminal/",
        },
        {
            "name": "Bharatiya Sakshya Adhiniyam, 2023",
            "authority": "India Code / Legislative Department",
            "target_dir": "data/raw/official/criminal/",
        },
    ],
    "contract": [
        {
            "name": "Indian Contract Act, 1872",
            "authority": "India Code / Legislative Department",
            "target_dir": "data/raw/official/contract/",
        }
    ],
    "labour": [
        {
            "name": "Central/state wage and labour materials relevant to the worker category",
            "authority": "Central or state labour department",
            "target_dir": "data/raw/official/labour/",
        }
    ],
    "constitution": [
        {
            "name": "Constitution of India",
            "authority": "India Code / Legislative Department",
            "target_dir": "data/raw/official/constitution/",
        }
    ],
    "tenancy": [
        {
            "name": "Applicable state rent/tenancy act or public guidance",
            "authority": "State rent/civil authority",
            "target_dir": "data/raw/official/tenancy/",
        }
    ],
}
