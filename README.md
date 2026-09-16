# 🔍 LeaseLens — AI-Powered Residential Lease Risk Highlighter

> **PromptWars Virtual 2026 · Legal AI Hackathon Submission**

LeaseLens is a multi-agent AI system that analyzes residential rent agreements against empirical regional market baselines, surfacing clauses that deviate statistically from the norm. Rather than providing legal opinions or advice, LeaseLens empowers tenants with **informational, data-driven insights** so they can have more informed conversations with qualified legal professionals.

> ⚖️ **Important:** LeaseLens is an **informational and educational tool only**. It does **not** constitute legal advice, does **not** create an attorney-client relationship, and must **never** be used as a substitute for consultation with a licensed attorney.

---

## 📌 Chosen Vertical

**Legal Assistance & Access**

LeaseLens directly addresses the acute information asymmetry faced by residential tenants when presented with complex lease agreements. In India's rental market — where 11-month leases are standard and terms vary dramatically between metros — tenants routinely sign agreements containing clauses that deviate significantly from market norms without realizing it. LeaseLens bridges this gap by providing instant, AI-powered statistical analysis of lease clauses, empowering users to identify deviations and seek appropriate professional counsel.

---

## 🧠 Approach and Logic

### Multi-Agent Supervisor Pattern (Google Antigravity SDK)

LeaseLens implements the **Supervisor Agent Pattern** using the Google Antigravity Python SDK, orchestrating four specialized agents in a deterministic pipeline:

```
┌───────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                         │
│          (Supervisor Pattern — Sequential Delegation)         │
│                                                               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐     │
│  │  INGESTION   │──▶│  CLASSIFIER  │──▶│ UPL GUARDRAIL│     │
│  │  AGENT       │   │  AGENT       │   │ AGENT        │     │
│  │ Gemini 3.6   │   │ Gemini 3.1   │   │ Gemini 3.6   │     │
│  │ Flash        │   │ Pro          │   │ Flash + Regex │     │
│  │              │   │              │   │              │     │
│  │ ● Multimodal │   │ ● CUAD-align │   │ ● Layer 1:   │     │
│  │   OCR        │   │   extraction │   │   Regex scan │     │
│  │ ● Markdown   │   │ ● Market     │   │ ● Layer 2:   │     │
│  │   normalize  │   │   benchmarks │   │   LLM audit  │     │
│  │ ● Read-only  │   │ ● Risk score │   │ ● Read-only  │     │
│  │   mode       │   │ ● Read-only  │   │   mode       │     │
│  └──────────────┘   └──────────────┘   └──────────────┘     │
└───────────────────────────────────────────────────────────────┘
```

**Why this architecture?**
- **Separation of concerns**: Each agent has a single, well-defined responsibility, making the system auditable and maintainable.
- **Defense-in-depth UPL safety**: The UPL Guardrail Agent applies **dual-layer sanitization** — deterministic regex replacement (Layer 1) followed by semantic LLM review (Layer 2) — ensuring legal advice never reaches the user even if the Classifier Agent halluccinates advisory language.
- **Deterministic output**: Pydantic v2 structured output schemas (`LeaseAnalysis`, `ClauseRisk`) enforce a strict JSON contract between agents and the frontend, eliminating formatting ambiguity.
- **Security**: All agents are explicitly configured with `CapabilitiesConfig(enabled_tools=BuiltinTools.read_only())`, preventing any agent from performing writes, executing code, or accessing the filesystem.

---

## ⚙️ How the Solution Works

### Step-by-Step Processing Flow

1. **User Upload**: The tenant uploads a PDF lease agreement or pastes the raw text via the React frontend.

2. **API Gateway** (`POST /api/analyze-lease`): FastAPI validates the input — checking MIME type (`application/pdf`, `image/png`, `image/jpeg`), enforcing a 20MB file size limit, and rejecting malformed requests via Pydantic validation.

3. **Ingestion Agent** (Gemini 3.6 Flash): Performs native multimodal OCR on the uploaded PDF/image. Outputs clean, normalized markdown text preserving exact clause wording and structure. No external PDF parsing libraries are needed — Gemini handles OCR natively, keeping the repository lightweight.

4. **Text Chunking** (Orchestrator): The normalized text is split into overlapping 2000-token sliding windows (with 200-token overlap) to ensure no clause is lost at chunk boundaries.

5. **Classifier Agent** (Gemini 3.1 Pro): Extracts verbatim clauses across 9 CUAD-aligned categories (Security Deposit, Lock-in Period, Notice Period, Maintenance Liability, Rent Escalation, Subletting, Termination, Painting & Restoration, Utilities & Common Area). Each clause is benchmarked against `market_norms.json` — a curated dataset of regional standards for Pan-India, Bangalore, Mumbai, Delhi NCR, and Hyderabad. Risk levels (`low`, `moderate`, `high`) are assigned based on statistical deviation percentages.

6. **UPL Guardrail Agent** (Dual-Layer):
   - **Layer 1 (Deterministic Regex)**: Scans all `educational_note` fields for 18 forbidden legal-advice terms (`illegal`, `void`, `sue`, `recommend`, `should sign`, `predatory`, etc.) and replaces them with neutral, informational alternatives.
   - **Layer 2 (Semantic LLM Audit)**: A separate Gemini 3.6 Flash agent reviews the entire analysis for subtler advisory patterns that regex cannot catch.
   - Both layers ensure every note ends with: *"Review by a qualified legal professional is advised prior to execution."*

