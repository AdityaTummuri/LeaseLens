# LeaseLens 🔍

> **PromptWars Virtual 2026 · Legal AI Hackathon Submission**
> Multi-Agent Residential Rent Agreement Risk Highlighter Powered by Google Antigravity & Gemini

---

## 🌟 Executive Summary

**LeaseLens** is a multi-agent AI system designed to empower tenants by analyzing residential rent agreements against regional market baselines. It breaks down complex, opaque legalese into an intuitive traffic-light risk heatmap, highlighting provisions that deviate significantly from empirical market standards.

### 🛡️ Core Hackathon Guardrails

1. **UPL Strict Compliance (Zero Legal Advice)**: LeaseLens strictly operates as an educational and informational tool. It never provides legal advice, never directs users to accept/reject terms, and never declares clauses illegal or void. All observations are framed as statistical deviations from regional market standards.
2. **Permanent Non-Collapsible Legal Disclaimer**: Always visible on screen, informing users that LeaseLens is not an attorney or substitute for professional legal counsel.
3. **Repository Footprint < 10MB**: Strict `.gitignore` enforcement and zero bloat keep the repository at **~244KB** (>97% headroom under the 10MB limit).

---

## 🏗️ Multi-Agent Architecture (Supervisor Pattern)

The backend leverages the **Supervisor Agent Pattern**:
- **Orchestrator Agent**: Manages the pipeline lifecycle, text chunking (2000-token sliding windows), error handling, and agent delegation.
- **Ingestion Agent (Gemini 3.6 Flash)**: Multimodal document OCR and markdown normalization from uploaded PDFs or pasted text.
- **Classifier Agent (Gemini 3.1 Pro)**: Extracts clauses across CUAD-aligned categories (Security Deposit, Lock-in, Notice Period, Maintenance, etc.) and benchmarks them against `market_norms.json`.
- **UPL Guardrail Agent (Gemini 3.6 Flash + Regex)**: Dual-layer sanitization engine ensuring strict adherence to Unauthorized Practice of Law safety standards.

---

## 🚀 Directory Structure

```
LeaseLens/
├── .gitignore                   # Root gitignore protecting repo size
├── LICENSE                      # Open-source license
├── README.md                    # Project README
├── leaselens-hackathon/         # Main submission package
│   ├── README.md                # Comprehensive technical documentation
│   ├── .env.example             # Environment template
│   ├── .gitignore               # Subdirectory ignore rules
│   ├── backend/
│   │   ├── main.py              # FastAPI gateway
│   │   ├── requirements.txt     # Python dependencies
│   │   ├── agents/              # Google Antigravity Agents
│   │   │   ├── orchestrator.py  # Supervisor pattern coordinator
│   │   │   ├── ingestion.py     # Multimodal OCR agent
│   │   │   ├── classifier.py    # CUAD extraction & benchmarking agent
│   │   │   └── upl_guardrail.py # Safety sanitization agent
│   │   ├── schemas/             # Pydantic v2 schemas
│   │   │   └── lease_schema.py  # Structured output definitions
│   │   ├── data/
│   │   │   └── market_norms.json # Regional market standards
│   │   └── test_upl_guardrail.py# Automated UPL test suite
│   ├── frontend/                # React + Vite client
│   │   ├── src/                 # UI components & styles
│   │   │   ├── App.jsx          # Root application
│   │   │   ├── index.css        # Tailwind & glassmorphism styles
│   │   │   └── components/      # Heatmap, RiskCard, Upload, Disclaimer
│   │   ├── package.json         # Node dependencies
│   │   ├── vite.config.js       # Vite configuration
│   │   └── tailwind.config.js   # Tailwind theme tokens
│   └── scripts/
│       └── check_repo_size.sh   # Automated repo size audit script
```

---

## 🚦 Getting Started

### 1. Setup Environment
```bash
cp leaselens-hackathon/.env.example leaselens-hackathon/.env
# Add your GEMINI_API_KEY in leaselens-hackathon/.env
```

### 2. Run Backend
```bash
cd leaselens-hackathon/backend
pip install -r requirements.txt
python main.py
```
Backend runs on `http://localhost:8000` (Swagger docs: `http://localhost:8000/docs`).

### 3. Run Frontend
```bash
cd leaselens-hackathon/frontend
npm install
npm run dev
```
Frontend runs on `http://localhost:5173`.

---

## 🧪 Verification & Automated Audits

### Run UPL Guardrail Test Suite
```bash
python3 leaselens-hackathon/backend/test_upl_guardrail.py
```
*Executes 15 unit tests verifying forbidden term scanning, regex sanitization, educational disclaimers, and adversarial prompt injection defenses.*

### Run Repository Size Audit
```bash
./leaselens-hackathon/scripts/check_repo_size.sh
```
*Validates that total repository size remains strictly under the 10MB limit.*
