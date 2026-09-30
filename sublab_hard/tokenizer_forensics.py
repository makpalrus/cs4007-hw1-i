"""Sublab Harder - why Kazakh costs more, and what a homoglyph does to a word.

Sublab Medium gave you six models and a table of what each one repaired. This
sublab explains part of that table, and it does it without calling any model at
all. A tokenizer is a fixed, inspectable piece of software: you can open it,
run text through it, and see exactly what the model was handed.

Two tokenizers, both real:

  cl100k_base   the GPT-4 / GPT-3.5-turbo vocabulary
  o200k_base    the newer, larger one used from GPT-4o onwards

Three measurements:

  A. the same meaning in Kazakh, Russian and English - how many tokens each
     costs, in both tokenizers;
  B. what a Latin homoglyph does to the token stream of a Kazakh word;
  C. whether the newer tokenizer narrowed the gap.

No API keys. No network at run time (tiktoken downloads its vocabulary files
once and caches them). Nothing here costs money, which means there is no excuse
for not running it several times.

Fill in every `TODO`. Do not change the function signatures.
"""

import json
import unicodedata
from pathlib import Path

import tiktoken

DATA = Path(__file__).resolve().parent.parent / "data"
PARALLEL = DATA / "parallel.json"
KAZAKH_ERRORS = DATA / "kazakh_errors.json"

# Both are real tiktoken encodings. Do not use tiktoken.encoding_for_model():
# the models in this course are newer than your installed tiktoken and it will
# not know their names.
ENCODINGS = ["cl100k_base", "o200k_base"]

LANGS = ["kk", "ru", "en"]


def load_triplets() -> list[dict]:
    """Six meanings, each written in Kazakh, Russian and English."""
    data = json.loads(PARALLEL.read_text(encoding="utf-8"))
    return data.get("triplets", data)


def load_sentences() -> list[dict]:
    """The corrupted Kazakh sentences from Sublab Medium."""
    data = json.loads(KAZAKH_ERRORS.read_text(encoding="utf-8"))
    return data.get("sentences", data)


# --------------------------------------------------------------------------
# The tokenizer itself
# --------------------------------------------------------------------------

def encode(text: str, encoding_name: str = "o200k_base") -> list[int]:
    """Token ids for `text` under the named encoding."""
    enc = tiktoken.get_encoding(encoding_name)
    return enc.encode(text)


def pieces(ids: list[int], encoding_name: str = "o200k_base") -> list[str]:
    """The text of each token, one string per id."""
    enc = tiktoken.get_encoding(encoding_name)
    result = []
    for token_id in ids:
        try:
            val = enc.decode([token_id])
        except Exception:
            val = repr(enc.decode_single_token_bytes(token_id))
        result.append(val)
    return result


# --------------------------------------------------------------------------
# Pure measurements.
# --------------------------------------------------------------------------

def tokens_per_char(text: str, ids: list[int]) -> float:
    """How many tokens each character of `text` cost."""
    if not text:
        return 0.0
    return len(ids) / len(text)


def first_divergence(a: list[int], b: list[int]) -> int | None:
    """Index of the first position where two token streams differ."""
    for idx, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return idx
    if len(a) != len(b):
        return min(len(a), len(b))
    return None


def foreign_chars(text: str) -> list[tuple[int, str, str]]:
    """Every character that is a letter but not a Cyrillic one."""
    res = []
    for idx, ch in enumerate(text):
        if ch.isalpha():
            name = unicodedata.name(ch, "")
            if "CYRILLIC" not in name:
                res.append((idx, ch, name))
    return res


# --------------------------------------------------------------------------
# A. The price of a language
# --------------------------------------------------------------------------

