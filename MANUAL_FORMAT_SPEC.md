# Manual Section-Format Spec

This is the required text format for every manual file in `data/manuals/`. `src/ingest.py` parses files by matching these exact labels — deviating from this format (different label names, missing colons, inconsistent casing) will break chunking and citations. Read this fully before writing any manual content.

## File basics

- One file per machine, plain `.txt`
- Filename convention: lowercase, no spaces — e.g. `cnc100.txt`, `press200.txt`
- UTF-8 encoding, no special formatting (no Markdown, no bullet symbols beyond plain `-` or `1.`)

## Required structure

Every manual file follows this exact skeleton:

```
MACHINE: <machine name>
MODEL: <model name>

ERROR CODE: <code>
SECTION: <section name>
PAGE: <page number>
MEANING: <one or two sentence meaning of the error>
CAUSES:
- <cause 1>
- <cause 2>
- <cause 3>

SECTION: <section name>
PAGE: <page number>
STEPS:
1. <step 1>
2. <step 2>
3. <step 3>

ERROR CODE: <next code>
...repeat the block above for each error code...
```

## Field-by-field rules

| Field | Rules | Why it matters |
|---|---|---|
| `MACHINE:` | Appears **once**, at the very top of the file. Exact machine name, consistent across every mention of this machine anywhere in the system (dropdown, query understanding, disambiguation). | This becomes the `machine` metadata tag on every chunk from this file. If it's inconsistent (e.g. "CNC-100" here but "CNC 100" elsewhere), machine-filtering breaks. |
| `MODEL:` | Appears once, right after `MACHINE:`. | Attached as `model` metadata — optional detail shown in citations. |
| `ERROR CODE:` | One per error code block. Format: a letter followed by digits, e.g. `E101`. Use the **exact same code string** if it's deliberately duplicated across two machines (this is required for at least one code — see below). | This becomes the `error_code` metadata field. The disambiguation logic matches on exact string equality. |
| `SECTION:` | Starts a new chunk. Every error code needs **at least two** `SECTION:` blocks — one for meaning/causes, one for troubleshooting steps. Section names should be descriptive, e.g. `Error Codes` or `E101 Troubleshooting`. | Each `SECTION:` block becomes one retrievable chunk. This is also the label shown in citations, so make section names readable — a technician will see "Source: § E101 Troubleshooting" in the UI. |
| `PAGE:` | A plain integer. Doesn't need to be real/sequential across the whole document — just needs to be present and consistent within a file. | Displayed directly in citations ("Page 214"). Missing this field means citations show no page number, which weakens the traceability requirement. |
| `MEANING:` | One or two plain sentences. No jargon beyond what a technician would recognize. | This is the exact text used to answer "what does this error mean" — write it clearly, since it may be quoted close to verbatim in generated answers. |
| `CAUSES:` | A `-`-prefixed list, 2-4 items, one cause per line. | Feeds directly into the "Probable causes" section of every generated answer. |
| `STEPS:` | A numbered list (`1.`, `2.`, `3.`...), one imperative action per line. | Feeds directly into the "Step-by-step corrective action" section. Steps should be concrete and orderable — no vague instructions like "check the system." |

## Two mandatory data-design requirements

These aren't optional — the whole point of the dataset is to demonstrate the system handles them correctly.

**1. Exactly one error code must appear in 2+ manuals with genuinely different meanings.**
Example: `E101` = "excessive motor temperature" in `cnc100.txt`, but `E101` = "hydraulic pressure below threshold" in `press200.txt`. Use the identical code string in both files. This is what triggers the disambiguation demo.

**2. At least one topic must be deliberately undocumented across every manual.**
Pick something a technician might plausibly ask about that you never write a `SECTION:` block for in any file — e.g. "how to replace the motor bearing." Never mention it anywhere. This is what triggers the "insufficient information" refusal demo. Do not accidentally include a stray sentence about it anywhere, even in passing — that would leak partial info and weaken the refusal demo.

## Worked example (copy this pattern exactly)

```
MACHINE: CNC-100
MODEL: X200

ERROR CODE: E101
SECTION: Error Codes
PAGE: 214
MEANING: E101 indicates excessive motor temperature.
CAUSES:
- Cooling fan failure
- Blocked ventilation
- Excessive machine load

SECTION: E101 Troubleshooting
PAGE: 215
STEPS:
1. Switch off the machine.
2. Inspect the cooling fan for obstruction or failure.
3. Check ventilation openings for blockages.
4. Allow the motor to cool before restarting.

ERROR CODE: E204
SECTION: Error Codes
PAGE: 220
MEANING: E204 indicates a spindle overload.
CAUSES:
- Excessive cutting load
- Worn spindle bearing
- Incorrect feed rate

SECTION: E204 Troubleshooting
PAGE: 221
STEPS:
1. Stop the spindle.
2. Reduce the feed rate.
3. Inspect the spindle bearing for wear.
4. Restart and monitor spindle load.
```

## Before you start writing

Confirm with the coder (me/you) once you've drafted the first manual — a 5-minute check that `ingest.py` parses it correctly before you write the remaining 2-3 manuals in the same session. Catching a format mismatch after all 4 manuals are written means redoing all of them; catching it after the first one costs nothing.
