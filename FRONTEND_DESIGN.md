# FRONTEND_DESIGN.md — UI/UX Specification for MachineAssist

## 1. Design Philosophy & Industrial Ergonomics

MachineAssist is designed specifically for **factory floor technicians, automation engineers, and maintenance operators**.
In high-stress, fast-paced industrial environments, software must prioritize:
1. **Zero Ambiguity**: Clear distinction between verified facts and machine ambiguity.
2. **Speed & Scannability**: Structured, color-coded sections that let a technician scan causes and corrective steps in under 5 seconds.
3. **Traceability**: Every recommendation points directly to an indexed manual, section, and page number.
4. **Visual Aid Integration**: Electrical and hydraulic issues require schematics; text alone is insufficient for physical diagnosis.
5. **No Hallucination Tolerance**: When manuals don't have an answer, the UI displays an unambiguous, high-contrast refusal card rather than plausible-sounding guesswork.

---

## 2. Color Palette & Typography

- **Theme**: Industrial Slate & High-Contrast Cyber Dark/Light.
- **Backgrounds**: Slate-900 / Zinc-950 (Dark), Gray-50 (Light).
- **Accents**:
  - **Diagnostic Cyan / Blue** (`#0ea5e9`, `bg-cyan-500`): Active session, AI response indicators, query highlight.
  - **Precision Emerald** (`#10b981`, `bg-emerald-500`): Verified citations, pass status, operational telemetry.
  - **Ambiguity Amber** (`#f59e0b`, `bg-amber-500`): Cross-manual conflict cards, clarification prompts.
  - **Safety Red** (`#ef4444`, `bg-red-500`): Honest refusal cards, safety bypass rejection, critical alerts.
- **Typography**: Clean sans-serif (`Inter`, `system-ui`), monospaced code blocks for error codes (`font-mono`).

---

## 3. Component Architecture & Card Types

### 3.1 Normal Answer Card (`NormalAnswerCard.tsx`)
The standard response card when an error or symptom is successfully verified:
- **Header**: Error code badge (`E101`, `H205`, `R101`), verified machine name, and source indicator.
- **Section 1: Error Meaning**: Clear, concise 1-2 sentence description of what the error or symptom indicates.
- **Section 2: Probable Causes**: Unordered bullet list highlighting root mechanical or electrical failure points.
- **Section 3: Corrective Actions**: Numbered step-by-step procedure instructing the operator on physical diagnosis, LOTO procedures, part replacement, and resets.
- **Section 4: Traceable Citations**: Clickable badges (`CitationChip.tsx`) linking to the exact manual and page number.
- **Technical Schematic Viewer**: Embedded SVG technical schematic with zoom controls, pan viewport, and explanatory engineering caption.

### 3.2 Ambiguity Selection Card (`AmbiguityCard.tsx`)
Triggered when an error code is defined across 2+ distinct machines with differing meanings (e.g. `E101`):
- **Warning Header**: Amber warning icon with notice: *"Error code exists on multiple machines — select your unit"*.
- **Machine Option Tiles**: Clickable cards listing each candidate machine and its corresponding failure summary:
  - Option A: *CNC-100: Excessive motor temperature*
  - Option B: *Press-200: Hydraulic oil pressure low*
- **Click Interaction**: Clicking a tile immediately sends the selected machine into the conversation, resolving the ambiguity cleanly.

### 3.3 Safety Refusal Card (`RefusalCard.tsx`)
Triggered when a query fails any of the 3 safety gates (low similarity, unverified error code, or undocumented symptom/action):
- **Shield / Refusal Header**: High-contrast red badge with shield icon.
- **Deterministic Refusal Copy**:
  > *"The manuals don't cover this. I won't guess at a fix."*
- **Zero Hallucination Guarantee**: Suppresses citations and suppresses LLM generation entirely.

---

## 4. Layout Hierarchy & Navigation

```
+-----------------------------------------------------------------------------------+
|  [Logo] MachineAssist   | [Copilot] [Benchmarks] [Manuals] [Telemetry] | (•) Live  ⚙  |
+---------------------+-------------------------------------------------------------+
| SIDEBAR             | MAIN CONTENT AREA                                           |
|                     |                                                             |
| - Machine Selector  | +---------------------------------------------------------+ |
|   [All Units ▼]     | | Chat Stream / Benchmark Table / Manual Viewer           | |
|                     | |                                                         | |
| - Session Memory    | | [Card 1: Normal Answer / Ambiguity / Refusal]           | |
|   Session: sess_xyz | | [Card 2: SVG Technical Schematic]                       | |
|   Machine: CNC-100  | +---------------------------------------------------------+ |
|   Error: E101       |                                                             |
|                     | +---------------------------------------------------------+ |
| - Event Trail       | | [Demo Chips: Demo 1 | Demo 2 | Demo 3 | Demo 4]         | |
|   > Parsed query    | | [ Input: Describe symptom or enter error code...  (Send)| |
|   > Scored chunks   | +---------------------------------------------------------+ |
|   > 3 Gates passed  |                                                             |
+---------------------+-------------------------------------------------------------+
```

### 4.1 Header Bar (`TopBar.tsx`)
- App title and logo.
- Primary navigation tabs:
  - **Copilot**: Real-time diagnostic assistant.
  - **Benchmarks**: Automated 13-15 test scenario evaluation matrix.
  - **Manuals**: Interactive library of raw manual texts and indexed chunks.
  - **Telemetry**: ChromaDB collection status, chunk counts, and live system health.
- Backend status indicator: Live (green dot) vs Mock (yellow dot).
- Settings modal trigger (⚙) for configuring base URLs and response modes.

### 4.2 Diagnostic Sidebar (`Sidebar/`)
- **Machine Filter (`MachineFilter.tsx`)**: Allows technicians to lock diagnosis to an active machine or search across all equipment.
- **Session Memory (`SessionMemory.tsx`)**: Live inspector displaying the active session state stored in `memory_store` (active machine, active error code, last updated timestamp).
- **Event Trail (`EventTrail.tsx`)**: Real-time pipeline execution monitor showing exact timestamps and status for:
  1. `query_understanding`
  2. `hybrid_retrieval`
  3. `disambiguation_check`
  4. `safety_evaluation`
  5. `context_assembly`
  6. `llm_generation`

### 4.3 Input Dock (`InputBar.tsx`)
- Quick-fill demo script selector (`DemoScriptBar.tsx`) for executing pre-canned benchmark scenarios with a single click.
- Monospaced query input with keyboard shortcuts (`Enter` to submit, `Esc` to clear).
- Multilingual voice/text indicators.

---

## 5. Modal Systems

### 5.1 Citation Deep-Dive Modal (`CitationModal.tsx`)
When a technician clicks a citation badge (e.g. `cnc100.txt [Page 2]`):
- Displays the complete grounded text snippet from ChromaDB.
- Highlights exact mechanical causes and step references.
- Displays metadata attributes (`machine`, `model`, `manual`, `section`, `page`).
- Embedded technical schematic associated with the cited section.

### 5.2 Backend Connection Settings (`BackendSettingsModal.tsx`)
- Switch between **Live Backend** (`http://127.0.0.1:8000`) and **Offline Mock Engine**.
- Custom backend URL configuration for remote factory floor deployments.
- Network latency simulation toggle for UX testing under poor factory WiFi conditions.
