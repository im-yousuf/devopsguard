"""
DevOpsGuard — Before/After Memory Demonstration
================================================
This script showcases the core value proposition of DevOpsGuard:

  PHASE 1 — BEFORE (Empty Memory Bank)
    Submit a production error with zero historical context.
    The agent gives generic, textbook-level advice.

  PHASE 2 — RETAIN (Load Post-Mortems)
    Ingest 5 realistic historical incident post-mortems into Hindsight.

  PHASE 3 — AFTER (Memory-Augmented Diagnosis)
    Submit the same (or related) error again.
    The agent now cites specific past incidents and provides
    precise, historically-grounded remediation steps.

  PHASE 4 — REFLECT
    Ask a strategic question across all stored incidents.
    Hindsight synthesises a cross-incident wisdom report.

Run:
    python demo.py
"""

import time
import agent  # DevOpsGuard core module


# ---------------------------------------------------------------------------
# Sample Historical Incidents (post-mortems to ingest)
# ---------------------------------------------------------------------------

HISTORICAL_INCIDENTS = [
    {
        "incident_id": "INC-101",
        "error_log": "Redis OOM crash on auth-service — maxmemory policy evicting active session keys",
        "resolution": (
            "Increased Redis maxmemory from 2GB to 4GB. Changed maxmemory-policy from "
            "noeviction to volatile-lru so only TTL-tagged keys are evicted. "
            "Added Redis memory dashboard alert at 75% threshold."
        ),
        "metadata": {"service": "auth-service", "severity": "P1", "team": "platform"},
    },
    {
        "incident_id": "INC-201",
        "error_log": "Postgres connection pool exhausted on orders-service under Black Friday traffic spike",
        "resolution": (
            "Reduced SQLAlchemy pool_recycle from 3600s to 300s to prevent stale connections. "
            "Set max_overflow=20 and pool_size=10. Added PgBouncer as a connection pooler in "
            "front of the RDS instance. Scaled RDS instance from db.t3.medium to db.r6g.large."
        ),
        "metadata": {"service": "orders-service", "severity": "P1", "team": "backend"},
    },
    {
        "incident_id": "INC-305",
        "error_log": "Kubernetes OOMKilled on payment-processor pods — container memory limit 512Mi exceeded",
        "resolution": (
            "Identified memory leak in gRPC client — connections were not being closed after "
            "use. Fixed by implementing connection pooling with a max_connections=50 cap. "
            "Increased container memory limit to 1Gi and set resource request to 768Mi. "
            "Added HPA with memory-based autoscaling trigger at 80% utilisation."
        ),
        "metadata": {"service": "payment-processor", "severity": "P1", "team": "payments"},
    },
    {
        "incident_id": "INC-412",
        "error_log": "Cascading timeout failures in API gateway — downstream service latency spiking to 30s",
        "resolution": (
            "Root cause: missing circuit breaker on inventory-service client. "
            "Implemented Hystrix-style circuit breaker with 5s timeout and 50% error threshold. "
            "Added retry logic with exponential backoff (max 3 retries). "
            "Deployed bulkhead pattern to isolate inventory calls from payment calls."
        ),
        "metadata": {"service": "api-gateway", "severity": "P2", "team": "platform"},
    },
    {
        "incident_id": "INC-519",
        "error_log": "Redis cluster split-brain after network partition — stale cache served for 12 minutes",
        "resolution": (
            "Enabled Redis Sentinel with quorum=2 for automatic failover. "
            "Set min-replicas-to-write=1 so master rejects writes without at least one replica. "
            "Implemented cache-aside pattern with a 60-second TTL fallback to DB on cache miss. "
            "Added distributed lock (Redlock) for write-heavy cache update paths."
        ),
        "metadata": {"service": "cache-layer", "severity": "P2", "team": "platform"},
    },
]


# ---------------------------------------------------------------------------
# Live Error to Diagnose
# ---------------------------------------------------------------------------

LIVE_ERROR = (
    "CRITICAL: Redis memory usage at 98% on auth-service. "
    "LRU eviction is removing active user session keys causing mass logouts. "
    "Error: OOM command not allowed when used memory > 'maxmemory'. "
    "Pod restart count: 3 in last 10 minutes."
)

LIVE_ERROR_2 = (
    "ERROR: Database connection pool exhausted on orders-service. "
    "All 20 connections in use, new requests timing out after 30s. "
    "Seeing 'QueuePool limit of size 5 overflow 10 reached' in logs. "
    "Traffic is 3x normal — possible sale event spike."
)

STRATEGIC_QUERY = (
    "What are the most recurring infrastructure failure patterns across our incidents, "
    "and what systemic changes should we prioritise to prevent future P1 outages?"
)


