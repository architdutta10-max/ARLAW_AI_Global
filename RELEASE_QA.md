# ARLAW AI Global 3.2.0 — Release QA

## Automated checks

- `python -m pytest -q`: 140 passed in the audited source tree.
- `node --check app/static/app.js`: passed.
- `python -m compileall -q app tests`: passed.
- Optional model routes and lazy imports are covered by source-level regression tests.
- Chat-history controls and the single active browser-local history script are covered by regression tests.

## Scope and limitations

- Chat history is stored in this browser's local storage. Individual, selected and clear-all deletion affect only this browser; there is no server-side history or cross-device synchronization.
- The history UI has passed source and syntax checks, but a full interactive browser test is still required on the target deployment.
- MobileNet, ResNet-50 and VGG-16 are implemented with `tf.keras.applications`, not TensorFlow Hub.
- TensorFlow/PyTorch/Transformers/Pillow remain optional and are not installed by the default Render build. The optional model endpoints will report missing dependencies until the ML requirements are installed in an adequately resourced environment.
- The default Hugging Face model is a general sentiment classifier, not a legal-answer model.
- Retrieval tests validate source discovery and routing only. They do not validate generated legal answers, legal correctness, source authenticity, or current validity.
- No independent legal-professional review or statistically validated accuracy benchmark has been completed. No legal accuracy percentage is claimed.
- This release is not production-certified or independently security-audited, and has not been pushed to GitHub or deployed to Render.
