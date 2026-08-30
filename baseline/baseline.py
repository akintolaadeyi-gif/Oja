import os
import json
from dotenv import load_dotenv
from google import genai
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console = Console()

BASELINE_SYSTEM_PROMPT = """You are a compliance advisor for Nigerian consumer goods founders.

When given a product description, provide:
1. The primary regulatory body responsible
2. Required permits and registrations
3. Key compliance risks or flags to be aware of
4. Rough timeline estimate

Be specific to Nigeria. Focus on NAFDAC, SON, CAC, and other relevant bodies.
"""

def run_baseline(product_description: str) -> dict:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    console.print(Panel("[bold yellow]BASELINE RUN[/bold yellow]\nModel: gemini-3.6-flash\nTools: None\nRetrieval: None"))
    console.print(f"\n[dim]Product:[/dim] {product_description}\n")
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=f"{BASELINE_SYSTEM_PROMPT}\n\nProduct description: {product_description}"
    )
    response_text = response.text
    console.print("[bold green]Baseline Response:[/bold green]")
    console.print(response_text)
    return {
        "model": "gemini-3.6-flash",
        "tools": [],
        "retrieval": False,
        "response": response_text
    }

if __name__ == "__main__":
    import sys
    description = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "A zobo hibiscus drink in PET bottles sold in Lagos supermarkets."
    result = run_baseline(description)
    print(json.dumps(result, indent=2))
