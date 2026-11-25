"""Opt-in, lazy-loaded model adapters. Heavy ML dependencies are optional.

Vision backbones use tf.keras.applications (not TensorFlow Hub). Hugging Face
pipelines are configurable and never replace the grounded legal-retrieval gate.
"""
from __future__ import annotations
import os
from functools import lru_cache

VISION_MODELS = {"mobilenet": "MobileNet", "resnet50": "ResNet50", "vgg16": "VGG16"}
DEFAULT_HF_MODEL = os.getenv("ARLAW_HF_MODEL", "distilbert/distilbert-base-uncased-finetuned-sst-2-english")


def _allowed_hf_models():
    """Return explicitly configured model IDs; never download arbitrary caller models."""
    configured = os.getenv("ARLAW_HF_ALLOWED_MODELS", "")
    allowed = {DEFAULT_HF_MODEL}
    allowed.update(item.strip() for item in configured.split(",") if item.strip())
    return allowed


def model_catalog():
    return {
        "vision": [{"id": key, "name": name, "available": _has_tensorflow()} for key, name in VISION_MODELS.items()],
        "nlp": {"provider": "Hugging Face Transformers", "default_model": DEFAULT_HF_MODEL,
                "allowed_models": sorted(_allowed_hf_models()), "available": _has_transformers(),
                "configured_model": os.getenv("ARLAW_HF_MODEL", "default")},
        "note": "Optional models load only when invoked. Vision models classify images; the default Hugging Face model is sentiment analysis, not a legal-answer model. Legal answers remain subject to source retrieval and evidence checks."
    }


def _has_tensorflow():
    try:
        import tensorflow  # noqa: F401
        return True
    except ImportError:
        return False


def _has_transformers():
    try:
        import transformers  # noqa: F401
        return True
    except ImportError:
        return False


@lru_cache(maxsize=3)
def _vision_model(name: str):
    if name not in VISION_MODELS:
        raise ValueError("Unsupported vision model")
    try:
        from tensorflow.keras.applications import MobileNet, ResNet50, VGG16
    except ImportError as exc:
        raise RuntimeError("Install the optional vision dependencies: pip install -r requirements-ml.txt") from exc
    return {"mobilenet": MobileNet, "resnet50": ResNet50, "vgg16": VGG16}[name](weights="imagenet")


def classify_image(name: str, image_bytes: bytes):
    import io
    try:
        from PIL import Image
        from tensorflow.keras.applications import mobilenet, resnet50, vgg16
        from tensorflow.keras.utils import img_to_array
    except ImportError as exc:
        raise RuntimeError("Install the optional vision dependencies: pip install -r requirements-ml.txt") from exc
    model = _vision_model(name)
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((224, 224))
    x = img_to_array(image)[None, ...]
    preprocess = {"mobilenet": mobilenet.preprocess_input, "resnet50": resnet50.preprocess_input, "vgg16": vgg16.preprocess_input}[name]
    decode = {"mobilenet": mobilenet.decode_predictions, "resnet50": resnet50.decode_predictions, "vgg16": vgg16.decode_predictions}[name]
    predictions = decode(model.predict(preprocess(x), verbose=0), top=5)[0]
    return [{"label": label, "confidence": float(score)} for _, label, score in predictions]


@lru_cache(maxsize=2)
def _hf_pipeline(task: str, model: str):
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError("Install optional NLP dependencies: pip install -r requirements-ml.txt") from exc
    return pipeline(task=task, model=model)


def run_hf_text(text: str, task: str = "sentiment-analysis", model: str | None = None):
    if task not in {"sentiment-analysis", "text-classification", "zero-shot-classification", "feature-extraction"}:
        raise ValueError("Unsupported Hugging Face task")
    if not text or len(text) > 12000:
        raise ValueError("Text must contain 1–12000 characters")
    selected = model or DEFAULT_HF_MODEL
    if selected not in _allowed_hf_models():
        raise ValueError("Model is not allowed. Configure its ID in ARLAW_HF_ALLOWED_MODELS.")
    result = _hf_pipeline(task, selected)(text)
    return {"task": task, "model": selected, "result": result}
