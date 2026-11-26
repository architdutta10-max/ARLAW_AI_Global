from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def test_version_320_optional_model_routes_and_lazy_imports():
    main = (ROOT / 'app/main.py').read_text(encoding='utf-8')
    module = (ROOT / 'app/optional_models.py').read_text(encoding='utf-8')
    assert 'VERSION = "3.4.0"' in main
    assert '/api/models' in main
    assert '/api/models/huggingface' in main
    assert '/api/models/vision/{model_name}' in main
    assert 'tfhub.dev/google/imagenet/mobilenet_v2_100_224/classification/5' in module
    assert 'tfhub.dev/google/imagenet/resnet_v1_50/classification/5' in module
    assert 'VGG-16' in module and 'tensorflow.keras.applications' in module
    assert 'trust_remote_code=False' in module
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
    assert 'tensorflow-cpu' in optional and 'tensorflow-hub' in optional and 'transformers' in optional and 'torch' in optional
