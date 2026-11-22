# Optional LoRA training

Fine-tuning is optional; ARLAW runs without it. Prefer retrieval over repeatedly fine-tuning
changing law. Use only lawfully obtained, expert-reviewed, non-confidential examples. Split train,
validation and test data by case/source and time to avoid leakage. Test citation validity,
jurisdiction recognition, effective-date awareness, multilingual performance and uncertainty.
Free GPU availability is not guaranteed. This starter does not create a professional legal expert.


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

The application keeps local Ollama as a development fallback when `GROQ_API_KEY` is absent.
