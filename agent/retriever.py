import os
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client
from rich.console import Console

load_dotenv()
console = Console()

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

def embed_query(query: str) -> list:
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return response.data[0].embedding

def retrieve(query: str, top_k: int = 5) -> list:
    query_embedding = embed_query(query)
    try:
        result = supabase.rpc("match_oja_documents", {
            "query_embedding": query_embedding,
            "match_count": top_k
        }).execute()
        return result.data or []
    except Exception as e:
        console.print(f"[yellow]Retrieval warning: {e}[/yellow]")
        return []

def retrieve_multi_query(queries: list, top_k_per_query: int = 3) -> list:
    seen_ids = set()
    all_passages = []
    for q in queries:
        results = retrieve(q, top_k=top_k_per_query)
        for p in results:
            pid = p.get("id", p.get("content", "")[:50])
            if pid not in seen_ids:
                seen_ids.add(pid)
                all_passages.append(p)
    return all_passages
