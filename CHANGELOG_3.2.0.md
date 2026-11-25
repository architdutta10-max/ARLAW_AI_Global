# ARLAW AI Global 3.2.0

## Added
- Optional MobileNet, ResNet-50 and VGG-16 image classification through `tf.keras.applications` with ImageNet weights and lazy model loading.
- Optional Hugging Face Transformers inference endpoint with configurable model ID and task allow-list.
- Model catalog endpoint at `GET /api/models`.
- Chat history multi-select deletion, select-all and clear-all controls, including responsive mobile visibility.

## Reliability and deployment
- TensorFlow, PyTorch, Transformers and Pillow are isolated in `requirements-ml.txt`; the default web deployment remains lightweight.
- Model routes return actionable dependency errors if optional packages are not installed.
- Image uploads are limited to JPEG/PNG/WebP and 8 MB.
- Existing individual chat deletion remains available.

## Accuracy and limitations
- The vision models are image classifiers, not legal reasoning models.
- The default Hugging Face model is a general sentiment classifier, not a legal model. Set `ARLAW_HF_MODEL` to a compatible model for another NLP task.
- These integrations do not train a new legal foundation model or independently verify legal authorities.
- Legal answer quality still depends on the relevance, completeness and currency of retrieved primary sources and the configured LLM provider. No legal accuracy percentage is claimed or certified.
- Chat history remains browser-local and is not synchronized across browsers or devices. Deleting browser-local history removes it from that browser's stored ARLAW data.


## 3.2.0 legal retrieval and model integration expansion

- MobileNetV2 and ResNet-50 now use explicit TensorFlow Hub ImageNet classification handles; VGG-16 uses TensorFlow Keras Applications because a corresponding maintained VGG-16 classification handle is not provided in the TensorFlow Hub image-classification model list.
- Added Hugging Face task support for text classification, zero-shot classification, token classification/NER and feature extraction. Optional model allowlisting is available through `ARLAW_HF_ALLOWED_MODELS`; remote custom model code is disabled.
- Added Indian statutory retrieval guides and official-source metadata for BNS, BNSS, BSA, DPDP Act, DPDP Rules 2025, DPDP commencement notification, Limitation Act 1963 and its Schedule, Indian Contract Act 1872 (Sections 2, 19, 22 and 23), Income-tax Act 2025, Income-tax Rules 2026 and official Tax Year 2026-27 guidance.
- Added `scripts/refresh_indian_legal_corpus.py` to fetch and index complete official PDFs/HTML documents from a fixed allowlist. It is operator-invoked, not run at service startup.
- Important: bundled records are retrieval guides and not complete reproductions of the statutes. Run the refresh script to index the complete source documents; inspect its report and verify subsequent Gazette amendments.
- TensorFlow Hub models are generic ImageNet object classifiers, not OCR or legal-document models. Hugging Face output is auxiliary NLP, not a legal-answer model.
- No claim of legal-accuracy certification, production certification or security audit is made.


### Retrieval coverage hotfix (3.2.0)

- Numbered research sections now recognise escaped Markdown numbering such as `1\.` so each question is routed and retrieved independently.
- Indian jurisdiction detection now recognises the BNS, BNSS, BSA, DPDP Act, Limitation Act, 1963 and Indian Contract Act by their named instruments.
- The full official Indian legal corpus still requires an explicit refresh; it is not fetched automatically at startup or during Render builds.
- Added regression tests for seven-question routing and Render corpus refresh configuration.