def language_table(encoding_name: str) -> dict[str, dict]:
    """Total tokens, total characters and tokens-per-character, per language."""
    triplets = load_triplets()
    totals = {
        lang: {"tokens": 0, "chars": 0, "tok_per_char": 0.0}
        for lang in LANGS
    }

    for trip in triplets:
        for lang in LANGS:
            text = trip[lang]
            tok_ids = encode(text, encoding_name)
            totals[lang]["tokens"] += len(tok_ids)
            totals[lang]["chars"] += len(text)

    for lang in LANGS:
        chrs = totals[lang]["chars"]
        toks = totals[lang]["tokens"]
        totals[lang]["tok_per_char"] = toks / chrs if chrs > 0 else 0.0

    return totals


def cost_per_thousand(tok_per_char: float, chars: int,
                      rate_in: float = 5.00) -> float:
    """What 1,000 sentences of this length would cost as input tokens."""
    tokens_per_sentence = tok_per_char * chars
    total_tokens = tokens_per_sentence * 1000
    return (total_tokens / 1_000_000.0) * rate_in


# --------------------------------------------------------------------------
# B. What the homoglyph did
# --------------------------------------------------------------------------

def homoglyph_report(corrupted: str, correct: str,
                     encoding_name: str = "o200k_base") -> dict:
    """Side-by-side forensics on one corrupted sentence."""
    ids_correct = encode(correct, encoding_name)
    ids_corrupted = encode(corrupted, encoding_name)

    return {
        "foreign": foreign_chars(corrupted),
        "tokens_correct": len(ids_correct),
        "tokens_corrupted": len(ids_corrupted),
        "delta": len(ids_corrupted) - len(ids_correct),
        "diverge_at": first_divergence(ids_correct, ids_corrupted),
        "pieces_correct": pieces(ids_correct, encoding_name),
        "pieces_corrupted": pieces(ids_corrupted, encoding_name),
    }


def show_homoglyphs(encoding_name: str = "o200k_base") -> None:
    """Given. Print the report for every latin_homoglyph row in the dataset."""
    rows = [r for r in load_sentences() if "latin_homoglyph" in r.get("errors", [])]
    if not rows:
        print("  no latin_homoglyph rows in the dataset")
        return
    for row in rows:
        rep = homoglyph_report(row["corrupted"], row["correct"], encoding_name)
        print("\n  [%s]  %+d tokens (%d -> %d), diverging at index %s"
              % (row["id"], rep["delta"], rep["tokens_correct"],
                 rep["tokens_corrupted"], rep["diverge_at"]))
        for idx, ch, name in rep["foreign"]:
            print("    char %d is %r - %s" % (idx, ch, name))
        d = rep["diverge_at"] or 0
        print("    correct  : %s" % rep["pieces_correct"][max(0, d - 1):d + 5])
        print("    corrupted: %s" % rep["pieces_corrupted"][max(0, d - 1):d + 5])


if __name__ == "__main__":
    print("=== A. the same six meanings, three languages, two tokenizers ===")
    for enc_name in ENCODINGS:
        table = language_table(enc_name)
        print("\n  %s" % enc_name)
        print("    %-4s %8s %8s %12s" % ("lang", "tokens", "chars", "tok/char"))
        for lang in LANGS:
            row = table[lang]
            print("    %-4s %8d %8d %12.3f"
                  % (lang, row["tokens"], row["chars"], row["tok_per_char"]))
        base = table["en"]["tok_per_char"]
        for lang in LANGS:
            print("    %s costs %.2fx English"
                  % (lang, table[lang]["tok_per_char"] / base))

    print("\n=== B. what a Latin homoglyph does to the token stream ===")
    show_homoglyphs("o200k_base")

    print("\n=== C. did the newer tokenizer narrow the gap? ===")
    old, new = (language_table(e) for e in ENCODINGS)
    for lang in LANGS:
        print("  %s: %.3f -> %.3f tok/char"
              % (lang, old[lang]["tok_per_char"], new[lang]["tok_per_char"]))
    print("\n  Now answer question 2 in SUBMISSION.md, with these numbers in hand.")