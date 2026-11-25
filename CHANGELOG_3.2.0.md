# ARLAW AI Global 3.2.0

## Added
- Optional MobileNet, ResNet-50 and VGG-16 image classification through `tf.keras.applications` with ImageNet weights and lazy model loading.
- Optional Hugging Face Transformers inference endpoint with configurable model ID and task allow-list.
- Model catalog endpoint at `GET /api/models`.
- Hugging Face model IDs are restricted to the configured default and `ARLAW_HF_ALLOWED_MODELS`; callers cannot request arbitrary model downloads.
- Chat history multi-select deletion, select-all and clear-all controls, including responsive mobile visibility.

## Reliability and deployment
- TensorFlow, PyTorch, Transformers and Pillow are isolated in `requirements-ml.txt`; the default web deployment remains lightweight.
- Model routes return actionable dependency errors if optional packages are not installed.
- Image uploads are limited to JPEG/PNG/WebP and 8 MB.
- Existing individual chat deletion remains available.
- Removed the unused legacy `history.js` file; the active browser-local history implementation is `app.js`.

## Accuracy and limitations
- The vision models are image classifiers, not legal reasoning models.
- The default Hugging Face model is a general sentiment classifier, not a legal model. Set `ARLAW_HF_MODEL` to a compatible default and add permitted model IDs as a comma-separated `ARLAW_HF_ALLOWED_MODELS` value. Only allow models you trust and have capacity to download. The vision backbones use `tf.keras.applications` (not TensorFlow Hub).
- These integrations do not train a new legal foundation model or independently verify legal authorities.
- Legal answer quality still depends on the relevance, completeness and currency of retrieved primary sources and the configured LLM provider. No legal accuracy percentage is claimed or certified.
- Chat history remains browser-local and is not synchronized across browsers or devices. Deleting browser-local history removes it from that browser's stored ARLAW data.