# ---------------------------------------------------------------------------
# Helper Utilities
# ---------------------------------------------------------------------------

def divider(title: str = "", char: str = "─", width: int = 65) -> None:
    if title:
        padding = (width - len(title) - 2) // 2
        print(f"\n{'─' * padding} {title} {'─' * padding}\n")
    else:
        print(f"\n{'─' * width}\n")


def pause(seconds: int = 2) -> None:
    """Brief pause so terminal output stays readable during demo."""
    time.sleep(seconds)


# ---------------------------------------------------------------------------
# Demo Phases
# ---------------------------------------------------------------------------

def phase_0_setup():
    divider("PHASE 0 — INITIALISE MEMORY BANK")
    print("Setting up Hindsight memory bank...")
    agent.setup_bank()
    pause(1)


def phase_1_before():
    divider("PHASE 1 — BEFORE (Empty Memory Bank)")
    print("📭  No historical incidents have been loaded yet.")
    print("    Submitting live error for diagnosis...\n")
    print(f"    Live Error: {LIVE_ERROR}\n")
    agent.diagnose_error(LIVE_ERROR)
    print(
        "\n💡  Observation: With no memory context, the agent gives "
        "generic SRE textbook advice — no specific past incidents cited."
    )
    pause(2)


def phase_2_retain():
    divider("PHASE 2 — RETAIN (Ingesting Historical Post-Mortems)")
    print(f"📥  Loading {len(HISTORICAL_INCIDENTS)} historical incidents into Hindsight...\n")

    for inc in HISTORICAL_INCIDENTS:
        agent.retain_incident(
            incident_id=inc["incident_id"],
            error_log=inc["error_log"],
            resolution=inc["resolution"],
            metadata=inc["metadata"],
        )
        pause(1)  # Slight delay to avoid rate-limiting on retain calls

    print(
        f"\n✅  All {len(HISTORICAL_INCIDENTS)} post-mortems stored in Hindsight memory bank '{agent.BANK_ID}'."
    )
    print("    Hindsight has extracted structured facts, entities, and relationships.")
    pause(2)


def phase_3_after():
    divider("PHASE 3 — AFTER (Memory-Augmented Diagnosis)")
    print("📬  Memory bank is now populated.")
    print("    Re-submitting a related Redis error for diagnosis...\n")
    print(f"    Live Error: {LIVE_ERROR}\n")
    agent.diagnose_error(LIVE_ERROR)

    print("\n" + "=" * 65)
    print("    Now diagnosing a Postgres connection pool error...")
    print("=" * 65 + "\n")
    print(f"    Live Error: {LIVE_ERROR_2}\n")
    agent.diagnose_error(LIVE_ERROR_2)

    print(
        "\n💡  Observation: The agent now cites specific incidents (INC-101, INC-201) "
        "and gives precise, historically-grounded steps — not generic advice."
    )
    pause(2)


def phase_4_reflect():
    divider("PHASE 4 — REFLECT (Cross-Incident Strategic Analysis)")
    print("🔮  Asking Hindsight to synthesise wisdom across ALL stored incidents...\n")
    print(f"    Question: {STRATEGIC_QUERY}\n")
    agent.reflect_on_incidents(STRATEGIC_QUERY)
    print(
        "\n💡  Observation: Hindsight's reflect operation synthesises patterns "
        "across incidents — giving SRE leadership actionable systemic insights."
    )
    pause(1)


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def main():
    print("\n" + "█" * 65)
    print("   DevOpsGuard — AI Incident Response Agent")
    print("   Before/After Memory Demonstration")
    print("█" * 65)
    print("\n   Memory Layer : Hindsight Cloud (hindsight.vectorize.io)")
    print("   LLM Engine   : Groq (openai/gpt-oss-120b)")
    print("   Memory Bank  : devops-incidents\n")

    try:
        phase_0_setup()
        phase_1_before()
        phase_2_retain()
        phase_3_after()
        phase_4_reflect()

        divider("DEMO COMPLETE")
        print("✅  DevOpsGuard demonstration finished successfully.")
        print(
            "\n   Key Takeaway:\n"
            "   ┌──────────────────────────────────────────────────────┐\n"
            "   │  BEFORE memory → Generic, textbook-level advice      │\n"
            "   │  AFTER memory  → Precise, incident-specific fixes    │\n"
            "   └──────────────────────────────────────────────────────┘\n"
        )

    except Exception as e:
        print(f"\n[Error] Demo failed: {e}")
        raise
    finally:
        agent.close()
        print("   Hindsight client closed.")


if __name__ == "__main__":
    main()
