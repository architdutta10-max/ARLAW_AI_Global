# ARLAW AI Global 3.2.0 — Release QA

## Automated checks

- `python -m pytest -q`: **145 passed** in the local build environment.
- `python -m compileall -q app tests scripts`: passed.
- `node --check app/static/app.js`: passed.
- Added regression checks for BNS, BNSS, BSA, separate DPDP Act/Rules/commencement records, Limitation Act Schedule retrieval, Contract Act sections 22/23 separation, Tax Year 2026-27 sources, Hugging Face zero-shot labels and model allowlisting.

## Model integration

- MobileNetV2 and ResNet-50 use TensorFlow Hub ImageNet classification handles.
- VGG-16 uses TensorFlow Keras Applications; a matching maintained VGG-16 classification handle is not listed in the official TensorFlow Hub image-classification tutorial.
- Hugging Face supports text classification, zero-shot classification, token classification/NER and feature extraction. Optional dependencies remain outside the default install.
- Model downloads and real inference were not executed in this lightweight QA environment; verify on a machine with the optional ML dependencies and adequate RAM/disk.

## Indian legal retrieval coverage

- Bundled retrieval guides and official-source metadata cover BNS, BNSS, BSA, DPDP Act, DPDP Rules 2025, DPDP commencement notification G.S.R. 843(E), Limitation Act 1963 including Schedule, Indian Contract Act 1872 sections 2, 19, 22 and 23, Income-tax Act 2025, Income-tax Rules 2026 and official Income Tax Department Tax Year 2026-27 guidance.
- `scripts/refresh_indian_legal_corpus.py` fetches complete official documents from a fixed HTTPS allowlist and indexes them into SQLite when explicitly run by the operator. It has not been run in this build environment; the bundled guides are not full reproductions of those statutes. The Render free filesystem is ephemeral, so a local refresh does not update the hosted database. A durable hosted corpus requires a persistent data volume or a build-time packaged corpus.
- Retrieval tests validate source discovery and routing only. They do not certify generated legal answers, statutory completeness, source authenticity, legal correctness or current validity.

## Limitations

- TensorFlow Hub/Keras vision models classify generic ImageNet objects; they are not OCR or legal-document understanding systems.
- The default Hugging Face model is general sentiment analysis, not a legal-answer model. Hugging Face output does not bypass the legal evidence gate.
- Browser-local chat-history deletion is not server-side deletion or cross-device synchronization.
- No independent legal-professional review, statistically validated legal-accuracy benchmark, production certification or security audit has been completed.
