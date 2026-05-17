# OracleChain — Build Plan

> **Time Budget**: ~32 hours
> **Team**: Solo developer
> **Build Priority**: Agent performance > Test coverage > Documentation > Deployment

## Phase 1: Foundation (Hours 0-4)

### Sprint 1.1: Project Setup (1h)
- [ ] Initialize Python project with `pyproject.toml`
- [ ] Set up virtual environment + install dependencies
  ```bash
  git clone https://github.com/ai-prophet/ai-prophet.git
  cd ai-prophet
  pip install -e packages/core
  pip install -e "packages/cli[dev]"
  pip install litellm fastapi uvicorn scikit-learn diskcache pytest pydantic python-dotenv
  ```
- [ ] Create project structure (see ARCHITECTURE.md)
- [ ] Set up `.env.example` with required keys:
  - `PA_SERVER_API_KEY` — Prophet Arena API key (from prophetarena.co)
  - `PA_SERVER_URL=https://api.aiprophet.dev` — Prophet Arena server
  - `OPENAI_API_KEY` — GPT-4o-mini for classification + reasoning
  - `ANTHROPIC_API_KEY` — Claude Sonnet 4 for low-confidence predictions
  - `GOOGLE_API_KEY` — Gemini Flash for medium-confidence
  - `EXA_API_KEY` — Exa search (for SDK SearchClient)
  - `BEARER_TOKEN` — Auth token for your deployed endpoint
- [ ] Initialize git repo + .gitignore
- [ ] **Register team**: `prophet forecast register --team-name oraclechain`

### Sprint 1.2: Dual-Endpoint Server (1.5h)
- [ ] Implement `oraclechain/server.py` with **TWO** endpoints:
  - **`POST /chat/completions`** (OpenAI-compatible) — for Prophet Arena auto-eval
  - **`POST /predict`** — for CLI `--agent-url` testing
  - Both route to the same core `predict()` pipeline
  - Bearer token auth via `HTTPBearer`
  - Response format: dual `p_yes` (binary) or `probabilities` list (multi-outcome)
- [ ] Add `GET /health` endpoint
- [ ] Reference: `ai-prophet/packages/cli/ai_prophet/forecast/example_agent.py` (official example)
- [ ] Test with sample event:
  ```bash
  # CLI-compatible test
  curl -X POST http://localhost:8001/predict -H "Content-Type: application/json" \
    -d '{"event_ticker": "test", "market_ticker": "test", "title": "Will X happen?", "category": "Sports", "outcomes": ["Yes", "No"], "close_time": "2026-05-20T00:00:00Z"}'
  ```
- [ ] Verify output matches `Prediction` schema (`p_yes` or `probabilities` + `rationale`)

### Sprint 1.3: Core Agent + Category Classifier (1.5h)
- [ ] Implement `oraclechain/agent.py` with `predict(event) -> dict` (CLI-compatible)
- [ ] Implement `oraclechain/parser.py` — extract event JSON from chat prompt text
- [ ] Implement `oraclechain/classifier.py` using GPT-4o-mini
  - Few-shot classification: Sports, Geopolitics, Economics, Science/Tech, Pop Culture, Other
  - Keyword-based fallback classifier (no API call)
  - Cache classification results
- [ ] Verify: `prophet forecast predict --local oraclechain.agent --events data/fixtures/sample_events.json`

## Phase 2: Core Pipeline (Hours 4-12)

### Sprint 2.1: Retrieval via SDK SearchClient (2h)
- [ ] Implement `oraclechain/retrieval.py` using `ai_prophet.search.SearchClient`
  ```python
  from ai_prophet.search import SearchClient
  search = SearchClient(provider="exa", api_key=os.environ["EXA_API_KEY"])
  results = search.search(query, limit=3)
  ```