7. **Frontend Rendering**: The React + Vite client renders the `LeaseAnalysis` JSON as an interactive risk heatmap dashboard with:
   - An animated overall risk gauge (0–10 scale)
   - Color-coded risk distribution chips (WCAG AA contrast-compliant)
   - Expandable clause cards showing verbatim text, market baselines, deviation percentages, and educational notes
   - A permanently visible, non-collapsible legal disclaimer banner

---

## 📝 Assumptions Made

1. **Regional Market Data**: Market baselines in `market_norms.json` are aggregated statistical averages from publicly available sources (NoBroker, MagicBricks, 99acres reports). They are approximations for informational comparison and do not reflect individual jurisdiction-specific legal requirements.

2. **Document Clarity**: OCR accuracy depends on the quality of the uploaded PDF/image. Illegible text is marked as `[ILLEGIBLE]` rather than guessed, preserving factual integrity.

3. **Indian Residential Context**: The system is optimized for standard Indian 11-month residential lease agreements. International lease formats may produce less accurate benchmarking.

4. **Token Approximation**: The chunking algorithm uses a rough 4-characters-per-token approximation for sliding window calculations. This is sufficient for residential leases (typically 2–10 pages) but may require calibration for significantly longer commercial leases.

5. **Single-Language Support**: LeaseLens currently processes English-language leases only. Multilingual support (Hindi, Kannada, Marathi) would require additional ingestion agent configurations.

6. **No Persistent Storage**: LeaseLens does not store uploaded documents or analysis results. All processing is ephemeral and session-scoped, protecting user privacy.

---

## 🚀 Local Setup & Run Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- A Google AI Studio API key (`GEMINI_API_KEY`) — [Get one here](https://aistudio.google.com/)

### 1. Clone the Repository
```bash
git clone https://github.com/AdityaTummuri/LeaseLens.git
cd LeaseLens/leaselens-hackathon
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Start the Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```
The FastAPI server starts at `http://localhost:8000`.
- Swagger API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 4. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
The Vite dev server starts at `http://localhost:5173`.

### 5. Use the Application
1. Open `http://localhost:5173` in your browser.
2. Upload a PDF lease agreement or paste the lease text.
3. Click **"Analyze Lease Agreement"**.
4. Review the interactive risk heatmap and clause-level analysis.

### 6. Run Automated Tests
```bash
# UPL Guardrail safety tests (15 test suites)
python3 backend/test_upl_guardrail.py

# Repository size audit (< 10MB enforcement)
chmod +x scripts/check_repo_size.sh && ./scripts/check_repo_size.sh
```

---

## 🏗️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **AI Agents** | Google Antigravity Python SDK | Supervisor pattern multi-agent orchestration |
| **LLM Models** | Gemini 3.6 Flash, Gemini 3.1 Pro | OCR, clause extraction, UPL sanitization |
| **Backend** | FastAPI + Uvicorn | Async REST API gateway |
| **Schemas** | Pydantic v2 | Deterministic structured output validation |
| **Frontend** | React 18 + Vite 5 | Interactive heatmap UI |
| **Styling** | Tailwind CSS 3 | Glassmorphism design system |
| **Testing** | Python unittest | UPL guardrail safety regression tests |

---

## 📂 Repository Structure

```
LeaseLens/
├── leaselens-hackathon/
│   ├── backend/
│   │   ├── main.py                    # FastAPI gateway + input validation
│   │   ├── requirements.txt           # 6 direct dependencies only
│   │   ├── agents/
│   │   │   ├── orchestrator.py        # Supervisor pattern coordinator
│   │   │   ├── ingestion.py           # Multimodal OCR agent (Gemini 3.6 Flash)
│   │   │   ├── classifier.py          # CUAD extraction agent (Gemini 3.1 Pro)
│   │   │   └── upl_guardrail.py       # Dual-layer UPL safety agent
│   │   ├── schemas/
│   │   │   └── lease_schema.py        # Pydantic v2 output schemas
│   │   ├── data/
│   │   │   └── market_norms.json      # Regional market baselines
│   │   └── test_upl_guardrail.py      # Automated safety test suite
│   ├── frontend/
│   │   ├── src/
│   │   │   ├── App.jsx                # Root application component
│   │   │   ├── index.css              # Tailwind + glassmorphism styles
│   │   │   └── components/
│   │   │       ├── LegalDisclaimer.jsx # Permanent UPL disclaimer
│   │   │       ├── FileUpload.jsx     # Drag-and-drop + paste input
│   │   │       ├── HeatmapView.jsx    # Risk gauge + dashboard
│   │   │       ├── RiskCard.jsx       # Expandable clause cards
│   │   │       └── LoadingSpinner.jsx # Multi-stage progress indicator
│   │   ├── package.json
│   │   ├── vite.config.js             # Terser minification config
│   │   └── tailwind.config.js         # Custom color tokens
│   └── scripts/
│       └── check_repo_size.sh         # < 10MB enforcement audit
├── .gitignore
├── LICENSE
└── README.md
```

---

## ⚖️ Legal Disclaimer

*LeaseLens is an AI-powered informational and educational tool. It does not provide legal advice, does not constitute an attorney-client relationship, and should not be relied upon as a substitute for professional legal counsel. All risk assessments are statistical comparisons against market baselines and may not reflect jurisdiction-specific regulations. Always consult a qualified legal professional before making any decisions regarding your lease agreement.*
