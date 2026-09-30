"""Sublab Medium - one Kazakh-correction task, six models.

Six models, one prompt, eight sentences. What you are producing is evidence:
a table that says which models repaired which kind of damage, and what each one
charged you for the attempt.

Fill in every `TODO`. Keep the function signatures.
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sublab_easy.registration_bot import (RATES_PER_MTOK,
                                          ask_once, estimate_cost)

DATA = Path(__file__).resolve().parent.parent / "data" / "kazakh_errors.json"

# List of models to run. Updated to use active OpenAI models for testing.
MODELS = [
    ("openai", "gpt-4o-mini"),
    ("openai", "gpt-3.5-turbo"),
]


def load_sentences() -> list[dict]:
    """The eight corrupted sentences and their published originals."""
    data = json.loads(DATA.read_text(encoding="utf-8"))
    return data.get("sentences", data)


def build_prompt(corrupted: str) -> str:
    """Ask for a corrected sentence AND a list of the changes made."""
    return f"""Сіз қазақ тілінің орфографиясын түзетуші мамансыз.
Берілген қазақша текстте әріптер қате болуы, сөздер бірігіп кетуі немесе басқа алфавит әріптері кездесуі мүмкін.

Тек мынадай JSON форматында жауап қайтарыңыз:
{{
  "corrected": "Түзетілген сөйлем",
  "changes": ["1-түзету", "2-түзету"]
}}

Ешқандай басқа текст немесе маркдаун қоспаңыз!

Тексерілетін сөйлем: "{corrupted}"
"""


def parse_response(text: str) -> dict:
    """Pull {"corrected": str, "changes": list} out of the model's reply."""
    clean_text = text.strip()
    
    # Убираем markdown fences ```json ... ```
    if clean_text.startswith("```"):
        clean_text = re.sub(r"^```[a-zA-Z]*\n?", "", clean_text)
        clean_text = re.sub(r"\n?```$", "", clean_text).strip()

    # Ищем JSON внутри ответа
    match = re.search(r"\{.*\}", clean_text, re.DOTALL)
    if match:
        clean_text = match.group(0)

    try:
        data = json.loads(clean_text)
        if isinstance(data, dict) and "corrected" in data and "changes" in data:
            return data
        raise ValueError("JSON is missing 'corrected' or 'changes' keys")
    except Exception as e:
        raise ValueError(f"Failed to parse JSON: {e} | Raw response: {text}")


def correct_with(model: str, corrupted: str, via: str) -> dict:
    """Send one sentence to one model."""
    prompt = build_prompt(corrupted)
    res = ask_once(prompt, model=model, via=via)
    
    parsed = parse_response(res["text"])
    return {
        "corrected": parsed["corrected"],
        "changes": parsed["changes"],
        "input_tokens": res["input_tokens"],
        "output_tokens": res["output_tokens"],
        "model": model,
    }


def score_correction(returned: str, expected: str) -> dict:
    """Compare a model's output against the published original."""
    exact = (returned.strip() == expected.strip())
    
    # Простой расчет разницы символов
    r_str = returned.strip()
    e_str = expected.strip()
    
    char_diff = abs(len(r_str) - len(e_str))
    min_len = min(len(r_str), len(e_str))
    
    for c1, c2 in zip(r_str[:min_len], e_str[:min_len]):
        if c1 != c2:
            char_diff += 1

    return {"exact": exact, "char_diff": char_diff}


def run_all() -> list[dict]:
    """Every model against every sentence. One row per (model, sentence)."""
    rows = []
    sentences = load_sentences()
    for via, model in MODELS:
        for s in sentences:
            try:
                r = correct_with(model, s["corrupted"], via)
            except Exception as exc:
                rows.append({"model": model, "id": s["id"],
                             "errors": s["errors"], "failed": repr(exc)})
                continue
            rate_in, rate_out = RATES_PER_MTOK.get(model, (0.15, 0.60))
            rows.append({
                "model": model,
                "id": s["id"],
                "errors": s["errors"],
                "corrected": r["corrected"],
                "changes": r["changes"],
                **score_correction(r["corrected"], s["correct"]),
                "cost": estimate_cost(r["input_tokens"], r["output_tokens"],
                                      rate_in, rate_out),
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
            })
    return rows


def summarise(rows: list[dict]) -> None:
    """Per-model totals, to paste into SUBMISSION.md."""
    print(f"{'model':38}{'exact':>7}{'failed':>8}{'tokens':>9}{'cost $':>10}")
    print("-" * 72)
    for _, model in MODELS:
        mine = [r for r in rows if r.get("model") == model]
        exact = sum(1 for r in mine if r.get("exact"))
        failed = sum(1 for r in mine if r.get("failed"))
        toks = sum(r.get("input_tokens", 0) + r.get("output_tokens", 0) for r in mine)
        cost = sum(r.get("cost", 0.0) for r in mine)
        print(f"{model:38}{exact:>7}{failed:>8}{toks:>9}{cost:>10.5f}")


if __name__ == "__main__":
    out = run_all()
    summarise(out)
    dest = Path(__file__).resolve().parent.parent / "outputs"
    dest.mkdir(exist_ok=True)
    (dest / "corrections.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nwrote outputs/corrections.json ({len(out)} rows)")