import os
import json
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from google import genai
from rich.console import Console
from rich.panel import Panel

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
console = Console()

AGENT_SYSTEM_PROMPT = """You are Oja, a compliance navigator for Nigerian consumer goods founders.

Produce a structured, source-cited compliance brief based ONLY on the retrieved passages provided.

RULES:
- Only make claims grounded in the retrieved passages
- Cite the source document for each requirement
- Never invent permits or regulatory bodies not in the sources
- If unclear, flag it explicitly
- Return valid JSON only, no markdown

OUTPUT FORMAT:
{
  "product_summary": "one sentence",
  "category": "food_beverage | cosmetics | dietary_supplement",
  "primary_regulatory_body": "main body",
  "additional_bodies": ["others"],
  "required_permits": [
    {"permit": "name", "issuing_body": "body", "notes": "detail", "source": "document title"}
  ],
  "estimated_timeline": "estimate with reasoning",
  "risk_flags": [
    {"flag": "description", "severity": "high | medium | low", "source": "document title"}
  ],
  "recommended_first_steps": ["step 1", "step 2", "step 3"],
  "confidence": "high | medium | low",
  "confidence_note": "why"
}"""


def call_gemini(prompt: str, system: str = None) -> str:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    full_prompt = f"{system}\n\n{prompt}" if system else prompt
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=full_prompt
    )
    return response.text


def get_embedding(text: str) -> list:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    r = client.models.embed_content(model="models/gemini-embedding-2", contents=text)
    return r.embeddings[0].values


def retrieve(query: str, top_k: int = 4) -> list:
    from supabase import create_client
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
    embedding = get_embedding(query)
    try:
        result = supabase.rpc("match_oja_documents", {
            "query_embedding": embedding,
            "match_count": top_k
        }).execute()
        return result.data or []
    except Exception as e:
        console.print(f"[yellow]Retrieval warning: {e}[/yellow]")
        return []


def retrieve_multi(queries: list, top_k: int = 3) -> list:
    seen = set()
    passages = []
    for q in queries:
        for p in retrieve(q, top_k):
            pid = p.get("id", p.get("content", "")[:50])
            if pid not in seen:
                seen.add(pid)
                passages.append(p)
        time.sleep(0.2)
    return passages


def classify(description: str) -> str:
    result = call_gemini(
        f"Classify into exactly one: food_beverage, cosmetics, dietary_supplement, other\nReply with label only.\nProduct: {description}"
    )
    return result.strip().lower()


def build_queries(description: str, category: str) -> list:
    result = call_gemini(
        f"""Generate 3 search queries to retrieve Nigerian regulatory compliance documents.
Product: {description}
Category: {category}
Return JSON array of 3 strings only. Example: ["query1", "query2", "query3"]"""
    )
    try:
        text = result.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)[:3]
    except Exception:
        return [
            f"NAFDAC {category} registration requirements Nigeria",
            f"{category} labelling rules Nigeria",
            "CAC business registration Nigerian founder"
        ]


def run_agent(product_description: str, save_trajectory: bool = True) -> dict:
    trajectory = []
    console.print(Panel("[bold cyan]OJA COMPLIANCE AGENT[/bold cyan]\nModel: gemini-3.6-flash\nTools: RAG retrieval + multi-query\nMemory: per-run context"))

    console.print("\n[bold]Step 1:[/bold] Classifying product...")
    category = classify(product_description)
    console.print(f"  → [green]{category}[/green]")
    trajectory.append({"step": "classify", "output": category})

    console.print("\n[bold]Step 2:[/bold] Generating retrieval queries...")
    queries = build_queries(product_description, category)
    for q in queries:
        console.print(f"  → [dim]{q}[/dim]")
    trajectory.append({"step": "queries", "queries": queries})

    console.print("\n[bold]Step 3:[/bold] Retrieving regulatory passages...")
    passages = retrieve_multi(queries)
    console.print(f"  → [green]{len(passages)}[/green] passages retrieved")

    context = ""
    for i, p in enumerate(passages):
        context += f"\n--- SOURCE {i+1}: {p.get('title','Unknown')} ---\n{p.get('content','')}\n"
    trajectory.append({"step": "retrieval", "count": len(passages), "sources": [p.get("title","") for p in passages]})

    console.print("\n[bold]Step 4:[/bold] Synthesising compliance brief...")
    synthesis_prompt = f"""Product: {product_description}
Category: {category}

Retrieved passages:
{context}

Produce the compliance brief as valid JSON based only on the passages above."""

    raw = call_gemini(synthesis_prompt, system=AGENT_SYSTEM_PROMPT)
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()

    try:
        brief = json.loads(raw)
    except Exception:
        brief = {"raw_response": raw, "parse_error": True}

    trajectory.append({"step": "synthesis", "brief": brief})
    console.print("\n[bold green]Brief:[/bold green]")
    console.print_json(json.dumps(brief, indent=2))

    result = {
        "product_description": product_description,
        "category": category,
        "queries": queries,
        "passages_retrieved": len(passages),
        "brief": brief,
        "trajectory": trajectory
    }

    if save_trajectory:
        os.makedirs("trajectories", exist_ok=True)
        path = f"trajectories/trajectory_{category}_{abs(hash(product_description)) % 10000}.json"
        with open(path, "w") as f:
            json.dump(result, f, indent=2)
        console.print(f"\n[dim]Trajectory saved: {path}[/dim]")

    return result


if __name__ == "__main__":
    description = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else \
        "A zobo hibiscus drink in 50cl PET bottles sold in Lagos supermarkets."
    run_agent(description)
