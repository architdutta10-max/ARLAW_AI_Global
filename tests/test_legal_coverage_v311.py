from app import knowledge, main


def _seed(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge, "DB_PATH", tmp_path / "legal-coverage.db")
    knowledge.init_db()
    knowledge.seed_builtin_knowledge()


def test_five_question_global_legal_coverage_retrieves_each_jurisdiction(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    prompt = """**1. Article 21 of the Constitution of India**
Explain Article 21 text and Maneka Gandhi fair just reasonable procedure.

**2. Privacy and data-protection laws (India, Germany, UK, US)**
Compare privacy and data protection laws.

**3. Corporate fraud and corporate criminal liability (directors & officers)**
Explain corporate fraud and corporate criminal liability, responsibilities of directors and officers.

**4. Cartelisation and anti-competitive agreements (India & EU)**
Explain cartelisation and anti-competitive agreements under Indian and EU competition law.

**5. Trade restrictions, sanctions, and export-control rules (India, Germany, Singapore)**
Explain trade restrictions, international sanctions and export controls."""
    hits, coverage, task = main._retrieve_request(prompt, "GLOBAL", 5)

    assert task == "legal_research"
    assert len(coverage) == 5
    assert coverage[0]["jurisdictions_with_sources"] == ["IN"]
    assert coverage[1]["jurisdictions_with_sources"] == ["IN", "DE", "UK", "US"]
    assert coverage[2]["jurisdictions_with_sources"] == ["GLOBAL"]
    assert coverage[3]["jurisdictions_with_sources"] == ["IN", "EU"]
    assert coverage[4]["jurisdictions_with_sources"] == ["IN", "DE", "SG", "INTL"]

    titles = "\n".join(hit["title"] for hit in hits)
    for expected in (
        "Article 21", "Digital Personal Data Protection", "GDPR",
        "Global comparison",
        "cartelisation", "Article 101", "SCOMET", "dual-use export controls",
        "Singapore", "UN Security Council sanctions",
    ):
        assert expected.lower() in titles.lower(), expected


def test_privacy_law_retrieval_finds_four_country_frameworks(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    cases = {
        "IN": "India DPDP Act 2023 commencement privacy data protection",
        "DE": "Germany GDPR BDSG data protection privacy",
        "UK": "UK GDPR Data Protection Act 2018 privacy data protection",
        "US": "United States federal state privacy HIPAA GLBA FTC data protection",
    }
    for jurisdiction, query in cases.items():
        hits = knowledge.search(query, 5, jurisdiction, "legal_research")
        assert hits, jurisdiction
        assert all(hit["jurisdiction"] == jurisdiction for hit in hits)


def test_trade_control_sources_are_jurisdiction_matched(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    cases = {
        "IN": "India export controls SCOMET DGFT Foreign Trade Development Regulation Act",
        "DE": "Germany EU dual use export controls AWG AWV sanctions",
        "SG": "Singapore Strategic Goods Control Act export permit sanctions",
        "INTL": "international sanctions UN Security Council cross-border trade",
    }
    for jurisdiction, query in cases.items():
        hits = knowledge.search(query, 5, jurisdiction, "legal_research")
        assert hits, jurisdiction
        assert all(hit["jurisdiction"] == jurisdiction for hit in hits)


def test_five_user_benchmark_prompts_retrieve_topic_sources_for_each_named_jurisdiction(tmp_path, monkeypatch):
    from app.llm import fit_context
    _seed(tmp_path, monkeypatch)
    prompts = [
        (
            "Explain the scope of Article 21 of the Constitution of India. Analyse Maneka Gandhi v. Union of India (1978), including its relationship with Articles 14 and 19.",
            ["IN"], ["Constitution of India", "Maneka Gandhi"],
        ),
        (
            "Compare India DPDP Act 2023, EU GDPR and UK GDPR, including commencement dates and individual rights.",
            ["IN", "UK", "EU"], ["Digital Personal Data Protection", "UK GDPR", "GDPR Regulation (EU) 2016/679"],
        ),
        (
            "A multinational company conceals financial losses, falsifies accounts and transfers assets for personal benefit. Analyse liability under Indian, UK, US and German law.",
            ["IN", "DE", "UK", "US"], ["India — corporate fraud", "Germany — corporate offences", "United Kingdom — corporate fraud", "United States — corporate criminal liability"],
        ),
        (
            "Competing companies secretly agree to fix prices, divide markets and restrict supply across India and the EU. Analyse Competition Act 2002 and Articles 101–102 TFEU.",
            ["IN", "EU"], ["India — cartelisation", "European Union — Article 101 TFEU"],
        ),
        (
            "An Indian manufacturer exports dual-use electronic components through Singapore to an EU buyer. Explain SCOMET, Singapore Strategic Goods Act 2002, EU Dual-Use Regulation 2021/821 and UN sanctions obligations.",
            ["IN", "EU", "SG", "INTL"], ["SCOMET", "Dual-Use Regulation (EU) 2021/821", "Singapore — strategic goods", "UN Security Council sanctions"],
        ),
    ]
    for prompt, expected_jurisdictions, expected_titles in prompts:
        hits, coverage, task = main._retrieve_request(prompt, "GLOBAL", 5)
        assert task == "legal_research"
        assert coverage[0]["jurisdictions_searched"] == expected_jurisdictions
        assert coverage[0]["jurisdictions_with_sources"] == expected_jurisdictions
        context, included = fit_context([
            f"[S{i}] {hit['title']} | {hit['jurisdiction']}\n{hit['content']}"
            for i, hit in enumerate(hits, 1)
        ])
        assert included == len(hits)
        for expected in expected_titles:
            assert expected.lower() in context.lower(), expected
