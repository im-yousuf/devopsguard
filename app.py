"""
DevOpsGuard — Web UI
====================
Flask server that streams the full 4-phase demo to the browser via
Server-Sent Events (SSE). Each phase emits structured JSON events that
the frontend renders as beautiful cards, tables, and badges.

Run:
    python app.py
Then open: http://localhost:5000
"""

import json
import threading
import time
import markdown2
import re
from flask import Flask, Response, render_template, stream_with_context
from demo import (
    HISTORICAL_INCIDENTS,
    LIVE_ERROR,
    LIVE_ERROR_2,
    STRATEGIC_QUERY,
)
import agent

app = Flask(__name__)

# ── SSE helper ──────────────────────────────────────────────────────────────

def sse(event: str, data: dict) -> str:
    """Format a Server-Sent Event frame."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def md_to_html(text: str) -> str:
    """Convert markdown (with tables) to HTML."""
    return markdown2.markdown(
        text,
        extras=["tables", "fenced-code-blocks", "strike", "header-ids"],
    )


# ── Demo runner (generator) ──────────────────────────────────────────────────

def run_demo():
    """
    Generator that yields SSE frames for every step of the demo.
    Runs synchronously so output arrives in order.
    """

    # ── PHASE 0 ─────────────────────────────────────────────────────────────
    yield sse("phase", {"id": 0, "title": "Initialise Memory Bank",
                        "icon": "⚙️", "status": "running"})
    try:
        agent.setup_bank()
        yield sse("log",  {"phase": 0, "text": "Memory bank devops-incidents is ready."})
        yield sse("phase_done", {"id": 0})
    except Exception as e:
        yield sse("error", {"phase": 0, "text": str(e)})
        return

    time.sleep(0.4)

    # ── PHASE 1 — BEFORE ────────────────────────────────────────────────────
    yield sse("phase", {"id": 1, "title": "Before — Empty Memory Bank",
                        "icon": "📭", "status": "running"})
    yield sse("error_card", {
        "phase": 1,
        "label": "Live Error",
        "severity": "critical",
        "text": LIVE_ERROR,
    })

    # recall
    yield sse("log", {"phase": 1, "text": "Querying Hindsight memory bank…"})
    memories = agent.recall_similar_incidents(LIVE_ERROR)
    if memories:
        yield sse("memory_badge", {"phase": 1, "count": len(memories), "found": True})
    else:
        yield sse("memory_badge", {"phase": 1, "count": 0, "found": False})

    # diagnose
    yield sse("log", {"phase": 1, "text": "Generating AI diagnosis via Groq…"})
    diagnosis = agent.diagnose_error(LIVE_ERROR)
    yield sse("diagnosis", {
        "phase": 1,
        "html": md_to_html(diagnosis),
        "label": "Diagnosis — No Memory",
        "variant": "before",
    })
    yield sse("observation", {
        "phase": 1,
        "text": "With no memory context the agent gives generic SRE textbook advice — "
                "no specific past incidents are cited.",
    })
    yield sse("phase_done", {"id": 1})
    time.sleep(0.4)

    # ── PHASE 2 — RETAIN ────────────────────────────────────────────────────
    yield sse("phase", {"id": 2, "title": "Retain — Ingesting Post-Mortems",
                        "icon": "📥", "status": "running"})
    yield sse("log", {"phase": 2,
                      "text": f"Loading {len(HISTORICAL_INCIDENTS)} historical incidents…"})

    rows = []
    for inc in HISTORICAL_INCIDENTS:
        agent.retain_incident(
            incident_id=inc["incident_id"],
            error_log=inc["error_log"],
            resolution=inc["resolution"],
            metadata=inc["metadata"],
        )
        rows.append({
            "id":       inc["incident_id"],
            "service":  inc["metadata"]["service"],
            "severity": inc["metadata"]["severity"],
            "team":     inc["metadata"]["team"],
            "error":    inc["error_log"],
            "fix":      inc["resolution"],
        })
        yield sse("incident_row", {"phase": 2, "row": rows[-1]})
        time.sleep(0.8)

    yield sse("retain_done", {
        "phase": 2,
        "count": len(rows),
        "bank":  agent.BANK_ID,
    })
    yield sse("phase_done", {"id": 2})
    time.sleep(0.4)

    # ── PHASE 3 — AFTER ─────────────────────────────────────────────────────
    yield sse("phase", {"id": 3, "title": "After — Memory-Augmented Diagnosis",
                        "icon": "📬", "status": "running"})

    for idx, error in enumerate([LIVE_ERROR, LIVE_ERROR_2]):
        label   = "Redis OOM — Auth Service" if idx == 0 else "Postgres Pool — Orders Service"
        sev     = "critical" if idx == 0 else "high"
        yield sse("error_card", {"phase": 3, "label": label, "severity": sev, "text": error})

        yield sse("log", {"phase": 3, "text": f"Recalling past incidents for: {label}…"})
        memories = agent.recall_similar_incidents(error)
        yield sse("memory_badge", {"phase": 3, "count": len(memories), "found": bool(memories)})

        yield sse("log", {"phase": 3, "text": "Generating memory-augmented diagnosis…"})
        diagnosis = agent.diagnose_error(error)
        yield sse("diagnosis", {
            "phase":   3,
            "html":    md_to_html(diagnosis),
            "label":   f"Diagnosis — {label}",
            "variant": "after",
        })

    yield sse("observation", {
        "phase": 3,
        "text": "The agent now cites specific past incidents (INC-101, INC-201) "
                "and gives precise, historically-grounded remediation steps.",
    })
    yield sse("phase_done", {"id": 3})
    time.sleep(0.4)

    # ── PHASE 4 — REFLECT ────────────────────────────────────────────────────
    yield sse("phase", {"id": 4, "title": "Reflect — Cross-Incident Analysis",
                        "icon": "🔮", "status": "running"})
    yield sse("log", {"phase": 4, "text": "Synthesising wisdom across all incidents…"})
    yield sse("query_card", {"phase": 4, "text": STRATEGIC_QUERY})

    reflection = agent.reflect_on_incidents(STRATEGIC_QUERY)
    yield sse("diagnosis", {
        "phase":   4,
        "html":    md_to_html(reflection),
        "label":   "Strategic Reflection",
        "variant": "reflect",
    })
    yield sse("observation", {
        "phase": 4,
        "text": "Hindsight's reflect operation synthesises patterns across all incidents, "
                "giving SRE leadership actionable systemic insights.",
    })
    yield sse("phase_done", {"id": 4})

    # ── COMPLETE ─────────────────────────────────────────────────────────────
    yield sse("done", {"message": "Demo complete — all 4 phases finished successfully."})


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stream")
def stream():
    def generate():
        try:
            yield from run_demo()
        except Exception as e:
            yield sse("error", {"phase": -1, "text": str(e)})
        finally:
            agent.close()

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":  "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    app.run(debug=False, port=5000, threaded=True)
