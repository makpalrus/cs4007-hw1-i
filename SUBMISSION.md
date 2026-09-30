# Submission Report: CS4007 HW1

## Sublab Easy: Registration Bot

### Token Usage & Costs

| Turn | Input Tokens | Output Tokens | Cost ($) |
|------|-------------:|--------------:|---------:|
| 1    |         1155 |           211 | 0.000300 |
| 2    |         1387 |            57 | 0.000242 |
| 3    |         1468 |            96 | 0.000278 |
| 4    |         1584 |            53 | 0.000269 |
| 5    |         1662 |           257 | 0.000403 |
| **Total** | | | **$0.001493** |

### Observations
1. **Context Accumulation:** Input tokens grew from 1,155 on Turn 1 to 1,662 on Turn 5 because the API requires passing full conversation history on every turn.
2. **Refusal Behavior:** In Turn 4, the system prompt instruction successfully forced the bot to refuse adding `CSS-4090 Quantum Machine Learning`, stating that it does not exist in the official course catalogue.
3. **Language Difference:** Turn 5 (Russian/Kazakh text) yielded higher output tokens (257) compared to the equivalent English Turn 1 (211 tokens) due to tokenization efficiency differences for Cyrillic scripts.

---

## Sublab Medium: Kazakh Correction

### Model Comparison Results

| Model | Exact Matches | Failures | Total Tokens | Cost ($) |
|-------|--------------:|---------:|-------------:|---------:|
| `gpt-4o-mini` | 7 / 8 | 0 | 1,621 | $0.00044 |
| `gpt-3.5-turbo` | 1 / 8 | 0 | 3,149 | $0.00229 |

### Analysis
- **`gpt-4o-mini`** demonstrated exceptional accuracy on Kazakh grammar and orthography, achieving 7 exact string matches while maintaining significantly lower token usage and cost.
- **`gpt-3.5-turbo`** struggled with exact character-for-character reconstruction (1 exact match) and produced longer responses, nearly doubling token consumption and cost.

---

## Sublab Hard: Tokenizer Forensics

### 1. Language Cost Multipliers

| Tokenizer | Kazakh (tok/char) | Russian (tok/char) | English (tok/char) | Kazakh Multiplier |
|-----------|------------------:|------------------:|------------------:|------------------:|
| `cl100k_base` | 0.760 | 0.466 | 0.203 | **3.75x** English |
| `o200k_base`  | 0.319 | 0.267 | 0.203 | **1.58x** English |

### 2. Analysis of Results

#### Q1: Why does Kazakh cost more than English?
The `cl100k_base` vocabulary was heavily optimized for English text. Cyrillic and non-Latin characters (especially specific Kazakh letters like `ә, ғ, қ, ң, ө, ұ, ү, һ, і`) were frequently split into character-level or byte-level tokens, requiring up to **3.75x** more tokens to represent the exact same semantic content as English.

#### Q2: Did `o200k_base` narrow the gap?
Yes, substantially. `o200k_base` expanded its vocabulary size significantly, reducing Kazakh token density from **0.760 tok/char to 0.319 tok/char**. This narrowed the cost penalty relative to English from **3.75x down to 1.58x**.

#### Q3: What do Latin homoglyphs do to the token stream?
When Latin letters (e.g., Latin 'A', 'a', 'o', 't') are mixed into Cyrillic Kazakh words, the BPE tokenizer fails to match whole-word vocabulary tokens.
- **KZ-03:** Inserting Latin 'A', 'a', 't' broke token merge rules and inflated token count from 16 to 20 (+4 tokens).
- **KZ-08:** Inserting Latin 'o', 'a', 'T' caused early divergence at index 1 and increased token count from 21 to 24 (+3 tokens).
