import os
import json
import sys
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from rich.console import Console
from rich.table import Table
from rich import box

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'))
console = Console()

def call_gemini(prompt: str) -> str:
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    r = client.models.generate_content(model="gemini-3.6-flash", contents=prompt)
    return r.text

def score_response(response_text: str, case: dict) -> dict:
    prompt = f"""Score this compliance response against expected answers. Return JSON only.

Expected regulatory body: {case['expected_regulatory_body']}
Expected permits: {json.dumps(case['expected_permits'])}
Expected flags: {json.dumps(case['expected_flags'])}

Response: {response_text[:2000]}

Return JSON:
{{
  "regulatory_body_correct": true/false,
  "permits_found": ["list of expected permits mentioned"],
  "permits_missed": ["list not mentioned"],
  "flags_found": ["list of expected flags raised"],
  "flags_missed": ["list not raised"],
  "hallucinations": ["fabricated permits or bodies"]
}}"""
    raw = call_gemini(prompt)
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"): raw = raw[4:]
    raw = raw.strip().rstrip("```").strip()
    try:
        return json.loads(raw)
    except:
        return {"regulatory_body_correct": False, "permits_found": [], "permits_missed": [], "flags_found": [], "flags_missed": [], "hallucinations": []}

def compute_score(scoring: dict, case: dict) -> dict:
    body = 1.0 if scoring.get("regulatory_body_correct") else 0.0
    ep = case.get("expected_permits", [])
    fp = scoring.get("permits_found", [])
    permit = len(fp) / len(ep) if ep else 0.0
    ef = case.get("expected_flags", [])
    ff = scoring.get("flags_found", [])
    flag = len(ff) / len(ef) if ef else 0.0
    hall = min(len(scoring.get("hallucinations", [])) * 0.1, 0.3)
    composite = max(0.0, min(1.0, body * 0.35 + permit * 0.40 + flag * 0.25 - hall))
    return {"regulatory_body": body, "permit_coverage": round(permit, 2), "flag_coverage": round(flag, 2), "hallucination_penalty": round(hall, 2), "composite": round(composite, 2)}

def run_evaluation():
    from baseline.baseline import run_baseline
    from agent.agent import run_agent

    cases_path = Path(__file__).parent / "cases.json"
    with open(cases_path) as f:
        cases = json.load(f)

    results = []
    console.print(f"\n[bold cyan]Oja Evaluation — {len(cases)} cases[/bold cyan]\n")

    for case in cases:
        console.print(f"[bold]{case['id']}[/bold] {case['category']} [{case['difficulty']}]")
        b = run_baseline(case["product_description"])
        time.sleep(2)
        bs = score_response(b["response"], case)
        bsc = compute_score(bs, case)

        a = run_agent(case["product_description"], save_trajectory=True)
        time.sleep(2)
        atext = json.dumps(a.get("brief", {}))
        as_ = score_response(atext, case)
        asc = compute_score(as_, case)

        results.append({"case_id": case["id"], "category": case["category"], "difficulty": case["difficulty"], "baseline": {"scores": bsc}, "agent": {"scores": asc}})
        diff = asc["composite"] - bsc["composite"]
        console.print(f"  Baseline: {bsc['composite']:.2f} | Agent: {asc['composite']:.2f} | Delta: {diff:+.2f}\n")
        time.sleep(1)

    with open(Path(__file__).parent / "results.json", "w") as f:
        json.dump(results, f, indent=2)

    table = Table(title="Oja Results", box=box.ROUNDED)
    table.add_column("Case"); table.add_column("Category"); table.add_column("Difficulty")
    table.add_column("Baseline", justify="right"); table.add_column("Agent", justify="right"); table.add_column("Delta", justify="right")

    bt, at, n = 0, 0, 0
    for r in results:
        b = r["baseline"]["scores"]["composite"]
        a = r["agent"]["scores"]["composite"]
        bt += b; at += a; n += 1
        table.add_row(r["case_id"], r["category"], r["difficulty"], f"{b:.2f}", f"{a:.2f}", f"{a-b:+.2f}")

    table.add_section()
    table.add_row("AVG", "", "", f"[bold]{bt/n:.2f}[/bold]", f"[bold]{at/n:.2f}[/bold]", f"[bold green]{(at-bt)/n:+.2f}[/bold green]")
    console.print(table)

if __name__ == "__main__":
    run_evaluation()
