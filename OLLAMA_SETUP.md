# Ollama setup for ARLAW AI

1. Install and start the Ollama application for your operating system.
2. Open a terminal and download the configured model:

   ```bash
   ollama pull qwen3:8b
   ```

3. In the ARLAW project, copy `.env.example` to `.env` if you have not already done so.
4. Set:

   ```dotenv
   OLLAMA_ENABLED=true
   OLLAMA_BASE_URL=http://127.0.0.1:11434
   OLLAMA_MODEL=qwen3:8b
   ARLAW_PROVIDER_ORDER=ollama,groq
   ```

5. Optionally add `GROQ_API_KEY` to enable cloud fallback.
6. Start ARLAW with `python run.py`; check `/api/health/model` to see configured providers.

The default order tries Ollama first and Groq second. Use `ARLAW_PROVIDER_ORDER=groq,ollama` to prefer Groq. Ollama must be running locally. A local model's speed depends on available system memory and hardware.
