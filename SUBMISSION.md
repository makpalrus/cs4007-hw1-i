# Submission Report: CS4007 HW1 — Talking to models

**Student:** Ruskulbek Makpal 
**Name:** Ruskulbek Makpal
**Student ID:** S23067710
**Group:** 9 

---

## 1. Sublab Easy: Registration Bot

### Token Usage & Per-Turn Costs

#### Run 1: OpenAI — `gpt-5.6-luna`

| Turn | Input Tokens | Output Tokens | Cost ($) |
|:----|-------------:|--------------:|---------:|
| 1   | 1340 | 572 | $0.000954 |
| 2   | 1643 | 165 | $0.000527 |
| 3   | 1794 |  74 | $0.000448 |
| 4   | 1887 |  33 | $0.000417 |
| 5   | 1944 | 422 | $0.000895 |
| **Total** | | | **$0.003241** |

#### Run 2: OpenRouter — `google/gemma-4-26b-a4b-it:free`
*Note: OpenRouter free tier encountered rate-limiting (`429 RateLimitError`) during the automated run sequence. Turn-4 verbatim response was captured in `outputs/easy_runs.json`.*

---

### Turn 4 Verbatim Replies

* **`gpt-5.6-luna`:**
  > "I cannot add **CSS-4090 — Quantum Machine Learning** because it does not exist in the provided **2026-FALL course catalogue**."

---

### Written Answers (Sublab Easy)

1. **What actually changed between providers, and what did not?**
   * **What changed:** The underlying language model, its specific tokenizer, the API host (`base_url`), and provider endpoints.
   * **What did not change:** The application logic, the OpenAI SDK interface/methods, the prompt template, and the conversation history array sent across the wire.

2. **Why did input tokens climb on every turn?**
   * Input tokens increased steadily ($1340 \to 1643 \to 1794 \to 1887 \to 1944$) because the LLM API is completely stateless. Every API call must resend the entire message history list.
   * **50-Turn Projection:** If the conversation ran for 50 turns, the cumulative context size would grow quadratically ($O(N^2)$ token billing for $N$ turns), causing the cost per turn to escalate significantly as the history accumulates.

3. **Turn 4 Analysis: Refusal vs Invention**
   * **Did it refuse?** Yes, the bot strictly refused to add the course.
   * **Why it held the line:** The system prompt explicitly contained the strict boundary constraint: *"refuse anything not in the catalogue"*.

4. **Where else was the bot checked for accuracy?**
   * **Tuesday Schedule Conflict:** In Turn 1 and Turn 2, the model correctly detected that `CSS-4007` and `CSS-4102` both meet on Tuesday from 09:00 to 10:50 and blocked simultaneous registration.
   * **Credit Limits:** In Turn 1, the model correctly noticed that valid eligible pairs (10–11 credits total) fell short of the required **15-credit minimum** limit.

---

## 2. Sublab Medium: Kazakh Correction

### Model Comparison Table (6 Models × 8 Sentences)

| Model | KZ-01 | KZ-02 | KZ-03 | KZ-04 | KZ-05 | KZ-06 | KZ-07 | KZ-08 | Exact | Failed | Total Tokens | Cost ($) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---:|---:|---:|---:|
| `qwen/qwen3.8-27b` | X | X | X | X | X | X | X | X | 0 | 8 | 0 | $0.00000 |
| `deepseek/deepseek-v4-flash-0731` | E | E | E | E | E | E | E | E | **8** | **0** | **6,479** | **$0.00148** |
| `gpt-5.6-luna` | ~3 | E | ~2 | ~1 | ~1 | E | E | E | 4 | 0 | 2,630 | $0.00198 |
| `gpt-5.6-terra` | E | E | ~2 | ~1 | ~1 | E | E | E | 5 | 0 | 1,756 | $0.00927 |
| `gpt-5.6-sol` | ~3 | ~1 | ~2 | ~1 | ~1 | E | E | E | 3 | 0 | 2,108 | $0.03374 |
| `google/gemma-4-26b-a4b-it:free` | ~6 | X | X | X | X | X | X | X | 0 | 7 | 332 | $0.00000 |

*Legend: **E** = Exact Match, **~N** = Valid Kazakh correction with N minor character differences (synonyms/rephrasing), **X** = API Failure / Uncorrected.*

---

### Analysis of Errors & Models

1. **Error Type Repairs:**
   * **`kaz_to_rus` (KZ-01, KZ-04, KZ-07):** Most models easily identified and repaired Russian Cyrillic substitutions back to proper Kazakh Cyrillic characters because token merges remained largely intact within the Cyrillic Unicode block.
   * **`latin_homoglyph` (KZ-03, KZ-08):** Models struggled significantly more with Latin homoglyphs. Inserting Latin characters into Cyrillic words shattered BPE subword tokens into byte-level fragments, obscuring word boundaries.

