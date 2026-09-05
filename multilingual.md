# Multilingual Ingestion: Translate-to-English-at-Ingest Architecture

## Goal
Replace the current parallel-language-manuals design (separate MX-7 entries for English, Chinese, Japanese, German) with a single canonical English knowledge base per machine. Any manual, regardless of source language, is translated to English at ingestion time before chunking and embedding. The original-language PDF is retained for human reading in the PDF viewer, but retrieval always happens against English chunks in one embedding space.

Optionally, add query-side translation so a technician can type a question in another language and still retrieve correctly against the English corpus.

---

## 1. Problem With the Current Design

Today, `data/manuals/` and the vector store contain **separate, independently embedded copies** of the same physical machine's manual:

- CNC Milling Machine MX-7 — English
- 数控铣床 MX-7 说明书 — Simplified Chinese
- CNCフライス盤 MX-7 取扱説明書 — Japanese
- CNC-Fräsmaschine MX-7 Handbuch — German
- "Multilingual Instruction Manual" / "Multilingual Machine Instruction Manual (All 4 Languages)" — bolted-on aggregate entries

This causes three concrete problems:

1. **Fragmented retrieval.** A query only matches well against chunks in the same language it was written in (unless the embedding model is explicitly multilingual and calibrated for cross-lingual similarity, which ours is not verified to be). An English query will not reliably surface the Chinese-manual chunks even if that manual has the more complete answer.
2. **4x the storage and chunk count for one machine**, with no retrieval benefit — this is duplication, not multilingual support.
3. **No actual cross-language capability.** The current setup *looks* multilingual in the UI (four flags, four manual cards) but doesn't do the thing the original PS bonus describes: a query in one language retrieving information regardless of what language the source manual was written in.

---

## 2. Target Architecture

```
Source PDF (any language)
        │
        ▼
  pypdf text extraction
        │
        ▼
  Language detection (source_language: "zh" | "ja" | "de" | "en" | ...)
        │
        ▼
  Translation to English (Gemini, same call that structures the manual)
        │
        ▼
  Structuring into spec format (MACHINE / SECTION / ERROR CODE / etc.)
        │
        ▼
  Human-in-the-loop review (technician sees English draft + can edit)
        │
        ▼
  Chunking (English only)
        │
        ▼
  Embedding (single embedding space, English only)
        │
        ▼
  ChromaDB (one set of chunks per machine)
```

The original PDF bytes are still saved to `data/manuals/<machine>.pdf` for the PDF Reader view, tagged with `source_language`. Only ONE manual entry exists per physical machine, not one per language.

Query-side translation (optional bonus layer) sits in front of the existing retrieval/safety pipeline and does not change any gate logic already implemented in `src/safety.py`:

```
User query (any language)
        │
        ▼
  Language detection
        │
        ▼
  Translate query → English   (if not already English)
        │
        ▼
  [existing pipeline, unchanged: Gate 1-5, retrieval, confidence]
        │
        ▼
  Answer generated in English
        │
        ▼
  Translate answer → user's language   (optional, if source was non-English)
        │
        ▼
  Response shown to user, with English citations + page refs preserved
```

---

## 3. Architecture & Separation of Concerns

### RAG Vector Retrieval (ChromaDB)
Only **canonical structured English manuals** are embedded into the ChromaDB vector store:
- `cncmx7.txt` — 20 verified chunks for CNC Milling Machine MX-7 Precision
- `conveyorcb4400.txt` — 20 verified chunks for Conveyor Belt System CB-4400
- `presshp2200.txt` — 20 verified chunks for Hydraulic Press HP-2200
- `robotarm_300.txt` — 6 verified chunks for RobotArm-300
Total: 66 high-fidelity canonical chunks in a single English embedding space.

Redundant language text dumps (`multilingual_manual_zh.txt`, `ja.txt`, `de.txt`) are excluded from vector embedding to eliminate chunk dilution, cross-lingual score distortion, and 4x retrieval fragmentation.

### Interactive UI Manual Viewer (`/api/manuals/multilingual`)
The flagship 9-section multilingual manual (`src/multilingual_manual_data.py`) remains available via `GET /api/manuals/multilingual?lang=...` and `frontend/src/App.tsx`. Operators and judges can switch between English, Simplified Chinese, Japanese, and German tabs in the UI to inspect specifications, safety instructions, and operating procedures in their native language.

---

## 4. Ingestion & Normalization Implementation

### `src/llm_answer.py` — Unconditional Translation & Structuring
- `PDF_STRUCTURING_SYSTEM_PROMPT` unconditionally enforces English output:
  1. If the source manual text is in Chinese, Japanese, German, or any other non-English language, Gemini translates all descriptions, error meanings, causes, and corrective action steps into clear, professional technical English during structuring.
  2. All numeric values, thresholds, units (`94°C`, `24,000 RPM`, `400V`, `32A`, `6.5 bar`, `18 bar`, `0.015 mm`), and error codes (`E101`, `SYM-OVERHEAT`) are copied character-for-character with zero mutation.
  3. Anti-fabrication rule: All error codes in structured output must exist in the source document ($\text{Codes}_{\text{output}} \subseteq \text{Codes}_{\text{source}}$).

