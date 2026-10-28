# Job Hunt Copilot — Phase 1: Single Agent

A hand-built agent loop (no framework) with 4 tools. Learn how agents work before LangGraph hides it.

## Setup (5 min)

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
copy .env.example .env         # Mac/Linux: cp .env.example .env
```

1. Put your Anthropic API key in `.env` (console.anthropic.com → API Keys; add ~$5 credit).
2. Paste your resume text into `resume.txt`.
3. Optional: free Adzuna keys (developer.adzuna.com) for real jobs. Without them it uses `sample_jobs.json`.

## Run

```bash
python agent.py "Find React or full-stack fresher jobs in Hyderabad"
```

Watch the terminal: 🔧 = tool call, ↳ = tool result, 💭 = agent thinking. Results land in `shortlist.csv`.

## Files

| File | What it teaches |
|---|---|
| `agent.py` | **The agent loop**: LLM → tool request → run tool → result back → repeat |
| `tools.py` | **Tool calling**: Python function + JSON schema the LLM reads |
| `SYSTEM_PROMPT` in agent.py | **Planning**: the step-by-step process the agent follows |
| `messages` list | **Short-term memory**: the whole conversation, resent every step |
| `MAX_STEPS`, try/except in `run_tool` | **Guardrails**: agents must fail safely |

## Exercises (do these before Phase 2)

1. **Add a tool**: `get_salary_estimate(role)` — return a hard-coded dict. Add the schema, the function, register it, and ask the agent about salaries.
2. **Break it**: make `fetch_job_description` always return an error. Does the agent adapt and use the snippet?
3. **Change the plan**: edit `SYSTEM_PROMPT` so it only shortlists jobs scoring ≥ 70. Observe the difference.
4. **Count cost**: print `response.usage.input_tokens` each step. Notice it grows — the whole history is resent every time.

## Next: Phase 2

RAG over your resume and projects (embeddings + vector search), and tailored resume bullets per job.
