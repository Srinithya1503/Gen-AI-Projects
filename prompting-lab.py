"""
╔══════════════════════════════════════════════════════════════╗
║          PROMPT VERSIONING LAB — Anthropic SDK               ║
║  Scientifically compare V1 (Simple) vs V2 (Engineered)       ║
╚══════════════════════════════════════════════════════════════╝
"""

import csv
import time
import anthropic

# ─────────────────────────────────────────────
# 1.  TEST CASES
# ─────────────────────────────────────────────
TEST_CASES = [
    {
        "id": "TC-01",
        "input": "hi its me sarah johnson, can u call me back pls? thx",
    },
    {
        "id": "TC-02",
        "input": "Meeting w/ DR. EMILY CHEN & mr. david park @ 3pm tomorrow!!",
    },
    {
        "id": "TC-03",
        "input": "fwd: james o'brien left a voicemail... also ANNA KOWALSKI called twice",
    },
    {
        "id": "TC-04",
        "input": "From: m.rodriguez@acme.com — Maria Rodriguez needs the report ASAP",
    },
    {
        "id": "TC-05",
        "input": "cc: Tom W., Lisa Hernandez-Ruiz, and someone named 'B. Singh' ??",
    },
]

# ─────────────────────────────────────────────
# 2a. V1 — SIMPLE PROMPT
# ─────────────────────────────────────────────
PROMPT_V1_TEMPLATE = """Extract all person names from the text below.
Return them as a comma-separated list.

Text: {input}"""

# ─────────────────────────────────────────────
# 2b. V2 — ENGINEERED PROMPT
#   • Role Persona
#   • XML structure tags
#   • 2 few-shot examples
# ─────────────────────────────────────────────
PROMPT_V2_TEMPLATE = """You are NameExtractorGPT, a precise information-extraction assistant \
specialised in identifying and normalising human names from noisy, informal text. \
Your output is always a clean JSON array of full names — nothing else.

<instructions>
  1. Read the <input> text carefully.
  2. Identify every person's name, even if abbreviated, ALL-CAPS, or hyphenated.
  3. Normalise to Title Case (e.g. "EMILY CHEN" → "Emily Chen").
  4. Include honorifics only if they are part of the name token (e.g. "Dr." when attached).
  5. Return ONLY a JSON array, e.g. ["Alice Smith", "Bob Jones"]. No prose, no markdown.
</instructions>

<examples>
  <example>
    <input>Called by JANET LEE and mr. kevin o'hara earlier today</input>
    <output>["Janet Lee", "Kevin O'Hara"]</output>
  </example>
  <example>
    <input>fwd from: p.nguyen@corp.com — Phuong Nguyen & SARA EL-AMIN need access</input>
    <output>["Phuong Nguyen", "Sara El-Amin"]</output>
  </example>
</examples>

<input>{input}</input>"""


# ─────────────────────────────────────────────
# 3.  RUNNER
# ─────────────────────────────────────────────
def run_prompt(client: anthropic.Anthropic, prompt_text: str) -> tuple[str, float]:
    """Call Claude and return (output_text, latency_seconds)."""
    start = time.perf_counter()
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=256,
        messages=[{"role": "user", "content": prompt_text}],
    )
    latency = round(time.perf_counter() - start, 3)
    output = message.content[0].text.strip()
    return output, latency


def run_experiment(output_csv: str = "results.csv") -> None:
    """Run all test cases against both prompt versions and write results to CSV."""
    client = anthropic.Anthropic()          # reads ANTHROPIC_API_KEY from env
    rows: list[dict] = []

    versions = {
        "V1_Simple":     PROMPT_V1_TEMPLATE,
        "V2_Engineered": PROMPT_V2_TEMPLATE,
    }

    print(f"\n{'─'*60}")
    print(f"  {'Test ID':<10} {'Version':<18} {'Latency':>8}   Output")
    print(f"{'─'*60}")

    for tc in TEST_CASES:
        for version_name, template in versions.items():
            prompt_text = template.format(input=tc["input"])
            output, latency = run_prompt(client, prompt_text)

            rows.append({
                "Test_ID":        tc["id"],
                "Prompt_Version": version_name,
                "Output":         output,
                "Latency":        latency,
            })

            # Truncate output for console display
            display_out = (output[:55] + "…") if len(output) > 55 else output
            print(f"  {tc['id']:<10} {version_name:<18} {latency:>7}s   {display_out}")

    print(f"{'─'*60}\n")

    # Write CSV
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Test_ID", "Prompt_Version", "Output", "Latency"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅  Results saved → {output_csv}  ({len(rows)} rows)\n")

    # Quick summary stats
    v1_rows = [r for r in rows if r["Prompt_Version"] == "V1_Simple"]
    v2_rows = [r for r in rows if r["Prompt_Version"] == "V2_Engineered"]

    avg = lambda lst: round(sum(r["Latency"] for r in lst) / len(lst), 3)
    print("  📊 Latency Summary")
    print(f"     V1 Simple      avg: {avg(v1_rows)}s")
    print(f"     V2 Engineered  avg: {avg(v2_rows)}s\n")


# ─────────────────────────────────────────────
# 4.  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    run_experiment()
