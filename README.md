# Oja — Compliance Navigator for Nigerian Consumer Goods Founders

*Oja* (Yoruba: market) — the gate every Nigerian founder must pass through before reaching their market.

## Who has this problem

A Nigerian founder with a ready product faces one of the most fragmented regulatory environments on the continent. Getting a food product to market requires navigating NAFDAC, CAC, and SON with no single source of truth. Founders spend weeks piecing together compliance requirements from WhatsApp groups and outdated blog posts.

**The bottleneck:** No structured, reliable, source-cited compliance brief a founder can act on without hiring a consultant.

## What Oja does

Takes a plain-English product description and returns a structured compliance brief: primary regulatory body, required permits with source citations, risk flags, timeline, and confidence rating.

## Setup

Requirements: Python 3.11+, Supabase account, Gemini API key (free at aistudio.google.com)

    git clone https://github.com/akintolaadeyi-gif/Oja.git
    cd Oja
    python3.11 -m pip install -r requirements.txt
    cp .env.example .env
    python3.11 scripts/ingest_docs.py
    python3.11 scripts/run_baseline.py "Your product description"
    python3.11 scripts/run_agent.py "Your product description"

## Improvement Changelog

| Stage | What | Decision |
|---|---|---|
| Baseline | Single prompt, no retrieval | Starting point |
| Iteration 1 | Curated knowledge base + single-query retrieval | Kept |
| Iteration 2 | Multi-query retrieval 3 queries per product | Kept |
| Iteration 3 | Product classification before retrieval | Kept |
| Removed | Verification pass second LLM call | Removed — marginal gain high cost |
| Final | Multi-query RAG + classification + JSON with source citation | Shipped |

**Main failure mode:** Cross-jurisdictional cases where knowledge base only covers Nigerian regulations. Agent flags uncertainty rather than hallucinating.

**Hot take:** The biggest reliability gain was forcing source citation. When the agent cannot find a source it says so. That constraint alone separates a useful compliance tool from a confident hallucination machine.

## Trajectories

See trajectories/ directory — one JSON file per agent run.