- [ ] Category-aware query builder:
  - Sports: `"{team} {sport} {season} odds injury report"`
  - Geopolitics: `"{event} {country} latest news analysis"`
  - Economics: `"{indicator} forecast {period} economist consensus"`
  - Science/Tech: `"{topic} latest research breakthrough"`
  - Pop Culture: `"{event} predictions odds betting"`
- [ ] Handle sandbox rejection (`search.last_rejected`, `search.last_warnings`)
- [ ] Use `as_of` parameter for date-fair searches
- [ ] Fallback: if search fails, return empty context (agent continues with LLM-only)
- [ ] **Time savings**: ~2h saved by using SDK search vs building 5 custom routers

### Sprint 2.2: LLM Reasoning Engine (3h)
- [ ] Implement `oraclechain/reasoning.py` with structured output prompts
- [ ] Prompt template: "Given this question, market context, and evidence, estimate probability for each outcome. Return JSON."
- [ ] Implement `oraclechain/model_router.py` — select model based on market price confidence
- [ ] JSON mode extraction for probabilities → dict format `{"Outcome A": 0.68, "Outcome B": 0.32}`
- [ ] Error handling: retry on API failure, fallback to cheaper model

### Sprint 2.3: Market Anchor (1h)
- [ ] Implement `oraclechain/anchor.py` — attempt to fetch market prices
- [ ] Try web scraping Kalshi/Polymarket for relevant market
- [ ] If not found: use uniform prior (1/n for n outcomes)
- [ ] Cache market prices (5-minute TTL)

### Sprint 2.4: Integration (2h)
- [ ] Wire parser → classifier → retrieval → reasoning → calibration → formatter in pipeline
- [ ] Dual entry points: `agent.predict(event)` (CLI) + `server.chat_completions(request)` (HTTP)
- [ ] End-to-end test with 5 sample events (one per category)
- [ ] Verbose logging: show pipeline steps in terminal
- [ ] Measure latency per step (aim for <30s total per event)

## Phase 3: Calibration & Optimization (Hours 14-20)

### Sprint 3.1: Calibration Layer (3h)
- [ ] Download datasets:
  ```bash
  prophet forecast retrieve --dataset sample-resolved --include-resolved -o data/fixtures/resolved_events.json
  prophet forecast retrieve --dataset sample-sports -o data/fixtures/sports_events.json
  prophet forecast retrieve --dataset sample-entertainment -o data/fixtures/entertainment_events.json
  prophet forecast retrieve --dataset sample-economics -o data/fixtures/economics_events.json
  ```
- [ ] Run base agent on `sample-resolved` (26 events) → collect raw predictions
- [ ] Train Platt scaling model on (predicted_prob, actual_outcome) pairs
- [ ] Implement `oraclechain/calibration.py` — load model, apply to new predictions
- [ ] Benchmark: compare calibrated vs uncalibrated Brier scores on resolved set
- [ ] Save calibration model as pickle (loaded at startup)

### Sprint 3.2: Cost Optimization (1.5h)
- [ ] Implement cost tracking per prediction (log model, tokens, USD)
- [ ] Test cost-tiered routing: ensure high-confidence questions use GPT-4o-mini
- [ ] Estimate 2-week cost at current rates
- [ ] Adjust thresholds if estimated cost > $40

### Sprint 3.3: Benchmarking + Submission (1.5h)
- [ ] Run `prophet forecast evaluate` on full historical dataset
- [ ] Create `scripts/bench.py` — batch benchmark with detailed output
- [ ] Generate Brier score table: per-category, overall, vs market baseline
- [ ] **Submit to server**: `prophet forecast submit --submission predictions.json`
- [ ] Check initial leaderboard position: `prophet forecast leaderboard`
- [ ] Document results in README

## Phase 4: Production & Deployment (Hours 20-26)

