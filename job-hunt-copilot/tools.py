"""
tools.py — the agent's "hands".

Each tool is a normal Python function. The LLM never runs these itself:
it only *asks* for a tool by name, and agent.py runs the function and
sends the result back.

Every tool has two parts:
  1. The Python function (what actually happens)
  2. A schema in TOOL_SCHEMAS (how the LLM learns the tool exists)
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).parent
RESUME_PATH = BASE_DIR / "resume.txt"
SHORTLIST_PATH = BASE_DIR / "shortlist.csv"
SAMPLE_JOBS_PATH = BASE_DIR / "sample_jobs.json"

ADZUNA_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"


# ---------------------------------------------------------------- tools

def search_jobs(role: str, location: str = "Hyderabad", limit: int = 8) -> dict:
    """Search job listings. Uses Adzuna if keys are set, else sample data."""
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        jobs = json.loads(SAMPLE_JOBS_PATH.read_text(encoding="utf-8"))
        words = role.lower().split()
        hits = [j for j in jobs if any(w in j["title"].lower() for w in words)]
        return {"source": "sample_data", "count": len(hits[:limit]), "jobs": hits[:limit]}

    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": role,
        "where": location,
        "results_per_page": limit,
        "content-type": "application/json",
    }
    resp = requests.get(ADZUNA_URL.format(country="in"), params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    jobs = [
        {
            "id": str(r.get("id")),
            "title": r.get("title", ""),
            "company": (r.get("company") or {}).get("display_name", "Unknown"),
            "location": (r.get("location") or {}).get("display_name", ""),
            "url": r.get("redirect_url", ""),
            "snippet": (r.get("description") or "")[:500],
        }
        for r in data.get("results", [])
    ]
    return {"source": "adzuna", "count": len(jobs), "jobs": jobs}


def fetch_job_description(url: str) -> dict:
    """Download a job page and return its visible text (trimmed)."""
    if url.startswith("sample://"):
        jobs = json.loads(SAMPLE_JOBS_PATH.read_text(encoding="utf-8"))
        for j in jobs:
            if j["url"] == url:
                return {"url": url, "text": j["full_description"]}
        return {"error": "sample job not found"}

    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except requests.RequestException as e:
        # Tools should return errors, not crash — the agent can decide what to do.
        return {"error": f"Could not fetch page: {e}. Use the search snippet instead."}

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    return {"url": url, "text": text[:4000]}  # trim so we don't blow up the prompt


def read_resume() -> dict:
    """Return the candidate's resume text."""
    if not RESUME_PATH.exists():
        return {"error": "resume.txt not found"}
    return {"resume": RESUME_PATH.read_text(encoding="utf-8")}


def save_shortlist(jobs: list) -> dict:
    """Append scored jobs to shortlist.csv (our simple tracker)."""
    new_file = not SHORTLIST_PATH.exists()
    fields = ["saved_at", "title", "company", "score", "reason", "missing_skills", "url"]
    with SHORTLIST_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new_file:
            w.writeheader()
        for j in jobs:
            w.writerow({
                "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "title": j.get("title", ""),
                "company": j.get("company", ""),
                "score": j.get("score", ""),
                "reason": j.get("reason", ""),
                "missing_skills": ", ".join(j.get("missing_skills", [])),
                "url": j.get("url", ""),
            })
    return {"saved": len(jobs), "file": SHORTLIST_PATH.name}


# --------------------------------------------- schemas the LLM reads

TOOL_SCHEMAS = [
    {
        "name": "search_jobs",
        "description": "Search current job listings in India for a role and city. Returns title, company, url and a short snippet for each job.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role": {"type": "string", "description": "Job title or keywords, e.g. 'React developer'"},
                "location": {"type": "string", "description": "City, e.g. 'Hyderabad'"},
                "limit": {"type": "integer", "description": "Max results (1-15)"},
            },
            "required": ["role"],
        },
    },
    {
        "name": "fetch_job_description",
        "description": "Fetch the full text of a job posting from its url. Use this before scoring a job you are seriously considering.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
    },
    {
        "name": "read_resume",
        "description": "Read the candidate's resume. Call this before scoring any job.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "save_shortlist",
        "description": "Save the final scored shortlist to the tracker. Call once at the end.",
        "input_schema": {
            "type": "object",
            "properties": {
                "jobs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "company": {"type": "string"},
                            "url": {"type": "string"},
                            "score": {"type": "integer", "description": "Fit score 0-100"},
                            "reason": {"type": "string", "description": "One sentence on why"},
                            "missing_skills": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": ["title", "company", "score", "reason"],
                    },
                }
            },
            "required": ["jobs"],
        },
    },
]

# Name -> function. agent.py uses this to run whatever the LLM asks for.
TOOL_FUNCTIONS = {
    "search_jobs": search_jobs,
    "fetch_job_description": fetch_job_description,
    "read_resume": read_resume,
    "save_shortlist": save_shortlist,
}


def run_tool(name: str, args: dict) -> str:
    """Run a tool by name and return its result as a JSON string."""
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool {name}"})
    try:
        return json.dumps(fn(**args), ensure_ascii=False)
    except Exception as e:  # never let one bad tool call crash the agent
        return json.dumps({"error": f"{type(e).__name__}: {e}"})
