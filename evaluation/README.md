# Evaluation before release

Test by jurisdiction, court level, language and effective date. Measure:
- jurisdiction identification and clarification;
- whether each citation exists and supports the proposition;
- amendment/effective-date correctness;
- binding vs persuasive authority;
- calibrated uncertainty when sources are missing;
- multilingual fidelity;
- privacy and prompt-injection resistance;
- tax year and accounting standard identification.

Do not evaluate only fluency. Have qualified professionals independently review test answers.


## Free hosted AI (Groq)

The app can use Groq's OpenAI-compatible hosted inference API. Groq offers a free tier
with model-specific rate and token limits; it is not unlimited and limits can change.

1. Create an account at https://console.groq.com/.
2. Create an API key at https://console.groq.com/keys.
3. In Render, open the `arlaw-ai-global` web service.
4. Open **Environment** and add `GROQ_API_KEY` with your secret key as the value.
5. Ensure `GROQ_MODEL` is set to `openai/gpt-oss-20b`.
6. Save changes and redeploy if Render does not redeploy automatically.

Never put the API key in GitHub, source code, screenshots, or browser JavaScript.
The key must be stored only as a Render environment variable. Free usage is subject to
provider limits, availability, and data-use terms. Do not send privileged, confidential,
or sensitive client information to a free-tier provider unless its terms and your
professional obligations permit it.

This release is Groq-only. If `GROQ_API_KEY` is absent, AI responses are unavailable; the app does not silently switch to a local model.
