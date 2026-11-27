from app.scope import assess_scope

def test_legal_research_is_in_scope():
    assert assess_scope("Explain Article 21 of the Constitution of India")["in_scope"]

def test_economic_policy_is_in_scope():
    assert assess_scope("Explain RBI monetary policy and inflation")["in_scope"]

def test_professional_contract_review_is_in_scope():
    assert assess_scope("Review this employment contract")["in_scope"]

def test_unrelated_poem_is_out_of_scope():
    assert not assess_scope("Write a poem about the moon")["in_scope"]

def test_unrelated_shopping_is_out_of_scope():
    assert not assess_scope("Recommend a gaming laptop")["in_scope"]

def test_short_follow_up_inherits_legal_context():
    messages = [
        {"role": "user", "content": "Explain Article 21"},
        {"role": "assistant", "content": "..."},
        {"role": "user", "content": "Explain more"},
    ]
    assert assess_scope("Explain more", messages)["in_scope"]
