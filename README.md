<div align="center">
  <h1>Sibyl 🔮</h1>
  <p><em>Retrieval-augmented forecasting agent for Prophet Arena — calibrated probability predictions with cost-tiered LLM routing.</em></p>
  <img src="docs/readme-hero.png" alt="Sibyl" width="100%">

  <br/>

  [![Live Demo](https://img.shields.io/badge/🚀_Live-Demo-06b6d4?style=for-the-badge)](https://github.com/edycutjong/sibyl)
  [![Pitch Video](https://img.shields.io/badge/🎬_Pitch-Video-ef4444?style=for-the-badge)](https://youtu.be/your-video)
  [![Pitch Deck](https://img.shields.io/badge/📊_Pitch-Deck-f59e0b?style=for-the-badge)](https://github.com/edycutjong/sibyl/pitch)
  [![Built for Prophet Hacks](https://img.shields.io/badge/Devpost-Prophet_Hacks-8b5cf6?style=for-the-badge)](https://prophethacks.devpost.com/)

  <br/>

  ![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat&logo=python&logoColor=white)
  ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)
  ![OpenAI](https://img.shields.io/badge/GPT--4o-412991?style=flat&logo=openai&logoColor=white)
  ![Anthropic](https://img.shields.io/badge/Claude_3.5_Sonnet-D97757?style=flat&logo=anthropic&logoColor=white)
  ![Google](https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=flat&logo=google&logoColor=white)
  ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
  ![Pytest](https://img.shields.io/badge/Pytest-0A9EDC?style=flat&logo=pytest&logoColor=white)
  [![CI](https://github.com/edycutjong/sibyl/actions/workflows/ci.yml/badge.svg)](https://github.com/edycutjong/sibyl/actions/workflows/ci.yml)

</div>

---

## 🎬 The Pitch

**Emotional Hook:**
A trader stares at a Kalshi contract for "Will the Fed raise rates in June?" priced at 42 cents. She knows the market is wrong — the CPI report just dropped 30 minutes ago — but she can't articulate WHY in probabilistic terms. Sibyl can.

### The Problem
Prediction markets like Kalshi aggregate the wisdom of thousands of informed traders into a single price. They're remarkably good — but they're not instantaneous. When new evidence drops (an economic report, an injury announcement, a geopolitical development), there's a window where the market price lags behind reality. That's the edge.

Current AI forecasting agents miss this edge entirely. They receive a question, prompt an LLM with no external context, and return whatever the model's training data suggests. The result: performance at or below market baseline, because the model's knowledge is months stale.

### The Solution & What's Novel
Most hackathon teams will wrap a single LLM with a "superforecaster" system prompt. Sibyl's edge comes from treating forecasting as an information retrieval problem, not a language generation problem. The LLM is the reasoning engine — but the evidence pipeline is what creates edge.

Sibyl is a **retrieval-augmented forecasting agent** that systematically beats prediction markets by combining three insights:
1. **Market Anchoring:** Starts with the market's probability as a Bayesian prior.
2. **Category-Specific Retrieval:** Routes each question to a specialized retrieval pipeline (Exa/Brave) that fetches the most relevant evidence for that domain.
3. **Calibrated Ensemble:** Applies post-hoc Platt scaling calibration trained on historical Prophet Arena data, plus cost-tiered model selection.

---

## 🏗️ Technical Architecture

> 📖 **Read more:** For a deeper dive into the system design, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

### The Prediction Pipeline
Sibyl uses an 8-step pipeline to process every forecasting event:
```text
Event → Category Classifier → Market Price Anchor
  → Category Router (Sports/Geo/Econ/Sci/Pop) → Evidence Retrieval
  → Context Assembly (4K tokens max) → Model Tier Selection
  → LLM Reasoning (structured JSON) → Calibration Layer
  → Output Probabilities
```

```mermaid
graph LR
    subgraph "Prophet Arena Evaluation Harness"
        PA["POST /chat/completions<br>OpenAI-compatible"]
    end

    subgraph "Sibyl Agent (FastAPI)"
        EP1["POST /chat/completions"]
        PARSE["Event Parser"]
        CC["Category Classifier"]
        MA["Market Anchor"]
        SC["ai_prophet.search.SearchClient"]
        CA["Context Assembler"]
        MT["Model Tier Selector"]
        LLM["LLM Reasoning"]
        CL["Calibration Layer"]
        FMT["Response Formatter"]
    end

    subgraph "LLM Providers (litellm)"
        MINI["GPT-4o-mini<br>High confidence"]
        FLASH["Gemini Flash<br>Medium confidence"]
        OPUS["Claude 3.5 Sonnet<br>Low confidence"]
    end

    PA --> EP1
    EP1 --> PARSE
    PARSE --> CC
    PARSE --> MA
    CC --> SC
    MA --> CA
    SC --> CA
    CA --> MT
    MT --> LLM
    LLM --> MINI & FLASH & OPUS
    LLM --> CL
    CL --> FMT
    FMT --> PA
```

### Key Design Decisions
- **100% completion rate**: Answers every question, even with minimal evidence (falls back to calibrated market price). The scoring formula `edge × completion_rate` rewards coverage.
- **Cost-efficient**: Estimated $15–40 for the full 2-week evaluation window via tiered model routing.
- **Stateless and robust**: Each prediction is independent. Server crash → restart → no state loss.

### Model Selection with Domain Justification

| Model | Use Case | Justification |
|---|---|---|
| **GPT-4o-mini** | Category classification, high-confidence predictions | Cheapest frontier model; classification doesn't need deep reasoning |
| **Gemini 2.5 Flash** | Medium-confidence predictions with retrieved context | Best cost-to-performance ratio for context-heavy reasoning |
| **Claude 3.5 Sonnet** | Close-call predictions (market 40-60%) | Best calibration and reasoning on ambiguous questions per Prophet Arena leaderboard |

### Agent Contracts

The Prophet Arena evaluation harness calls the agent via an **OpenAI-compatible `POST /chat/completions`** endpoint. 
It sends event details as a chat prompt. The agent parses the event from `messages[0].content`, runs forecasting logic, and returns an OpenAI-shaped response with a `probabilities` JSON in the `content` field.
Sibyl also implements a secondary `POST /predict` endpoint for CLI `--agent-url` testing, which accepts raw event JSON.

---

## 🛡️ Sponsor Defense: Prophet Arena

> 📖 **Read more:** View the full sponsor integration strategy in [SPONSOR_DEFENSE.md](docs/SPONSOR_DEFENSE.md).

### Why ONLY Prophet Arena?
Sibyl is built **exclusively** for the Prophet Arena evaluation ecosystem. Every component integrates with Prophet Arena's toolchain. Without Prophet Arena's toolchain, we would need 7 separate systems: a custom event ingestion system, evaluation harness, leaderboard, dataset registry, agent contract standard, web search infrastructure, and submission pipeline.

### Prophet Arena Touchpoints Used
We leverage **15 integration points** across 3 SDK packages. The agent exists because this evaluation framework exists.

| # | Feature/Method | What It Does | Code Location |
|---|---|---|---|
| 1 | `prophet forecast retrieve` | Fetches sample datasets (4 event slates) | `scripts/fetch_events.sh` |
| 2 | `prophet forecast register` | **Registers team** permanently with server | CLI setup |
| 3 | `prophet forecast events` | Lists open/closed events from live server | `sibyl/agent.py` |
| 4 | `prophet forecast predict --local` | Runs our agent against events | `sibyl/agent.py` |
| 5 | `prophet forecast predict --agent-url`| Tests our HTTP `/predict` endpoint | `sibyl/server.py` |
| 6 | `prophet forecast evaluate` | Scores predictions locally using Brier score | `scripts/bench.py` |
| 7 | `prophet forecast submit` | **Submits predictions** to leaderboard | `scripts/submit.sh` |
| 8 | `prophet forecast leaderboard` | Compares performance against 13 baselines| `README.md` |
| 9 | `ai-prophet-datasets` | Sample datasets for calibration training | `scripts/calibrate.py` |
| 10 | `Prediction` schema | Dual format (`p_yes` / `probabilities`) | `sibyl/agent.py` |
| 11 | `ai_prophet.search.SearchClient` | **SDK built-in retrieval** (Exa, Brave, etc.)| `sibyl/retrieval.py` |
| 12 | OpenAI-compatible `POST` endpoint | HTTP endpoint contract for auto-eval | `sibyl/server.py` |
| 13 | `POST /predict` endpoint | CLI-compatible endpoint | `sibyl/server.py` |
| 14 | `prophetarena.co/onboarding` | Agent registration config | Deployment |
| 15 | `PA_SERVER_API_KEY` | CLI configuration for server authentication | `.env.example` |

### SDK Integration Depth
```text
ai-prophet-core (PyPI)
├── ai_prophet_core.forecast.schemas  → Event model, Prediction model
├── ai_prophet_core.ServerAPIClient   → Typed HTTP client (Trading track)

ai-prophet (PyPI, CLI: prophet)
├── register           → Team registration (one-time)
├── retrieve           → Dataset fetching
├── events             → Live server event listing
├── predict            → Agent invocation
├── submit             → Prediction submission
├── evaluate           → Brier scoring

ai_prophet.search (SDK built-in)
├── SearchClient       → Unified search (Exa, Brave, Tavily, Perplexity)
├── sandbox_status     → Result filtering for fairness
```

### Honest Limitations
1. **26 resolved events for calibration** — Small training set for Platt scaling. May need to supplement with synthetic data or use simpler calibration.
2. **10-minute response window per batch** — For complex questions requiring extensive web research, this may be tight if the batch is large.
3. **SearchClient sandbox** — SDK's sandboxed search may reject some results; fallback to LLM-only if too aggressive.

---

## 📝 Hackathon Submission

> 📖 **Read more:** View our complete Devpost submission write-up in [SUBMISSION.md](docs/SUBMISSION.md).

---

## 👩‍⚖️ For Judges

Welcome! Thank you for evaluating Sibyl.

### Live Deployment
- **API Base URL:** `https://api.sibyl.edycu.dev/`
- **Swagger Documentation:** `https://api.sibyl.edycu.dev/docs`
- **Pitch Deck (Landing Page):** `https://api.sibyl.edycu.dev/`

### How to Test the Agent
The live deployment requires a Bearer token for authentication. You can test the endpoint using the following `curl` command:

```bash
curl -X POST https://api.sibyl.edycu.dev/predict \
  -H "Authorization: Bearer 483d6297928e3cf538c66af2fe92894ccf2be0c1802ca370bd6052d1d7edd6c9" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Will SpaceX successfully catch the Super Heavy booster in the next Starship flight?",
    "description": "Starship Flight 6 objective is to catch the Super Heavy booster with the Mechazilla chopstick arms.",
    "outcomes": ["Yes", "No"],
    "category": "Technology"
  }'
```

If you are configuring the Prophet Arena CLI, you can use the same token for the `PA_SERVER_API_KEY` (if passing the token via the Prophet CLI) or configure the agent URL to `https://api.sibyl.edycu.dev/chat/completions`.

---

## 🚀 Getting Started

### Prerequisites
- Python ≥ 3.12
- Docker (optional, for containerized deployment)

### Installation
1. Clone: `git clone https://github.com/edycutjong/sibyl.git`
2. Configure: `cp .env.example .env` and add your keys
3. Install: `python -m venv .venv && source .venv/bin/activate && pip install -e ".[dev]"`
4. Run: `uvicorn sibyl.server:app --port 8001`
5. Alternatively, run with Docker: `make docker-run`

## 🧪 Testing & CI
```bash
ruff check .          # Linting
pytest --cov          # Run tests with coverage
```

## 📁 Project Structure
```text
sibyl/
├── docs/              # Documentation and project assets
├── sibyl/             # Core prediction pipeline and server
│   ├── server.py      # FastAPI dual-endpoint server
│   ├── agent.py       # Core prediction pipeline
│   └── model_router.py# Cost-tiered model selection
├── tests/             # Pytest test suite
├── .env.example       # Environment template
├── .github/           # CI workflows
├── Makefile           # Dev scripts and Docker helpers
└── README.md          # You are here
```

## 📄 License
[MIT](LICENSE) © 2026 Edy Cu

## 🙏 Acknowledgments
Built for Prophet Hacks. Thank you to the sponsors for the APIs and tools.
