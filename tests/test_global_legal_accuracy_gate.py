from app import main


def test_global_router_detects_all_registry_country_names():
    assert "BR" in main._explicit_jurisdictions("Explain contract law in Brazil.")
    assert "ES" in main._explicit_jurisdictions("Explain Spanish law in Spain.")
    assert "NG" in main._explicit_jurisdictions("Explain Nigerian law in Nigeria.")
    assert "AE" in main._explicit_jurisdictions("Explain employment law in United Arab Emirates.")


def test_specific_uk_legal_system_is_not_broadened_to_uk():
    assert main._explicit_jurisdictions("Explain employment law in Scotland.") == ["SCO"]
    assert main._explicit_jurisdictions("Explain contract law in England and Wales.") == ["ENG-WAL"]


def test_multiple_explicit_jurisdictions_are_preserved():
    found = main._explicit_jurisdictions("Compare privacy law in Brazil and South Africa.")
    assert "BR" in found
    assert "ZA" in found


def test_legal_research_abstains_when_retrieval_is_disabled_or_empty():
    assert main._must_abstain_without_legal_sources("legal_research", True, [])
    assert main._must_abstain_without_legal_sources("civil_procedure", False, [])
    assert not main._must_abstain_without_legal_sources(
        "legal_research", True, [{"id": 1, "content": "verified excerpt"}]
    )


def test_nonlegal_tasks_are_not_blocked_by_legal_source_gate():
    assert not main._must_abstain_without_legal_sources("general", False, [])