### `src/ingest.py` — NFKC Unicode Normalization
- Added `unicodedata.normalize('NFKC', content)` in `parse_manual_text()` to normalize full-width CJK characters (`Ｅ１０１` $\to$ `E101`, `９４°Ｃ` $\to$ `94°C`, full-width space) into standard ASCII before chunking and embedding.

### `src/api.py` — Document-Level Language Sampling
- In `upload_manual`, extracts text and samples the first **2,500 non-empty characters** of substantive body text (lines with $\ge 4$ words) from Pages 1–2.
- Runs `_module_instance.detect_language()` from `src/translation.py`.
- Returns `source_language`, `detected_language`, and `is_translated` in `ManualUploadResponse`.

### `src/safety.py`, `src/retrieval.py`, `src/confidence.py`
- These modules only ever see English text (native or translated). The strict hallucination controls (Gates 0–5) are fully preserved. Foreign gibberish and noise queries (Katakana mash, Cyrillic mash, German consonant mash) are rejected cleanly.

---

## 5. Frontend Changes

### `frontend/src/App.tsx` — Manuals Library
- Remove the "Multilingual Instruction Manual" cards entirely.
- Each machine now has exactly one card. Add a small language badge (e.g. "EN", "ZH → EN", "JA → EN") next to the manual title to indicate the source language, without implying there are multiple separate manual entries.
- The PDF Reader view for a non-English-sourced manual still shows the **original-language PDF** (technician can read it in the source language). The RAG Chunks view shows the English structured/chunked content used for retrieval.

### Upload modal (`PdfUploadModal.tsx`)
- Update status messages during upload to reflect the new step, e.g.:
  - "Extracting text with pypdf..."
  - "Detecting language..."
  - "Translating to English..." (only shown if source is non-English)
  - "Structuring with Gemini..."
- The review studio always displays the English structured draft, with a small note if translation occurred ("Translated from Chinese — verify technical terms are accurate before approving").

### Optional: query input
- If implementing query-side translation as a demo feature, no UI change is strictly required — the chat input can accept any language as-is. Consider adding a subtle note under the answer like "Translated from [detected language]" if the query wasn't in English, for demo transparency.

---

## 6. Verification Plan

### Ingestion correctness
1. Take one existing non-English manual (e.g. the Japanese MX-7 PDF).
2. Run it through the updated ingestion pipeline.
3. Confirm: `source_language` metadata is set correctly, the structured draft shown for review is in English, and the resulting chunks in ChromaDB are English text.
4. Confirm the original Japanese PDF is still viewable in the PDF Reader.

### Retrieval correctness (the actual point of this change)
1. Query in English: `"Why is the CNC-100 spindle overheating?"` → should retrieve correctly regardless of whether the source manual was originally English, Chinese, Japanese, or German.
2. Confirm there is only **one** MX-7 entry in `/api/manuals`, not four.
3. Confirm chunk count for MX-7 reflects one manual's worth of content, not the sum of four language copies.

### Query-side translation — regression-check the existing feature, don't rebuild it
1. Re-run `tests/test_translation_module.py` as a baseline before touching anything — confirm current behavior for Chinese/Japanese/German queries still passes.
2. Submit a query in a non-English language (e.g. Chinese: 为什么主轴过热) → confirm it's detected, translated via `translate_input`, correctly routed through Gates 1–5, and returns the same answer content as the English-equivalent query would.
3. Confirm citations (manual name, section, page) remain in their original form (not translated into nonsense) — check this against the current `/query` implementation, since it may already handle this correctly.
4. **New test to add**: run gibberish through translation first (e.g. a nonsense string typed in Chinese characters) and confirm Gate 5's noise floor still correctly refuses after translation — a bad or overly literal translation of gibberish should not accidentally produce real-looking English domain vocabulary that slips past the floor. This wasn't a risk before because gate-hardening (this conversation's earlier work) was only tested against English gibberish.

### Migration completeness
1. Confirm no unique content from the four now-merged language-specific manuals was lost (diff check per Section 3).
2. Confirm the old "Multilingual Instruction Manual" and "All 4 Languages" pseudo-entries no longer appear anywhere in `/api/manuals` output or the frontend UI.

### Regression
- Re-run full existing suite: `tests/test_translation_module.py`, `tests/test_confidence_scoring.py`, `tests/test_manual_endpoints.py`, `tests/test_rigorous.py`, `tests/test_gibberish_and_offtopic.py`.
- `npm run build` in `frontend/`.

---

## 7. Demo Framing

For judges, this is a stronger story than "we support 4 languages" — it's:

> "It doesn't matter what language the source manual is written in — our system normalizes everything into a single knowledge base at ingestion time, so retrieval quality doesn't fragment across languages. And if you ask a question in a different language than the manual was written in, we translate the query, run it through the same hallucination-controlled retrieval pipeline, and translate the answer back — with citations still pointing at the exact original-language page."

This also directly answers the PS's bonus mention of multilingual queries ("Machine heat aagtha ide, yen problem?") in a way that's architecturally honest rather than a UI trick.