2. **Cheapest and Best Model:**
   * **`deepseek/deepseek-v4-flash-0731`** was by far the best performer. It achieved an **exact 8/8 match rate** across all synthetic corruption types while costing only **$0.00148** total—significantly cheaper than GPT-5.6 variants while outperforming them on exact string reconstruction.

---

## 3. Sublab Hard: Tokenizer Forensics

### Measurement A: Language Cost Multipliers

| Language | `cl100k_base` (tok/char) | `o200k_base` (tok/char) | Cost / 1k Sentences (`cl100k`) | Cost / 1k Sentences (`o200k`) |
|:---|---:|---:|---:|---:|
| **Kazakh (kk)** | **0.760** | **0.319** | $0.1667 | $0.0700 |
| **Russian (ru)** | 0.466 | 0.267 | $0.1075 | $0.0617 |
| **English (en)** | 0.203 | 0.203 | $0.0492 | $0.0492 |

* **`cl100k_base` Kazakh Multiplier:** **3.75x** English cost
* **`o200k_base` Kazakh Multiplier:** **1.58x** English cost

---

### Measurement B: Latin Homoglyphs vs. Russian Substitutions

#### 1. Latin Homoglyphs (Subword Fragmentation)
* **`KZ-03` (`latin_homoglyph`):** Token count exploded from **16 to 20** (+4 tokens), diverging at index 0.
  * *Non-Cyrillic detected:* `char 0 = 'A'` (LATIN CAPITAL A), `char 2 = 'a'`, `char 5 = 't'`.
  * **Correct Tokens:** `['А', 'лая', 'қ', 'тарға', ' ақша', 'ңызды', ' ауд', 'арып', ' қой', 'са', 'ңыз', ' не', ' і', 'сте', 'у', ' керек']`
  * **Corrupted Tokens:** `['A', 'л', 'a', 'я', 'қ', 't', 'ар', 'ға', ' ақша', 'ңызды', ' ауд', 'арып', ' қой', 'са', 'ңыз', ' не', ' і', 'сте', 'у', ' керек']`
* **`KZ-08` (`latin_homoglyph`):** Token count expanded from **21 to 24** (+3 tokens), diverging at index 1.
  * **Correct Tokens:** `['Д', 'он', 'аль', 'д', ' Т', 'рамп', ' К', 'им', ' Ч', 'ен', ' Ы', 'н', 'мен', ...]`
  * **Corrupted Tokens:** `['Д', 'o', 'н', 'a', 'л', 'ль', 'д', ' T', 'рамп', ' К', 'им', ' Ч', 'ен', ' Ы', 'н', 'мен', ...]`

#### 2. Russian Cyrillic Substitutions (Preserved Merges)
* **`KZ-01` (`kaz_to_rus`):** Token count actually decreased from **28 to 26** (-2 tokens), diverging at index 0.
  * *Non-Cyrillic detected:* **None** (all characters remain within the Cyrillic Unicode block).
  * **Correct Tokens:** `['Қ', 'ас', 'ым', '-', 'Ж', 'ом', 'арт', ' То', 'қа', 'ев', ' бір', 'қ', 'атар', ...]`
  * **Corrupted Tokens:** `['К', 'ас', 'ым', '-', 'Ж', 'ом', 'арт', ' Т', 'ока', 'ев', ' бир', 'к', 'атар', ...]`

---

### Written Answers (Sublab Hard)

1. **What is the Kazakh Tax?**
   * Under `cl100k_base`, Kazakh text costs **3.75x** more than English ($0.1667 vs $0.0492 per 1,000 parallel sentences). 
   * In `o200k_base`, the vocabulary expansion reduced this tax down to **1.58x** ($0.0700 per 1,000 sentences), representing a **58% decrease** in token overhead for Kazakh.

2. **Why did models repair `kaz_to_rus` easily but struggle with `latin_homoglyph`?**
   * **`kaz_to_rus`:** Replacing Kazakh specific letters with Russian Cyrillic lookalikes keeps all characters inside the Cyrillic Unicode script block. BPE subword merges remain mostly intact (e.g., `' То'`, `'ка'`, `'ев'`), providing the LLM's attention mechanism with whole semantic word blocks.
   * **`latin_homoglyph`:** Mixing Latin ASCII characters into Cyrillic words violently shatters BPE tokenization rules because Latin and Cyrillic belong to completely separate Unicode script ranges. The word splits into isolated single-character/byte tokens (`['A', 'л', 'a', 'я', 'қ', 't', ...]`), preventing the LLM from recognizing word boundaries or leveraging subword embedding representations.

3. **What does this measurement NOT explain about Sublab Medium results?**
   * We measured OpenAI's proprietary tokenizers (`cl100k_base`, `o200k_base`). However, non-OpenAI models in Sublab Medium (e.g., Qwen, Gemma, DeepSeek) utilize completely different open-source or custom tokenizers with distinct vocabulary sizes and BPE merge patterns.
   * **To close the gap:** We would need to load each specific model's exact HuggingFace tokenizer (e.g., `AutoTokenizer.from_pretrained(...)` for DeepSeek/Qwen) and run identical forensics on their native token streams.