### Sprint 4.1: Railway Deployment (2h)
- [ ] Write `Dockerfile` (Python 3.12, uvicorn, environment variables)
- [ ] Deploy to Railway
- [ ] Generate domain
- [ ] Set environment variables:
  ```bash
  railway variables set PA_SERVER_API_KEY=prophet_xxx
  railway variables set PA_SERVER_URL=https://api.aiprophet.dev
  railway variables set OPENAI_API_KEY=sk-...
  railway variables set ANTHROPIC_API_KEY=sk-ant-...
  railway variables set GOOGLE_API_KEY=AIza...
  railway variables set EXA_API_KEY=...
  railway variables set BEARER_TOKEN=oraclechain-secret-token-xxx
  ```
- [ ] Test both endpoints:
  ```bash
  # OpenAI-compatible (for Prophet Arena)
  curl -X POST https://<domain>/chat/completions \
    -H "Authorization: Bearer <token>" \
    -d '{"model":"oraclechain-v1","messages":[{"role":"user","content":"<event prompt>"}]}'
  
  # CLI-compatible (for prophet forecast predict)
  curl -X POST https://<domain>/predict \
    -d '{"event_ticker":"test","market_ticker":"test","title":"Test?","category":"Sports","outcomes":["Yes","No"],"close_time":"2026-05-20T00:00:00Z"}'
  ```
- [ ] Verify health: `curl https://<domain>/health`
- [ ] **Register endpoint**: `prophet forecast register --team-name oraclechain --endpoint-url https://<domain>/chat/completions`
- [ ] **OR** Onboard at `prophetarena.co/onboarding` — submit endpoint URL + model name + bearer token

### Sprint 4.2: Reliability (2h)
- [ ] Add request timeout handling (30s per event, graceful degradation)
- [ ] Add retry logic with exponential backoff for external APIs
- [ ] Add rate limiting for external retrieval APIs
- [ ] Test crash recovery: restart container, verify stateless operation
- [ ] Add `/stats` endpoint for monitoring

### Sprint 4.3: Test Suite (2h)
- [ ] Unit tests: server (OpenAI schema), parser, classifier, retrieval, reasoning, calibration
- [ ] Integration tests: full pipeline with mock external APIs
- [ ] Edge cases: missing outcomes, empty descriptions, timeout scenarios
- [ ] Target: 50+ tests, all passing

## Phase 5: Documentation & Submission (Hours 26-32)

### Sprint 5.1: README (2h)
- [ ] Hero section with one-line pitch
- [ ] Architecture diagram (Mermaid)
- [ ] Performance benchmark table
- [ ] Setup instructions (3-step: clone, install, run)
- [ ] Cost analysis table
- [ ] Design decisions section
- [ ] License (MIT)

### Sprint 5.2: Devpost Submission (2h)
- [ ] Create Devpost project page
- [ ] Write long description (from SUBMISSION.md)
- [ ] Upload 4 screenshots (terminal output, benchmark, architecture, cost breakdown)
- [ ] Record 2-3 minute demo video (terminal recording with voiceover)
- [ ] Link GitHub repo
- [ ] Specify "Forecasting Track"

### Sprint 5.3: Final Verification (2h)
- [ ] Run full test suite: `pytest -v`
- [ ] Run benchmark: `python scripts/bench.py`
- [ ] Test deployed endpoint with sample events via Prophet Arena
- [ ] Verify agent responds within 30s per event
- [ ] Check all API keys are set in Railway env
- [ ] Verify onboarding passes at `prophetarena.co/onboarding`
- [ ] Submit on Devpost before **5:00 PM CT** deadline

## Critical Path

```
Foundation → OpenAI-Compatible Server → Parser + Classifier
  → Retrieval Routers (longest sprint, 4h) → LLM Reasoning
  → Integration → Calibration → Deployment → Onboarding → README → Submit
```

**Risk mitigation** (if behind schedule):
- Drop calibration layer (use raw LLM probabilities) — saves 3h
- Drop market anchor (predict from scratch) — saves 1h
- Use `p_yes` binary format only (skip multi-outcome normalization) — saves 0.5h
- Minimum viable: SDK SearchClient + single LLM + dual-endpoint server = still competitive
