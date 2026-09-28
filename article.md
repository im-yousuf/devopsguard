# How I Gave an On-Call Agent a Memory and Cut Incident Diagnosis Time in Half

The on-call rotation is where institutional knowledge goes to die.

An alert fires at 2 AM. You open the runbook. It's six months out of date. You search Slack for "Redis OOM" and find a thread from eight months ago with half the context missing. You dig through Jira, find INC-101, and eventually piece together that someone increased `maxmemory` and changed the eviction policy. Forty minutes later, you've applied the fix. The fix that already existed.

That's the problem I kept running into — not that the knowledge didn't exist, but that it lived in the wrong places. So I built DevOpsGuard: an incident response agent with persistent memory that recalls exactly how your team fixed similar problems before, and surfaces that context the moment a new alert fires.

---

## What DevOpsGuard Does

DevOpsGuard is a Python-based AI agent that wraps two things: [Hindsight Cloud](https://hindsight.vectorize.io/) for persistent agent memory, and Groq for fast LLM inference. The flow is straightforward:

1. **Retain** — You feed it historical post-mortems. An incident ID, the error, the resolution. Hindsight processes each one, extracts structured facts and relationships, and indexes them across four retrieval strategies: semantic similarity, BM25 keyword search, graph traversal, and temporal ranking.

2. **Recall** — When a live error comes in, the agent queries the [Hindsight memory bank](https://vectorize.io/what-is-agent-memory) with the raw error text. It gets back ranked, structured memories — not raw documents, but extracted facts tied to specific past incidents.

3. **Diagnose** — Those recalled memories are injected directly into a Groq prompt alongside the live error. The LLM produces a structured diagnostic report that cites specific past incidents by name and maps their resolutions to the current failure.

4. **Reflect** — A separate operation lets you ask cross-incident strategic questions. "What failure patterns keep recurring?" Hindsight synthesises an answer across everything it has stored, without needing a separate LLM call to build context.

The architecture is intentionally thin. There's no database to maintain, no vector store to configure, no embedding pipeline to debug. Hindsight handles all of that.

---

## The Core Technical Story: Memory Makes the Diagnosis

The cleanest way to explain why memory matters here is to show what happens without it.

**Without memory**, here's what the agent returns for a Redis OOM on the auth-service:

```
Likely Root Cause:
- Redis has hit its maxmemory limit
- The eviction policy is removing active keys

Recommended Actions:
- Increase maxmemory
- Review eviction policy
- Add memory monitoring
```

Correct. Useless. Any SRE knows this. It's the Redis OOM chapter from every infrastructure book ever written.

**With memory loaded** — after ingesting five post-mortems — the same error produces this:

```
Evidence from Past Incidents:
- INC-101 (2026-09-28): Redis OOM on auth-service. Fixed by increasing
  maxmemory from 2GB to 4GB and changing maxmemory-policy to volatile-lru.
  Alert threshold set at 75%.

- INC-519: Redis split-brain after network partition. Sentinel quorum=2
  enabled. min-replicas-to-write=1 set to prevent writes without replica.

Most probable root cause:
The volatile-lru fix from INC-101 may have been reverted or applied to
the wrong Redis instance. Session keys carry TTLs and are therefore
treated as volatile — eligible for eviction under the current policy.
```

That second response doesn't just describe the problem class. It names the exact incident, the exact config values, and proposes a theory specific to this system's history. That's what a senior SRE with six months of context would say. The difference is entirely the memory layer.

---

## How the Memory Integration Works

The Hindsight SDK makes the retain/recall pattern simple to implement. Here's the actual retain call from `agent.py`:

```python
from hindsight_client import Hindsight

hindsight = Hindsight(
    base_url="https://api.hindsight.vectorize.io",
    api_key=os.getenv("HINDSIGHT_API_KEY"),
)

def retain_incident(incident_id, error_log, resolution, metadata=None):
    content = (
        f"Incident {incident_id}: Encountered error — '{error_log}'. "
        f"Root cause and resolution: {resolution}"
    )
    hindsight.retain(
        bank_id="devops-incidents",
        content=content,
        context="postmortem",
        metadata=metadata or {},
    )
```

The `content` field is free-form text. Hindsight doesn't store it verbatim — it decomposes it into structured facts, entities, and relationships. When you recall later, you're querying those structured representations, not doing a naive text search. That's why recall across four strategies (semantic, BM25, graph, temporal) returns 33 ranked memories from five post-mortems — each incident generates multiple extracted facts.

The recall-and-diagnose pipeline injects those memories directly into the Groq prompt:

```python
def diagnose_error(current_error):
    memories = recall_similar_incidents(current_error)

    memory_block = "\n".join(f"  - {m}" for m in memories) if memories \
        else "No relevant historical incidents found."

    user_prompt = (
        f"## Current Production Error\n{current_error}\n\n"
        f"## Recalled Historical Incidents from Memory Bank\n{memory_block}\n\n"
        f"Provide a structured diagnostic report."
    )

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content
```

Temperature at 0.3 matters here. Incident diagnosis is not a creative task. You want the model to reason tightly over the evidence, not hallucinate plausible-sounding root causes.

The `reflect` operation is separate and worth highlighting. It doesn't need Groq at all:

```python
def reflect_on_incidents(query):
    response = hindsight.reflect(
        bank_id="devops-incidents",
        query="What are the most recurring infrastructure failure patterns?"
    )
    return response.text
```

Hindsight runs the reasoning internally and returns synthesised text. For strategic questions — pattern analysis, recurring failures, systemic risk — this is faster and more grounded than building a RAG pipeline yourself.

---

## What the Demo Shows

The demo script (`demo.py`) runs four phases in sequence, and the contrast between Phase 1 and Phase 3 is the whole point.

Phase 1 submits a live Redis OOM error with an empty memory bank. The agent returns generic advice. It doesn't know your system. It doesn't know your team ever fixed this before.

Phase 2 ingests five post-mortems covering Redis OOM, Postgres connection pool exhaustion, Kubernetes OOMKill, API gateway cascade failures, and Redis split-brain. Each `retain` call takes about a second. Hindsight processes them asynchronously in the background.

Phase 3 submits the same Redis error plus a Postgres pool exhaustion error. The agent now cites INC-101 for Redis and INC-201 for Postgres — by name, with specific config values and a theory about what changed since the last fix.

Phase 4 asks a cross-incident strategic question. The reflect response categorises the failure patterns (resource exhaustion, connection management, distributed system fragility), maps each pattern to specific incidents, and produces a prioritised remediation roadmap. That's the kind of output that belongs in a quarterly infrastructure review, not a 2 AM Slack thread.

---

## Lessons Learned

**1. The memory layer changes what questions the LLM can answer.** Without Hindsight, the model reasons from general knowledge. With it, the model reasons from your specific history. These are fundamentally different tasks, and the output quality gap is significant for any domain with institutional context.

**2. Hindsight's multi-strategy retrieval matters more than it sounds.** A single semantic similarity search would miss keyword-specific matches ("OOMKilled", "volatile-lru", "pool_recycle"). BM25 catches exact terminology. Graph traversal connects related entities across incidents. You get all four strategies automatically — that's not trivial to build yourself.

**3. Free-form content input is a real advantage.** You don't need to structure your post-mortems into a schema before ingesting them. Paste a Confluence page, a Slack thread, a raw Jira comment. Hindsight extracts the structure. This matters for real adoption — engineers won't maintain a schema, but they will paste a post-mortem.

**4. Temperature tuning is worth the two seconds it takes.** 0.7 on a diagnosis prompt produces confident-sounding hallucinations. 0.3 keeps the model anchored to the recalled evidence. For safety-critical operational tools, this is not optional.

**5. The `reflect` operation is underrated.** Most people will focus on retain/recall, but reflect — Hindsight's native reasoning-over-memories capability — is what makes cross-incident analysis practical. It's not a RAG call. It's a reasoning operation over structured memory, and the output is qualitatively different.

---

## Where This Goes

Right now DevOpsGuard ingests post-mortems manually. The natural next step is automatic ingestion: hook it into PagerDuty to pull incident data, Confluence for post-mortems, or a Slack channel where your team documents fixes. The memory bank grows passively as your team works. The agent gets better without anyone feeding it deliberately.

The second evolution is proactive alerting — not just "diagnose this error when asked" but "I noticed this error pattern and it looks like the precursor to INC-305, here's what happened last time." That requires combining Hindsight's recall with a monitoring webhook, but the memory layer is already there.

The [Hindsight GitHub repository](https://github.com/vectorize-io/hindsight) has the SDK and examples if you want to build on top of it. The [documentation](https://hindsight.vectorize.io/) covers the full retain/recall/reflect API. If you're building any agent that operates in a domain with historical context — support, sales, compliance, DevOps — the [agent memory pattern](https://vectorize.io/what-is-agent-memory) is worth understanding deeply.

The core insight is simple: stateless agents are hitting a ceiling. The next meaningful improvement in agent quality isn't a bigger model. It's giving agents the ability to learn from their own operational history. That's what persistent memory unlocks.
