from backend.app.law_packs.official_source_metadata import infer_law_metadata


def test_primary_act_title_beats_internal_ipc_reference() -> None:
    text = """
    THE INDIAN CONTRACT ACT, 1872
    ARRANGEMENT OF SECTIONS
    Later cross-reference: the Indian Penal Code may be mentioned in this Act.
    """

    metadata = infer_law_metadata("A187209", "contract", text)

    assert metadata.act_name == "Indian Contract Act, 1872"
    assert metadata.domain == "contract_payment"
    assert "contract_payment" in metadata.issue_tags


def test_bnss_title_beats_later_bns_reference() -> None:
    text = """
    EXTRAORDINARY
    THE BHARATIYA NAGARIK SURAKSHA SANHITA, 2023
    Later references may mention the Bharatiya Nyaya Sanhita, 2023.
    """

    metadata = infer_law_metadata("250884_2_english_01042024", "criminal", text)

    assert metadata.act_name == "Bharatiya Nagarik Suraksha Sanhita, 2023"
    assert metadata.effective_from == "2024-07-01"
    assert metadata.effective_to is None


def test_historical_ipc_metadata_has_effective_end_date() -> None:
    metadata = infer_law_metadata(
        "250882_english_01042024",
        "criminal",
        "THE INDIAN PENAL CODE\nARRANGEMENT OF SECTIONS",
    )

    assert metadata.act_name == "Indian Penal Code, 1860"
    assert metadata.effective_to == "2024-06-30"


def test_unreadable_tenancy_file_keeps_tenancy_tags() -> None:
    metadata = infer_law_metadata("34 of 2001 (E)", "tenancy", "\x01\x02\x03")

    assert metadata.domain == "tenancy_deposit"
    assert "deposit_deduction" in metadata.issue_tags
