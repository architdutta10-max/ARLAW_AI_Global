# ARLAW AI cloud inference architecture

## Active provider configuration

This release uses **Groq only** for hosted inference. Gemini, Ollama and generic OpenAI-compatible provider adapters are removed from runtime routing. No local model runtime or model download is required.

- Provider: Groq Chat Completions API.
- Credential: `GROQ_API_KEY`, loaded server-side from `.env` or deployment environment.
- Model: configured by `GROQ_MODEL` (default `openai/gpt-oss-20b`).
- Task classification continues to select specialist system instructions; it does not switch providers.
- Independent multi-model peer review is disabled because only one provider is active.

## Local setup

1. Copy `.env.example` to `.env`.
2. Set `GROQ_API_KEY` in `.env`.
3. Install dependencies with `python -m pip install -r requirements.txt`.
4. Start directly with `python run.py` (no batch file required).

Never commit `.env` or expose API keys in browser JavaScript, screenshots or logs.

## Legal source verification boundary

ARLAW retrieves indexed materials and validates that cited source labels exist. It does not establish that a cited passage legally supports every proposition, verify live amendments, check court-status histories, or resolve conflicting authorities automatically. These require source-specific parsers, official-source ingestion, effective-date tracking and expert evaluation. Do not describe citation-reference validation as legal verification.

## Multilingual boundary

The prompt layer supports multilingual responses, but FTS5 lexical search is not a semantic multilingual search engine. For stronger Hindi/Bengali/global retrieval, add multilingual embeddings and a tested reranker, retain original-language passages, and evaluate per jurisdiction/language. Never translate a statutory phrase silently when the original wording matters.

## Training and distillation policy

Use the LoRA/QLoRA trainer for expert-approved supervised examples. For teacher/student distillation, prepare teacher outputs with `training/build_distillation.py`; the script accepts only examples marked `approved` with source IDs and teacher model provenance. Review legal examples by qualified domain experts before training. Split evaluation by source/case and time to reduce leakage. Keep changing law in retrieval, not model weights. Confirm model and dataset licences before use or distribution.

## Deployment

For hosted deployment, configure `GROQ_API_KEY` only through the hosting provider's secret/environment settings. Free-tier limits and provider availability can change.
