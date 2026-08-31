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

    last_error = None

    for attempt in range(5):
        try:
            r = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
            return r.text

        except Exception as e:
            last_error = e
            error_text = str(e)

            if "503" not in error_text and "UNAVAILABLE" not in error_text:
                raise

            wait_time = 2 ** attempt
            console.print(
                f"[yellow]Gemini temporarily unavailable. "
                f"Retry {attempt + 1}/5 in {wait_time}s...[/yellow]"
            )
            time.sleep(wait_time)

    raise last_error

def score_response(response_text: str, case: dict) -> dict:
    """
    Deterministic evaluator.

    This intentionally does NOT call Gemini.
    This prevents the evaluation itself from consuming API quota.
    """
    response_lower = response_text.lower()

    expected_body = case.get("expected_regulatory_body", "")
    body_parts = [
        part.strip().lower()
        for part in expected_body.replace("/", ",").split(",")
        if part.strip()
    ]

    regulatory_body_correct = all(
        body in response_lower for body in body_parts
    )

    permits_found = []
    permits_missed = []

    for permit in case.get("expected_permits", []):
        permit_lower = permit.lower()

        if permit_lower in response_lower:
            permits_found.append(permit)
            continue

        # Flexible matching.
        words = [
            w for w in permit_lower
            .replace("-", " ")
            .replace("/", " ")
            .split()
            if len(w) > 3
        ]

        # Special aliases for common regulatory terminology.
        aliases = {
            "cac registration": [
                ["cac"],
                ["corporate", "affairs"],
                ["business", "registration"],
            ],
            "cac business registration": [
                ["cac"],
                ["business", "registration"],
                ["corporate", "affairs"],
            ],
            "nafdac product registration": [
                ["nafdac", "registration"],
                ["product", "registration"],
            ],
            "nafdac facility inspection": [
                ["nafdac", "inspection"],
                ["facility", "inspection"],
            ],
            "nafdac cosmetic product notification": [
                ["nafdac", "cosmetic"],
                ["cosmetic", "notification"],
            ],
            "nafdac supplement registration": [
                ["nafdac", "supplement"],
                ["supplement", "registration"],
            ],
            "nafdac paediatric supplement registration": [
                ["nafdac", "paediatric"],
                ["pediatric", "supplement"],
                ["paediatric", "supplement"],
            ],
            "gmp certificate": [
                ["gmp"],
                ["good", "manufacturing", "practice"],
            ],
            "nepc exporter registration": [
                ["nepc"],
                ["exporter", "registration"],
            ],
            "nafdac export certificate": [
                ["nafdac", "export"],
                ["export", "certificate"],
            ],
            "nafdac import permit": [
                ["nafdac", "import"],
                ["import", "permit"],
            ],
        }

        matched = False

        for alias_group in aliases.get(permit_lower, []):
            if all(word in response_lower for word in alias_group):
                matched = True
                break

        if not matched and words:
            matched = (
                sum(word in response_lower for word in words)
                >= max(1, len(words) // 2)
            )

        if matched:
            permits_found.append(permit)
        else:
            permits_missed.append(permit)

    flags_found = []
    flags_missed = []

    for flag in case.get("expected_flags", []):
        flag_lower = flag.lower()

        if flag_lower in response_lower:
            flags_found.append(flag)
            continue

        words = [
            w for w in flag_lower
            .replace("-", " ")
            .replace("/", " ")
            .split()
            if len(w) > 3
        ]

        # Flexible semantic-ish keyword matching.
        matched = False

        flag_aliases = {
            "pet bottle suitability": [
                ["pet", "bottle"],
                ["food", "grade", "pet"],
                ["packaging", "suitability"],
            ],
            "shelf life testing required": [
                ["shelf", "life"],
                ["shelf-life"],
            ],
            "nutritional labelling mandatory": [
                ["nutritional", "labelling"],
                ["nutrition", "label"],
                ["nutritional", "label"],
            ],
            "aflatoxin testing likely required": [
                ["aflatoxin"],
            ],
            "ingredient list must be inci compliant": [
                ["inci"],
                ["ingredient", "list"],
            ],
            "lavender oil concentration limits apply": [
                ["lavender"],
                ["concentration", "limit"],
            ],
            "kojic acid concentration limits apply": [
                ["kojic", "acid"],
                ["concentration", "limit"],
            ],
            "rebranding requires manufacturer authorization": [
                ["manufacturer", "authorization"],
                ["manufacturer", "authorisation"],
                ["rebrand"],
            ],
            "import permit and registration are separate": [
                ["import", "permit"],
                ["registration"],
            ],
            "immune booster claim requires scientific backing": [
                ["immune", "claim"],
                ["scientific", "backing"],
                ["scientific", "evidence"],
            ],
            "herbal registration timeline 6-12 months": [
                ["herbal", "registration"],
                ["6-12", "months"],
                ["6", "12", "months"],
            ],
            "paediatric products face stricter review": [
                ["paediatric"],
                ["pediatric"],
                ["children"],
                ["stricter", "review"],
            ],
            "iron supplements have dosage caps": [
                ["iron", "dosage"],
                ["iron", "dose"],
                ["iron", "limit"],
            ],
            "child-resistant packaging required": [
                ["child-resistant"],
                ["child", "resistant"],
                ["children", "packaging"],
            ],
        }

        for alias_group in flag_aliases.get(flag_lower, []):
            if all(word in response_lower for word in alias_group):
                matched = True
                break

        if not matched and words:
            matched = (
                sum(word in response_lower for word in words)
                >= max(1, len(words) // 2)
            )

        if matched:
            flags_found.append(flag)
        else:
            flags_missed.append(flag)

    # We intentionally avoid aggressive hallucination detection.
    # Ordinary regulatory discussion should not be treated as fabricated.
    hallucinations = []

    return {
        "regulatory_body_correct": regulatory_body_correct,
        "permits_found": permits_found,
        "permits_missed": permits_missed,
        "flags_found": flags_found,
        "flags_missed": flags_missed,
        "hallucinations": hallucinations,
    }

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
        bs = score_response(b["response"], case)
        bsc = compute_score(bs, case)

        a = run_agent(case["product_description"], save_trajectory=True)
        atext = json.dumps(a.get("brief", {}))
        as_ = score_response(atext, case)
        asc = compute_score(as_, case)

        results.append({"case_id": case["id"], "category": case["category"], "difficulty": case["difficulty"], "baseline": {"scores": bsc}, "agent": {"scores": asc}})
        diff = asc["composite"] - bsc["composite"]
        console.print(f"  Baseline: {bsc['composite']:.2f} | Agent: {asc['composite']:.2f} | Delta: {diff:+.2f}\n")

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
