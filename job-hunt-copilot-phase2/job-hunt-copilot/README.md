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

---

# Phase 2: RAG + Tailored Resumes

The agent now searches your **knowledge base** (detailed project notes) by meaning, and writes resume bullets tailored to each job — every bullet must cite its source.

## Setup

```bash
pip install -r requirements.txt      # adds chromadb
```

1. Write your projects in `knowledge/projects/*.md` (see `knowledge/README.md`). Delete the example file.
2. Build the index: `python rag.py index` (first run downloads an ~80 MB embedding model once).
3. Test retrieval: `python rag.py search "REST API design"`
4. Run the agent as before. Tailored bullets land in `output/tailored/`.

## How it works

```
knowledge/*.md ─chunk by ## heading─> chunks ─embed─> vectors ─> ChromaDB (.chroma/)
job requirement ─embed─> vector ─nearest neighbours─> top chunks + source_ids ─> LLM writes bullets
```

| File | What it teaches |
|---|---|
| `rag.py` `chunk_file` | **Chunking**: split text into focused, searchable pieces |
| `rag.py` `build_index` | **Embeddings + vector DB**: text → numbers → stored |
| `rag.py` `search` | **Retrieval**: find chunks closest in meaning, not exact words |
| `tools.py` `save_tailored_resume` | **Grounding guardrail**: bullets with no real source are rejected |
| `knowledge/` | **Long-term memory**: facts about you that persist across runs |

## Phase 2 exercises

1. **Semantic search**: search `"database indexing"` when your notes say `"added indexes on barcode"`. It still matches — that's embeddings, not keyword search.
2. **Chunk size**: put a whole project under one `##` heading. Re-index and compare search quality. Why is it worse?
3. **Relevance threshold**: in `search_profile`, drop results with `distance` above some value so weak matches don't sneak in. Find a good cut-off by testing.
4. **Break the guardrail**: ask the agent to "make the resume sound more senior". Watch the rejections in the terminal.

## Next: Phase 3

Rebuild the agent in **LangGraph** and split it into multiple agents (Scout, Matcher, Writer) coordinated by a supervisor.
