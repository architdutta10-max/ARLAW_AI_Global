# ARLAW AI Global

**An AI-assisted legal information platform designed to make legal knowledge easier to explore.**

- **Live application:** https://arlaw-ai-global.onrender.com
- **GitHub repository:** https://github.com/architdutta10-max/ARLAW_AI_Global

---

## Overview

ARLAW AI Global is an AI-powered application for exploring legal, civil, and economic topics through a conversational interface. It uses a hosted language model through the Groq API to generate responses.

The project is intended as an informational and educational technology tool. It is **not a law firm, does not provide legal representation, and is not a substitute for advice from a qualified lawyer**.

## Project information

| Item | Details |
|---|---|
| Project | ARLAW AI Global |
| Developer | Archit Dutta |
| Location | Siliguri, West Bengal, India |
| AI provider | Groq API |
| Configured model | `openai/gpt-oss-20b` |
| Application framework | FastAPI |
| Hosting | Render |

## Live demo

Visit **https://arlaw-ai-global.onrender.com** to try the deployed application.

The service may take a short time to wake up after a period of inactivity.

## Technology

- Python
- FastAPI
- Groq API
- `openai/gpt-oss-20b`
- Render

## Run locally

### 1. Clone the repository

```bash
git clone https://github.com/architdutta10-max/ARLAW_AI_Global.git
cd ARLAW_AI_Global
```

### 2. Create and activate a virtual environment

**Windows Command Prompt:**

```cmd
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

If the repository includes `requirements.txt`, run:

```bash
pip install -r requirements.txt
```

### 4. Configure the API key

Set the `GROQ_API_KEY` environment variable to your own Groq API key.

**Windows Command Prompt (current session):**

```cmd
set GROQ_API_KEY=your_groq_api_key
```

**macOS / Linux:**

```bash
export GROQ_API_KEY="your_groq_api_key"
```

Never commit API keys, passwords, or other secrets to GitHub. For Render, add `GROQ_API_KEY` under the service's **Environment** settings.

### 5. Start the application

The FastAPI application entry point is `app.main:app`. If Uvicorn is included in the project's dependencies, run:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000.

If the repository's current dependency file or start command differs, follow the configuration included in the repository.

## Deployment

The application is deployed on Render:

https://arlaw-ai-global.onrender.com

When deploying from GitHub, connect the repository to Render and configure the required environment variable:

| Environment variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Authenticates requests to the Groq API |

Keep this key private. Do not place it in source code, README files, screenshots, or public issue reports.

## Responsible use and legal disclaimer

AI-generated information may be incomplete, outdated, or incorrect. Laws and legal procedures vary by jurisdiction and change over time.

- Verify important information against current official legislation, regulations, and court or government sources.
- Consult a qualified legal professional about a real case, legal rights, deadlines, contracts, or court proceedings.
- Do not rely on generated output as the sole basis for legal, financial, or other high-impact decisions.
- Do not submit confidential, privileged, or sensitive personal information unless you understand and accept the application's data-handling arrangements.

**Using this application does not create a lawyer-client relationship.**

## Contributing

Suggestions, bug reports, and improvements are welcome. Please open an issue in the GitHub repository before proposing substantial changes.

For pull requests:
1. Explain the purpose of the change.
2. Keep API keys and other secrets out of the code.
3. Include relevant testing or reproduction steps.

## Developer

**Archit Dutta**  
Siliguri, West Bengal, India

- **GitHub:** https://github.com/architdutta10-max
- **LinkedIn:** https://www.linkedin.com/in/archit-dutta-4522693aa/
- **Instagram:** https://www.instagram.com/architdutta17/
- **Email:** architdutta10@gmail.com

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
