# DevOpsGuard — Video Script & YouTube Titles

---

## 5 YouTube Title Options

1. I Built an Incident Response Agent With Memory — Here's What Happened
2. How Hindsight Turned My AI Agent Into a Senior SRE
3. Why My On-Call Agent Was Useless Until I Gave It Memory
4. I Fed 5 Post-Mortems to an AI Agent — Here's What It Recalled at 2 AM
5. How I Built a Production Incident Agent That Actually Remembers Past Fixes

---

## 3-Minute Video Script

---

### SEGMENT 1 — Intro (0:00–0:30)

**[SCREEN: Show terminal at project root — `d:\New folder\devopsguard`]**

Hey, I'm [YOUR NAME]. I built an AI incident response agent called DevOpsGuard.

The idea is simple: when production breaks, the fix usually already exists — buried in a Jira ticket, a Slack thread, a post-mortem nobody reads anymore.

DevOpsGuard uses Hindsight for persistent agent memory, so it actually recalls how your team fixed similar problems before — and surfaces that context the moment a new alert fires.

Let me show you exactly what that looks like.

---

### SEGMENT 2 — The Problem (0:30–1:00)

**[SCREEN: Open `agent.py`, scroll to `diagnose_error()` function]**

Here's the core function. It does two things: first it queries Hindsight for past incidents, then it passes those memories into a Groq prompt.

**[SCREEN: Switch to terminal, run:]**
```
python demo.py
```

**[SCREEN: Let Phase 0 and Phase 1 output appear — pause here]**

Watch this first response. The memory bank is empty. I'm submitting a Redis OOM error on the auth-service.

**[SCREEN: Highlight the Phase 1 diagnostic output]**

"Increase maxmemory. Review your eviction policy. Add monitoring."

That's it. Correct. Completely useless at 2 AM. Any engineer already knows this. The agent has no idea we've seen this exact failure before.

---

### SEGMENT 3 — Live Demo (1:00–2:30)

**[SCREEN: Watch Phase 2 output — the retain calls firing]**

Now watch Phase 2. I'm ingesting 5 historical post-mortems. These are real incident descriptions — Redis OOM, Postgres pool exhaustion, Kubernetes OOMKill, API gateway cascades, Redis split-brain.

Each `retain()` call sends the post-mortem text to Hindsight. Hindsight doesn't store it as a blob — it extracts structured facts, entities, and relationships. That's why recall quality is so much higher than a naive vector search.

**[SCREEN: Watch Phase 3 output appear — specifically the "33 relevant past incidents recalled" line]**

There it is — 33 structured memories recalled from just 5 post-mortems. One incident generates multiple extracted facts.

**[SCREEN: Highlight the diagnosis output that cites INC-101 and INC-519]**

Now look at the diagnosis. It names INC-101 — the exact Redis OOM from September. It says the volatile-lru fix may have been reverted. It ties INC-519 — the split-brain incident — to the current failure pattern.

**[SCREEN: Let the Postgres diagnosis for INC-201 appear]**

Same thing for the Postgres pool exhaustion. It cites INC-201, gives the exact SQLAlchemy config values that fixed it last time — `pool_size=10`, `max_overflow=20`, `pool_recycle=300` — and mentions PgBouncer.

**[SCREEN: Scroll to `recall_similar_incidents()` in agent.py]**

Here's the recall call. One line. Hindsight runs four retrieval strategies in parallel behind the scenes — semantic similarity, BM25, graph traversal, and temporal — then fuses and reranks the results.

**[SCREEN: Watch Phase 4 reflect output]**

And this is reflect — a cross-incident analysis. I'm asking "what are the recurring failure patterns?" Hindsight synthesises an answer across all stored incidents. Three pattern categories, a prioritised remediation table, specific incident citations. No extra LLM call needed.

---

### SEGMENT 4 — Wrap Up (2:30–3:00)

**[SCREEN: Show the final demo output summary box]**

The key takeaway: the model didn't get smarter between Phase 1 and Phase 3. The prompts are identical. The only thing that changed is the memory layer.

Before Hindsight: generic SRE textbook.
After Hindsight: specific, incident-cited, historically grounded diagnosis.

That gap is the entire argument for [agent memory](https://vectorize.io/what-is-agent-memory).

What surprised me most was how little code it took. The `retain()` and `recall()` calls are three lines each. The complexity lives inside Hindsight — multi-strategy retrieval, entity extraction, structured memory — and you get all of it through the SDK.

Links in the description. Thanks for watching.

---

## Screen Recording Checklist

Before you hit record:
- [ ] Increase terminal font size (at least 16pt)
- [ ] Close Slack, email, browser notifications
- [ ] Set resolution to 1080p minimum
- [ ] Have `demo.py` ready but NOT yet running
- [ ] Open `agent.py` in your editor so you can switch to it
- [ ] Test audio levels with a 10-second clip first

## Description Template (YouTube)

DevOpsGuard is an incident response AI agent with persistent memory. It ingests post-mortems using Hindsight and recalls specific past fixes when new production errors fire — giving you historically-grounded diagnoses instead of generic SRE advice.

🔗 Project GitHub: [YOUR REPO URL]
🧠 Hindsight: https://github.com/vectorize-io/hindsight
📖 Hindsight Docs: https://hindsight.vectorize.io/
💡 Agent Memory: https://vectorize.io/what-is-agent-memory
