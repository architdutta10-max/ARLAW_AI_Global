# ARLAW AI integrated hybrid architecture

## Implemented in this repository

- **Provider adapters:** Groq, local Ollama and an optional OpenAI-compatible endpoint. Credentials stay server-side.
- **Fallback orchestration:** configured provider order with per-task overrides (`ARLAW_ROUTE_*`). Failed or empty providers fall through.
- **Specialist task routing:** legal research, civil procedure, finance/tax, document review, translation and general research receive different system instructions.
- **Multilingual prompting:** the requested response language is preserved; English, Hindi, Bengali and mixed-language prompts are explicitly supported. Actual quality depends on the chosen model and indexed corpus.
- **Optional independent peer review:** `ARLAW_MULTI_MODEL_REVIEW=true` asks other configured providers to review the primary draft concurrently. Their review is shown separately and is not treated as a vote, consensus, or proof.
- **Citation-reference validation:** checks whether each `[S#]` used in the response exists in the retrieved source set. This verifies reference existence only, not whether the source substantively proves the claim.
- **Knowledge base:** existing SQLite/FTS5 store remains in place, with jurisdiction, authority, language, URL and as-of metadata.
- **Training:** existing QLoRA/SFT pipeline plus a provenance/approval-gated teacher-output distillation preparation script.
- **Evaluation:** API smoke runner and tests for routing, fallback and citation-reference checks.

## Task-specific routing

Set one or more variables in `.env` or the deployment environment:

```env
ARLAW_PROVIDER_ORDER=groq,ollama,openai_compatible
ARLAW_ROUTE_LEGAL_RESEARCH=groq,ollama
ARLAW_ROUTE_CIVIL_PROCEDURE=groq,ollama
ARLAW_ROUTE_FINANCE_TAX=groq,ollama
ARLAW_ROUTE_DOCUMENT_REVIEW=groq,ollama
ARLAW_ROUTE_TRANSLATION=ollama,groq
ARLAW_ROUTE_GENERAL=groq,ollama
```

Only adapters that are configured and reachable will work. The route sets provider priority; it does not claim that a provider has been trained as a lawyer or domain specialist.

## Multi-model review

Enable with `ARLAW_MULTI_MODEL_REVIEW=true`. The primary model drafts the answer; up to two other providers independently review it. Reviewers can disagree or be wrong. Their text is explicitly separated from the primary response. Keep this disabled if latency, provider limits, or data-handling terms make parallel review unsuitable.

## Legal source verification boundary

ARLAW currently performs retrieval and validates that cited source labels exist. It does **not** yet establish that a cited passage legally supports every proposition, verify live amendments, check court-status histories, or resolve conflicting authorities automatically. Those require source-specific parsers, official-source ingestion, effective-date tracking and expert evaluation. Do not describe citation-reference validation as legal verification.

## Multilingual boundary

The prompt layer supports multilingual responses, but FTS5 lexical search is not a semantic multilingual search engine. For stronger Hindi/Bengali/global retrieval, add multilingual embeddings and a tested reranker, retain original-language passages, and evaluate per jurisdiction/language. Never translate a statutory phrase silently when the original wording matters.

## Training and distillation policy

Use the LoRA/QLoRA trainer for expert-approved supervised examples. For teacher/student distillation, prepare teacher outputs with `training/build_distillation.py`; the script accepts only examples marked `approved` with source IDs and teacher model provenance. Review legal examples by qualified domain experts before training. Split evaluation by source/case and time to reduce leakage. Keep changing law in retrieval, not model weights. Confirm model and dataset licences before use or distribution.

## Deployment

Render remains supported. Add provider keys only through Render Environment settings. Ollama is usually a local development option; a Render free web service cannot access a developer's localhost Ollama. For local-only use set `ARLAW_PROVIDER_ORDER=ollama`. No paid provider is required, but free tiers, GPU availability and local compute are limited.
