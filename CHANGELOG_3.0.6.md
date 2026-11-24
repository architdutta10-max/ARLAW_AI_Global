# ARLAW AI 3.0.6 — jurisdiction and retrieval correction

- India is now the explicit initial jurisdiction in the chat and knowledge-library upload controls. Users can still choose GLOBAL or another listed jurisdiction.
- The chat API and document-upload endpoint default to `IN` when a client omits the jurisdiction field, matching the India-focused product default.
- Long structured prompts retain named authorities that occur after the first 16 search terms; retrieval now considers up to 32 distinct terms.
- Added regression tests for the Article 21 / Maneka Gandhi structured prompt and the India default.

This patch does not add new legal authorities or independently validate the truth of model-generated legal propositions. It fixes jurisdiction selection and retrieval of sources already bundled with the project.
