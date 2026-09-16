# LeaseLens 🔍

> **PromptWars Virtual 2026 · Legal AI Hackathon Submission**
> Residential Rent Agreement Risk Highlighter Powered by Google Antigravity & Gemini

---

## 🌟 Overview

**LeaseLens** is a multi-agent AI system designed to demystify complex residential lease agreements for tenants. By orchestrating specialized agents powered by Google Antigravity and Gemini, LeaseLens performs high-fidelity document ingestion, CUAD-aligned clause extraction, statistical deviation analysis against regional market norms, and strict Unauthorized Practice of Law (UPL) sanitization.

### 🛡️ Core Guardrails
1. **Zero Legal Advice (UPL Strict Compliance)**: LeaseLens never issues directives (e.g. "do not sign", "sue", "illegal"), never declares provisions void or unenforceable, and never acts as an attorney. Every finding is framed statistically against empirical regional market baselines.
2. **Permanent Legal Disclaimer**: A non-dismissible, non-collapsible banner reminds users that analysis is strictly informational and educational.
3. **Repository Footprint < 10MB**: Strict `.gitignore` enforcement and dependency hygiene guarantee that the public repository remains ultra-lightweight (currently ~144KB, >98% headroom).

---

## 🏗️ Architecture: Supervisor Agent Pattern

```
                             User
                               │
                      (PDF / Raw Lease Text)
                               ▼
                    ┌─────────────────────┐
                    │ React + Vite Client │
                    └──────────┬──────────┘
                               │ POST /api/analyze-lease
                               ▼
                    ┌─────────────────────┐
                    │   FastAPI Gateway   │
                    └──────────┬──────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       ┌───────────────┐               ┌───────────────┐
       │ Ingestion Agt │               │  market_norms │
       │(Gemini 3.6 F) │               │    (JSON)     │
       └───────┬───────┘               └───────┬───────┘
               │ (Normalized Markdown)         │
               ▼                               │
       ┌───────────────┐                       │
       │Classifier Agt │◄──────────────────────┘
       │(Gemini 3.1 P) │ (Sliding 2000-token window)
       └───────┬───────┘
               │ (Raw Clause Risks)
               ▼
       ┌───────────────┐
       │ UPL Guardrail │ Dual-layer sanitization:
       │(Gemini 3.6 F) │ 1. Deterministic regex rules
       └───────┬───────┘ 2. Semantic safety audit
               │
               ▼
         LeaseAnalysis
      (Deterministic JSON)
```

---

## 🧩 Agent Hierarchy

| Agent | Model / Engine | Capabilities | Responsibility |
|---|---|---|---|
| **Orchestrator** | Supervisor (Python) | Router & Coordinator | Chunks text, manages retries, pipes data between agents |
| **Ingestion** | Gemini 3.6 Flash | Read-only | Native multimodal OCR and markdown normalization |
| **Classifier** | Gemini 3.1 Pro | Read-only + Structured Output | CUAD-aligned extraction against regional baselines |
| **UPL Guardrail** | Gemini 3.6 Flash + Regex | Read-only + Deterministic | Strips legal advice, enforces educational framing |

---

## 📊 CUAD-Aligned Categories & Market Norms

LeaseLens benchmarks clauses against regional standards across Indian metros (Bangalore, Mumbai, Delhi NCR, Hyderabad) and general pan-India 11-month lease norms:

- **Security Deposit**: 2 months standard (Pan-India) vs. 10 months standard (Bangalore)
- **Lock-in Period**: 0–1 month standard; >3 months flagged as high variance
- **Notice Period**: 1 month mutual standard
- **Maintenance Liability**: Tenant minor (<₹5,000) / Owner structural
- **Rent Escalation**: 5% per annum on renewal
- **Subletting**: Consent-based standard
- **Termination**: Mutual notice standard
- **Painting & Restoration**: Normal wear and tear excluded
- **Utilities & Common Area**: Tenant utilities / Owner society charges

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- `GEMINI_API_KEY` ([Google AI Studio](https://aistudio.google.com/))

### 2. Backend Setup
```bash
cd backend
cp ../.env.example .env
# Add your GEMINI_API_KEY into .env

pip install -r requirements.txt
python main.py
```
Backend runs at `http://localhost:8000`. API documentation is available at `http://localhost:8000/docs`.

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`.

---

## 🧪 Verification & Auditing

### Automated UPL Guardrail Tests
```bash
python3 backend/test_upl_guardrail.py
```
Runs 15 automated test suites covering forbidden term detection, regex sanitization, advisory disclaimer suffixes, and adversarial prompt injections.

### Repository Size Audit
```bash
./scripts/check_repo_size.sh
```
Audits tracked files and validates `.gitignore` enforcement against the 10MB limit.

---

## ⚖️ Legal Disclaimer

*LeaseLens is an AI-powered informational and educational tool only. It does not provide legal advice, does not constitute an attorney-client relationship, and should not be relied upon as a substitute for professional legal counsel. Consult a qualified legal professional before executing any legal agreement.*
