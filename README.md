# DevOpsGuard — AI Incident Response Agent with Persistent Memory

An intelligent, memory-augmented incident response assistant for DevOps and SRE teams. DevOpsGuard uses **Hindsight Cloud** as a persistent memory layer and **Groq** as a fast LLM inference engine to recall historical post-mortems and deliver precise, historically-grounded diagnoses for live production errors.

---

## How It Works

```
Live Error Log
      │
      ▼
┌─────────────────────┐       ┌──────────────────────────┐
│  Hindsight Cloud    │ ────▶ │  Groq LLM                │
│  (Memory Recall)    │       │  (Diagnosis Engine)       │
│  devops-incidents   │       │  llama-3.3-70b-versatile  │
└─────────────────────┘       └──────────────────────────┘
      │                                    │
      └──────────────┬─────────────────────┘
                     ▼
          Structured Diagnostic Report
          (cites specific past incidents)
```

### The Before/After Difference

| | Before (Empty Memory) | After (Memory Loaded) |
|---|---|---|
| **Past incidents cited** | None | INC-101, INC-201, etc. |
| **Advice quality** | Generic textbook steps | Specific config values & proven fixes |
| **Time to resolution** | Engineer must search manually | Immediate, historically grounded |

---

## Project Structure

```
devopsguard/
├── agent.py          # Core agent — retain, recall, diagnose, reflect
├── demo.py           # Before/after demonstration script
├── requirements.txt  # Python dependencies
├── .env              # API credentials (never commit this)
└── README.md
```

---

## Setup

### 1. Prerequisites

- Python 3.10+
- A [Hindsight Cloud](https://hindsight.vectorize.io) account (API key provided)
- A [Groq](https://console.groq.com) account (free tier available)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Edit `.env` and fill in your keys:

```env
HINDSIGHT_API_KEY=hsk_your_key_here
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
GROQ_API_KEY=gsk_your_groq_key_here
```

> Get your free Groq API key at [console.groq.com](https://console.groq.com)

---

## Running the Demo

```bash
python demo.py
```

The demo runs four phases automatically:

| Phase | What Happens |
|---|---|
| **0 — Setup** | Initialises the `devops-incidents` Hindsight memory bank |
| **1 — Before** | Diagnoses a Redis OOM error with an empty memory bank (generic output) |
| **2 — Retain** | Ingests 5 real-world incident post-mortems into Hindsight |
| **3 — After** | Diagnoses the same Redis error + a Postgres error (specific, cited output) |
| **4 — Reflect** | Asks Hindsight to synthesise cross-incident systemic patterns |

---

## Using the Agent Programmatically

```python
import agent

# One-time setup
agent.setup_bank()

# Store a post-mortem
agent.retain_incident(
    incident_id="INC-301",
    error_log="Kafka consumer lag spiking to 500k messages on checkout-events topic",
    resolution="Scaled consumer group from 3 to 8 pods. Set max.poll.records=200. Added lag alert at 50k.",
    metadata={"service": "checkout-consumer", "severity": "P2", "team": "data"}
)

# Diagnose a live error
agent.diagnose_error(
    "Kafka consumer group checkout-events is falling behind, lag at 1.2M messages"
)

# Strategic reflection across all incidents
agent.reflect_on_incidents(
    "Which services have the highest repeat incident rate?"
)

# Clean up
agent.close()
```

---

## Agent API Reference

### `setup_bank()`
Creates the `devops-incidents` Hindsight memory bank. Safe to call multiple times.

### `retain_incident(incident_id, error_log, resolution, metadata=None)`
Stores a historical incident post-mortem into Hindsight persistent memory.

| Param | Type | Description |
|---|---|---|
| `incident_id` | `str` | Unique ID, e.g. `"INC-101"` |
| `error_log` | `str` | Short description of the observed error |
| `resolution` | `str` | Root cause and the fix applied |
| `metadata` | `dict` | Optional: service name, severity, team, etc. |

### `diagnose_error(current_error)`
Recalls relevant past incidents from Hindsight and generates a structured AI diagnosis via Groq.

Returns a formatted diagnostic report with:
1. Likely Root Cause
2. Evidence from Past Incidents
3. Recommended Immediate Actions
4. Long-Term Prevention Steps

### `recall_similar_incidents(current_error)`
Raw recall — returns a list of matching memory strings without generating an LLM response.

### `reflect_on_incidents(query)`
Uses Hindsight's `reflect` operation to synthesise an AI answer across all stored incidents.

### `close()`
Releases the Hindsight SDK connection.

---

## Security Notes

- Never commit `.env` to source control — add it to `.gitignore`
- Do not include real production secrets, passwords, or customer PII in incident logs
- Rotate API keys regularly via the Hindsight Cloud dashboard

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| Persistent Memory | [Hindsight Cloud](https://hindsight.vectorize.io) (`hindsight-client`) |
| LLM Inference | [Groq](https://groq.com) (`groq` SDK, llama-3.3-70b-versatile) |
| Config Management | `python-dotenv` |
