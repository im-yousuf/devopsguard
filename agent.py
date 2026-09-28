"""
DevOpsGuard — AI Incident Response Agent with Persistent Memory
================================================================
Core agent module providing:
  - retain_incident()  : Store historical post-mortems in Hindsight memory bank
  - diagnose_error()   : Recall relevant past incidents + generate AI diagnosis via Groq
  - setup_bank()       : One-time memory bank initialisation (idempotent)
"""

import os
import sys
from dotenv import load_dotenv
from hindsight_client import Hindsight
from groq import Groq

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

load_dotenv()

HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")
HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BANK_ID = "devops-incidents"

# Validate required credentials
if not HINDSIGHT_API_KEY:
    sys.exit("[Fatal] HINDSIGHT_API_KEY is not set. Check your .env file.")

if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
    sys.exit("[Fatal] GROQ_API_KEY is not set. Add it to your .env file (https://console.groq.com).")

# ---------------------------------------------------------------------------
# SDK Clients
# ---------------------------------------------------------------------------

hindsight = Hindsight(
    base_url=HINDSIGHT_BASE_URL,
    api_key=HINDSIGHT_API_KEY,
)

groq_client = Groq(api_key=GROQ_API_KEY)


# ---------------------------------------------------------------------------
# Memory Bank Setup
# ---------------------------------------------------------------------------

def setup_bank() -> None:
    """
    Creates the Hindsight memory bank if it does not already exist.
    Safe to call multiple times — creation errors for existing banks are ignored.
    """
    try:
        hindsight.create_bank(
            bank_id=BANK_ID,
            name="DevOps Incident Post-Mortems",
            background=(
                "This memory bank stores historical production incident post-mortems "
                "for a cloud-native engineering team. It is used to recall past failures, "
                "root causes, and proven resolutions to accelerate future incident response."
            ),
        )
        print(f"[Setup] Memory bank '{BANK_ID}' created successfully.")
    except Exception as e:
        # Bank already exists — treat as a no-op
        if "already exists" in str(e).lower() or "conflict" in str(e).lower() or "400" in str(e):
            print(f"[Setup] Memory bank '{BANK_ID}' already exists — skipping creation.")
        else:
            print(f"[Setup Warning] Could not create bank: {e}")


# ---------------------------------------------------------------------------
# Retain — Store Historical Incidents
# ---------------------------------------------------------------------------

def retain_incident(incident_id: str, error_log: str, resolution: str, metadata: dict = None) -> None:
    """
    Pushes a historical incident post-mortem into the Hindsight memory bank.

    Args:
        incident_id : Unique incident identifier, e.g. "INC-101"
        error_log   : Short description of the observed error / symptom
        resolution  : Root cause analysis and the fix that resolved it
        metadata    : Optional dict with extra fields (severity, service, team, etc.)
    """
    content = (
        f"Incident {incident_id}: Encountered error — '{error_log}'. "
        f"Root cause and resolution: {resolution}"
    )

    hindsight.retain(
        bank_id=BANK_ID,
        content=content,
        context="postmortem",
        metadata=metadata or {},
    )

    print(f"[✓ Retained] Incident {incident_id} stored in Hindsight memory.")


# ---------------------------------------------------------------------------
# Recall — Retrieve Relevant Past Incidents
# ---------------------------------------------------------------------------

def recall_similar_incidents(current_error: str) -> list[str]:
    """
    Queries Hindsight for semantically similar past incidents.

    Args:
        current_error : The live production error or symptom description

    Returns:
        List of recalled memory strings (may be empty if no match found)
    """
    result = hindsight.recall(
        bank_id=BANK_ID,
        query=current_error,
        budget="mid",
    )

    memories = [m.text for m in result.results] if result.results else []
    return memories


# ---------------------------------------------------------------------------
# Diagnose — AI-Powered Context-Aware Error Diagnosis
# ---------------------------------------------------------------------------

def diagnose_error(current_error: str) -> str:
    """
    Full diagnostic pipeline:
      1. Recalls relevant past incidents from Hindsight
      2. Builds a context-aware prompt injecting memory into the LLM
      3. Returns a structured diagnosis from Groq

    Args:
        current_error : Raw production error log or symptom description

    Returns:
        Formatted diagnostic report string
    """
    print(f"\n{'='*60}")
    print(f"🔍  Analyzing Live Error")
    print(f"{'='*60}")
    print(f"  Error: {current_error}")
    print(f"{'='*60}\n")

    # Step 1 — Recall from Hindsight
    print("🧠  Querying Hindsight memory bank...")
    memories = recall_similar_incidents(current_error)

    if memories:
        print(f"  ✅  {len(memories)} relevant past incident(s) recalled.\n")
        memory_block = "\n".join(f"  - {m}" for m in memories)
    else:
        print("  ⚠️   No similar past incidents found in memory.\n")
        memory_block = "  No relevant historical incidents found."

    # Step 2 — Build prompt for Groq
    system_prompt = (
        "You are DevOpsGuard, an expert Site Reliability Engineer and incident response AI. "
        "Your job is to diagnose production errors quickly and accurately. "
        "When past incidents are available, cite them explicitly and map them to the current failure. "
        "Structure every response with: "
        "1) Likely Root Cause, "
        "2) Evidence from Past Incidents (if any), "
        "3) Recommended Immediate Actions, "
        "4) Long-Term Prevention Steps."
    )

    user_prompt = (
        f"## Current Production Error\n"
        f"{current_error}\n\n"
        f"## Recalled Historical Incidents from Memory Bank\n"
        f"{memory_block}\n\n"
        f"Provide a structured diagnostic report."
    )

    # Step 3 — Groq inference
    print("⚡  Generating AI diagnosis via Groq (openai/gpt-oss-120b)...")
    chat_completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,  # Lower temp for deterministic, factual incident analysis
        max_tokens=1024,
    )

    diagnosis = chat_completion.choices[0].message.content

    print("\n📋  Diagnostic Report:")
    print("-" * 60)
    print(diagnosis)
    print("-" * 60)

    return diagnosis


# ---------------------------------------------------------------------------
# Reflect — Synthesised Wisdom Across All Incidents
# ---------------------------------------------------------------------------

def reflect_on_incidents(query: str) -> str:
    """
    Uses Hindsight's reflect operation to synthesise an AI-powered answer
    grounded across all stored incident memories (no Groq call needed).

    Args:
        query : A strategic or investigative question about past incidents

    Returns:
        Synthesised answer string from Hindsight
    """
    print(f"\n🔮  Reflecting on: '{query}'")
    response = hindsight.reflect(
        bank_id=BANK_ID,
        query=query,
    )
    print("\n📊  Hindsight Reflection:")
    print("-" * 60)
    print(response.text)
    print("-" * 60)
    return response.text


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def close():
    """Release Hindsight SDK resources."""
    hindsight.close()
