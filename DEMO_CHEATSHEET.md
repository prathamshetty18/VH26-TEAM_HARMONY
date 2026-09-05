# MachineAssist — Demo Day Q&A Cheat Sheet

## 1. Safety Gate Formula (Deterministic Pre-Filter)

$$\text{PASS} \iff \text{error\_code\_valid} \land \Big(\text{similarity} \ge 0.50 \lor \big(0.35 \le \text{similarity} < 0.50 \land \text{content\_token\_overlap} \ge 40\%\big)\Big)$$

- **Hard Floor Band ($\text{score} < 0.35$)**: Rejects ungrounded or out-of-domain questions immediately.
- **Borderline Similarity Band ($0.35 \le \text{score} < 0.50$)**: Requires $\ge 40\%$ content keyword overlap to rescue valid terse queries while stopping incidental keyword drift.
- **High Semantic Match Band ($\text{score} \ge 0.50$)**: Bypasses keyword requirements to support natural-language paraphrases (*"getting extremely hot"* $\rightarrow$ *"excessive motor temperature"*).

---

## 2. Architectural Design Principles (1-Sentence Answers)

- **Why Disambiguation Exists**: Disambiguation prevents silent guessing when identical error codes (e.g. `E101`) exist across multiple machines with completely different meanings and repair procedures.
- **Why Safety Gates Run Before the LLM**: Deterministic pre-filter gates run before LLM invocation to eliminate latency, reduce API costs, and guarantee zero hallucination for out-of-domain queries or malformed error codes.
- **Why Two Lines of Defense**: Deterministic pre-filters catch score/code failures early, while the second-line LLM safety net catches subtle details absent from retrieved chunks (such as missing torque or viscosity specifications).

---

## 3. Combined Test Suite Status

- **Fast Unit Tests (Mocked)**: **57 / 57 PASSED** (100% pass rate, 17.24s execution time)
- **Live-API Integration Tests (Gemini 3.6 Flash)**: **5 / 5 Refusal & Safety Net Invariants PASSED** (100% self-refusal consistency across repeated Demo 5 runs & parameter bypass queries). 1 Positive Control test passes cleanly when under the Gemini Free Tier 20 requests/day limit.
- **Error Handling Invariant**: Verified that 429 Rate Limit / API errors gracefully trigger `REFUSAL_MESSAGE` fallback without server crashes or raw stack traces.

---

## 4. Key Judge Question & Golden Answer

> **Judge Question:** *"How do you know your LLM won't just make something up when a manual lacks specific details?"*
>
> **Golden Answer:** *"We empirically validated our second-line safety net with Demo 5 — a query asking for an electrical torque spec that scored 0.5158 similarity and passed all pre-filters, where Gemini Flash strictly self-refused using our exact refusal string rather than inventing a number."*
