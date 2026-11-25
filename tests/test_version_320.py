from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_version_320_optional_model_routes_and_lazy_imports():
    main = (ROOT / 'app/main.py').read_text(encoding='utf-8')
    module = (ROOT / 'app/optional_models.py').read_text(encoding='utf-8')
    assert 'VERSION = "3.2.0"' in main
    assert '/api/models' in main
    assert '/api/models/huggingface' in main
    assert '/api/models/vision/{model_name}' in main
    assert 'from tensorflow.keras.applications import MobileNet, ResNet50, VGG16' in module
    assert 'from transformers import pipeline' in module
    assert 'lru_cache' in module
    assert 'not a legal-answer model' in module


def test_selective_and_bulk_history_deletion_controls():
    html = (ROOT / 'app/static/index.html').read_text(encoding='utf-8')
    js = (ROOT / 'app/static/app.js').read_text(encoding='utf-8')
    css = (ROOT / 'app/static/style.css').read_text(encoding='utf-8')
    for item in ('historySelectAll', 'historyDeleteSelected', 'historyClearAll'):
        assert f'id="{item}"' in html
        assert item in js
    assert 'Permanently delete ALL saved conversations?' in js
    assert 'Permanently delete ${ids.length} selected conversation(s)?' in js
    assert '.history-tools' in css


def test_optional_model_dependencies_are_not_added_to_default_requirements():
    requirements = (ROOT / 'requirements.txt').read_text(encoding='utf-8').lower()
    optional = (ROOT / 'requirements-ml.txt').read_text(encoding='utf-8').lower()
    assert 'tensorflow' not in requirements and 'transformers' not in requirements and 'torch' not in requirements
    assert 'tensorflow-cpu' in optional and 'transformers' in optional and 'torch' in optional


def test_history_uses_only_the_browser_local_implementation():
    html = (ROOT / 'app/static/index.html').read_text(encoding='utf-8')
    js = (ROOT / 'app/static/app.js').read_text(encoding='utf-8')
    assert '/static/app.js?v=3.2.0' in html
    assert 'history.js' not in html
    assert not (ROOT / 'app/static/history.js').exists()
    assert "const HISTORY_KEY='arlaw-chat-history-v1'" in js
    assert 'function deleteConversation(id)' in js


def test_hugging_face_models_are_allow_listed(monkeypatch):
    from app import optional_models
    monkeypatch.setenv('ARLAW_HF_ALLOWED_MODELS', 'org/approved-model')
    monkeypatch.setattr(optional_models, 'DEFAULT_HF_MODEL', 'org/default-model')
    import pytest
    with pytest.raises(ValueError, match='not allowed'):
        optional_models.run_hf_text('test input', model='org/untrusted-model')
