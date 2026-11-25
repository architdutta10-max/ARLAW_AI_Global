"""Opt-in, lazy-loaded TensorFlow Hub/Keras vision and Hugging Face NLP adapters.

MobileNetV2 and ResNet-50 use official TensorFlow Hub ImageNet classifiers.
VGG-16 uses tf.keras.applications because a maintained, equivalent official
VGG-16 classification handle is not listed in TensorFlow Hub's model tutorial.
These are generic image classifiers, not legal-document/OCR models.
"""
from __future__ import annotations
import os
from functools import lru_cache

VISION_MODELS = {
    "mobilenet": {
        "name": "MobileNetV2",
        "provider": "TensorFlow Hub",
        "handle": "https://tfhub.dev/google/imagenet/mobilenet_v2_100_224/classification/5",
        "image_size": 224,
    },
    "resnet50": {
        "name": "ResNet-50",
        "provider": "TensorFlow Hub",
        "handle": "https://tfhub.dev/google/imagenet/resnet_v1_50/classification/5",
        "image_size": 224,
    },
    "vgg16": {
        "name": "VGG-16",
        "provider": "TensorFlow Keras Applications",
        "handle": None,
        "image_size": 224,
    },
}
DEFAULT_HF_MODEL = os.getenv(
    "ARLAW_HF_MODEL", "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
)
HF_ALLOWED_TASKS = {
    "sentiment-analysis", "text-classification", "zero-shot-classification",
    "feature-extraction", "token-classification", "ner",
}


def _has_tensorflow():
    try:
        import tensorflow  # noqa: F401
        return True
    except ImportError:
        return False


def _has_tfhub():
    try:
        import tensorflow_hub  # noqa: F401
        return True
    except ImportError:
        return False


def _has_transformers():
    try:
        import transformers  # noqa: F401
        return True
    except ImportError:
        return False


def model_catalog():
    tf = _has_tensorflow()
    hub = _has_tfhub()
    return {
        "vision": [
            {
                "id": key,
                "name": spec["name"],
                "provider": spec["provider"],
                "available": (hub if spec["provider"] == "TensorFlow Hub" else tf),
                "requires": ("tensorflow-cpu,tensorflow-hub,Pillow" if spec["provider"] == "TensorFlow Hub" else "tensorflow-cpu,Pillow"),
            }
            for key, spec in VISION_MODELS.items()
        ],
        "nlp": {
            "provider": "Hugging Face Transformers",
            "default_model": DEFAULT_HF_MODEL,
            "available": _has_transformers(),
            "configured_model": os.getenv("ARLAW_HF_MODEL", "default"),
            "allowed_tasks": sorted(HF_ALLOWED_TASKS),
            "allowed_models": [x.strip() for x in os.getenv("ARLAW_HF_ALLOWED_MODELS", "").split(",") if x.strip()],
        },
        "note": (
            "Optional models load only when invoked. MobileNetV2 and ResNet-50 use TensorFlow Hub; "
            "VGG-16 uses Keras Applications. These classify ImageNet objects and do not perform OCR, "
            "legal-document understanding or legal reasoning. The default Hugging Face model is "
            "sentiment analysis, not a legal-answer model. Legal answers remain governed by the "
            "separate jurisdiction-matched retrieval and evidence gate."
        ),
    }


@lru_cache(maxsize=2)
def _hub_model(handle: str):
    try:
        import tensorflow_hub as hub
    except ImportError as exc:
        raise RuntimeError("Install optional TensorFlow Hub dependencies: pip install -r requirements-ml.txt") from exc
    return hub.load(handle)


@lru_cache(maxsize=1)
def _vgg16_model():
    try:
        from tensorflow.keras.applications import VGG16
    except ImportError as exc:
        raise RuntimeError("Install optional vision dependencies: pip install -r requirements-ml.txt") from exc
    return VGG16(weights="imagenet")


def classify_image(name: str, image_bytes: bytes):
    import io
    try:
        import numpy as np
        import tensorflow as tf
        from PIL import Image
        from tensorflow.keras.applications.vgg16 import decode_predictions, preprocess_input
        from tensorflow.keras.utils import img_to_array
    except ImportError as exc:
        raise RuntimeError("Install optional vision dependencies: pip install -r requirements-ml.txt") from exc
    if name not in VISION_MODELS:
        raise ValueError("Unsupported vision model")
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB").resize((224, 224))
    x = img_to_array(image)[None, ...].astype("float32")
    if name == "vgg16":
        predictions = _vgg16_model().predict(preprocess_input(x), verbose=0)
    else:
        classifier = _hub_model(VISION_MODELS[name]["handle"])
        # TensorFlow Hub's image-classification tutorial expects float images in [0, 1].
        predictions = classifier(tf.convert_to_tensor(x / 255.0))
        if isinstance(predictions, dict):
            predictions = next(iter(predictions.values()))
        if isinstance(predictions, (tuple, list)):
            predictions = predictions[0]
        predictions = tf.nn.softmax(predictions, axis=-1).numpy()
    # ImageNet labels are only generic object classes, never legal-document labels.
    try:
        decoded = decode_predictions(np.asarray(predictions), top=5)[0]
    except Exception as exc:
        raise RuntimeError("The selected model returned an unsupported ImageNet output shape") from exc
    return [{"label": label, "confidence": float(score)} for _, label, score in decoded]


@lru_cache(maxsize=4)
def _hf_pipeline(task: str, model: str):
    try:
        from transformers import pipeline
    except ImportError as exc:
        raise RuntimeError("Install optional NLP dependencies: pip install -r requirements-ml.txt") from exc
    return pipeline(task=task, model=model, trust_remote_code=False)


def run_hf_text(
    text: str,
    task: str = "sentiment-analysis",
    model: str | None = None,
    candidate_labels: list[str] | None = None,
):
    if task not in HF_ALLOWED_TASKS:
        raise ValueError("Unsupported Hugging Face task")
    if not text or len(text) > 12000:
        raise ValueError("Text must contain 1–12000 characters")
    selected = (model or DEFAULT_HF_MODEL).strip()
    if not selected or len(selected) > 256:
        raise ValueError("Invalid Hugging Face model identifier")
    allowlist = {x.strip() for x in os.getenv("ARLAW_HF_ALLOWED_MODELS", "").split(",") if x.strip()}
    if allowlist and selected not in allowlist:
        raise ValueError("Model is not in ARLAW_HF_ALLOWED_MODELS")
    if task == "zero-shot-classification":
        labels = [str(x).strip() for x in (candidate_labels or []) if str(x).strip()]
        if len(labels) < 2 or len(labels) > 20:
            raise ValueError("Zero-shot classification requires 2–20 candidate_labels")
        result = _hf_pipeline(task, selected)(text, candidate_labels=labels)
    else:
        result = _hf_pipeline(task, selected)(text)
    return {
        "task": task,
        "model": selected,
        "result": result,
        "warning": "Hugging Face output is an auxiliary NLP prediction, not legal advice or verified legal analysis.",
    }
