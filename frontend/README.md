# MachineAssist Frontend — Industrial Diagnostic Console

A high-performance React + TypeScript + Tailwind CSS web interface purpose-built for factory operators and field maintenance technicians. It connects seamlessly to the MachineAssist RAG backend, providing real-time hardware error diagnostics, interactive technical schematics, multi-turn dialogue memory, and honest safety controls.

---

## 1. System Overview

The console provides an industrial-grade user experience with high-contrast UI, rapid keyboard-driven workflows, and comprehensive diagnostic transparency:

- **AI Copilot (`/`)**: Natural language chat interface with structured 4-section answers, interactive technical SVG schematics, clickable source citations, and honest refusal cards.
- **Benchmark Suite**: Automated 13+ scenario benchmark runner with live pass/fail scoring, latency tracking, and expectation verification.
- **Manuals Explorer**: Library viewer rendering indexed technical manuals, chapter structures, and chunk metadata.
- **System Telemetry**: Real-time vector store metrics, ChromaDB chunk count, registered machine status, and latency telemetry.
- **Event Trail & Session Memory**: Sidebar widgets displaying real-time pipeline telemetry (query understanding, vector retrieval, safety gate evaluation, LLM generation) and active session state.

---

## 2. Key Features

### Diagnostic Answer Cards
- **Structured Sections**: Automatically parses and displays *Error Meaning*, *Probable Causes*, *Step-by-Step Corrective Actions*, and *Traceable Citations*.
- **Interactive SVG Technical Schematics**: Embedded engineering diagrams (coolant circuits, VFD power circuits, hydraulic manifold loops) with responsive zoom and captioning.
- **Clickable Citations**: Pill badges referencing exact manuals and page numbers (`cnc100.txt [Page 2]`), opening a modal with grounded snippet text and metadata.

### Cross-Manual Disambiguation
- When an error code is shared across multiple machines (e.g. `E101` on CNC-100 vs Press-200), the UI renders an **Ambiguity Card** prompting the operator to click their target machine before dispensing repair instructions.

### 3-Gate Safety Refusals
- When queries fall out of scope, request unsupported procedures, or ask for unauthorized safety bypasses, the UI renders a high-visibility **Safety Refusal Card**:
  > *"The manuals don't cover this. I won't guess at a fix."*

### Multi-Turn Context & Machine Scoping
- **Session Memory**: Carries over active machines and error codes across turns (e.g. *"What if that doesn't work?"*).
- **Machine Scoping**: Allows technicians to lock the diagnostic scope to a single machine unit (e.g., `CNC-100`, `Press-200`, `Hydraulic Press`).

### Multilingual Translation
- Accepts operator input in regional languages (Kannada, Hindi, Tamil, Spanish, German, etc.) and routes through the automated translation service.

---

## 3. Project Structure

```
frontend/
├── public/
│   ├── diagrams/             # High-resolution SVG schematics
│   ├── static/diagrams/      # Mirrored static schematics
│   ├── favicon.svg
│   └── icons.svg
├── src/
│   ├── components/
│   │   ├── Chat/
│   │   │   ├── AmbiguityCard.tsx     # Disambiguation selection card
│   │   │   ├── CitationChip.tsx      # Source citation pill badge
│   │   │   ├── CitationModal.tsx     # Full-text grounded source modal
│   │   │   ├── DemoScriptBar.tsx     # One-click demo script selector
│   │   │   ├── InputBar.tsx          # Technician input dock with status indicators
│   │   │   ├── MessageList.tsx       # Main diagnostic conversation stream
│   │   │   ├── NormalAnswerCard.tsx  # 4-section answer card with SVG diagram viewer
│   │   │   └── RefusalCard.tsx       # Safety Gate refusal card
│   │   ├── Sidebar/
│   │   │   ├── EventTrail.tsx        # Pipeline stage execution telemetry
│   │   │   ├── MachineFilter.tsx     # Equipment unit selector
│   │   │   └── SessionMemory.tsx     # Active session state display
│   │   ├── BackendSettingsModal.tsx  # API connection & mode settings
│   │   └── TopBar.tsx                # Header bar with navigation tabs & health badge
│   ├── services/
│   │   ├── api.ts            # DiagnosticService client for FastAPI backend
│   │   └── mockEngine.ts     # Offline demo engine for standalone operation
│   ├── types/
│   │   └── index.ts          # Complete TypeScript interfaces and data contracts
│   ├── App.tsx               # Root application shell & tab routing
│   ├── App.css               # Component utility styles
│   ├── index.css             # Tailwind base & custom design tokens
│   └── main.tsx              # React DOM entry point
├── package.json
├── tsconfig.json
└── vite.config.ts            # Vite config with complete backend proxy
```

---

## 4. Setup & Running

### Prerequisites
- Node.js 18+ and `npm`

### Installation
```bash
cd frontend
npm install
```

### Development Mode (with Hot Reloading)
```bash
npm run dev
```
The application will start on **`http://localhost:5173/`**.  
All API calls (`/query`, `/machines`, `/api`, `/diagrams`, `/static`) are automatically proxied to the Python backend running on `http://127.0.0.1:8000/`.

### Production Build
```bash
npm run build
```
Generates an optimized production bundle in `frontend/dist/`.  
When the FastAPI backend is started, it automatically serves this production build at **`http://127.0.0.1:8000/`**.

### Preview Production Build
```bash
npm run preview
```

---

## 5. Dual-Mode Architecture

The frontend supports two operating modes configurable via the settings dialog (⚙ icon in header):

1. **Live Backend Mode (Default)**:
   - Talks directly to FastAPI (`/query`).
   - Executes real hybrid search on ChromaDB with SentenceTransformers.
   - Enforces 3-gate safety controls and dynamic diagram retrieval.
2. **Offline Mock Mode**:
   - Built-in simulation engine ([`src/services/mockEngine.ts`](file:///c:/fr1/VH26-TEAM_HARMONY/frontend/src/services/mockEngine.ts)) handling all 4 demo scenarios offline.
   - Automatically activates if the backend server is temporarily unreachable.
