# Prophet Hacks — Research

## Event Summary

| Field | Value |
|---|---|
| **Name** | Prophet Hacks (AI Forecasting Hackathon) |
| **Platform** | Devpost |
| **URL** | https://prophethacks.devpost.com/ |
| **Organizer** | Prophet Arena Team (SIGMA Lab, University of Chicago) |
| **Powered by** | Kalshi (regulated prediction market) |
| **Type** | In-person at UChicago + Online submission via Devpost |
| **Location** | John Crerar Library, University of Chicago |
| **Duration** | 32 hours |
| **Build Window** | Sat May 16, 9:00 AM CT → Sun May 17, 5:00 PM CT |
| **Submission Deadline** | Sun May 17, 5:00 PM CT (10:00 PM UTC) |
| **Evaluation Window** | May 17 → May 31 (2 weeks, continuous) |
| **Winners Announced** | Monday, June 1, 2026 |
| **Participants** | 89 registered |
| **Team Size** | Solo allowed; up to 10 per team |
| **Prize Pool** | $1,000+ cash + 2× sponsored trips to South Korea (~$4,000 value each) |

## ⚠️ Critical: This is NOT a Typical Hackathon

> **No subjective judging.** Winners are determined PURELY by algorithmic performance metrics over a 2-week evaluation window. Your agent runs against live questions (Forecasting) or a live trading harness (Trading). The leaderboard updates continuously.

### Key Differences from Standard Hackathons
1. **No demo day / pitch** — your code IS the product
2. **No UI needed** — this is a backend/agent competition
3. **2-week post-event eval** — agent must be robust and cost-effective
4. **API costs on participants** — model choice, token usage, and request volume matter
5. **Performance-only scoring** — no "innovation" or "design" criteria

## Tracks

### Track 1: Forecasting
- **What**: Agent takes forecasting questions, returns calibrated probability predictions
- **Scoring**: `Total Score = (team_avg_Brier − market_avg_Brier) × completion_rate`
- **Win condition**: Total score must be > 0 (beat market average)
- **Endpoint**: **OpenAI-compatible `POST /chat/completions`** — NOT a custom `/predict` route
- **CLI Agent**: `POST /predict` endpoint OR local Python module with `predict(event) -> dict`
- **Response format**: `p_yes` (binary) OR `probabilities` list (multi-outcome) — **BOTH accepted**
- **Response window**: 10 minutes per request batch
- **Submission**: `prophet forecast submit --submission predictions.json`

### Track 2: Trading
- **What**: Agent trades on prediction markets, aims for positive PnL
- **Scoring**: Live paper-trading PnL + Sharpe ratio (combined rank across metrics)
- **Win condition**: PnL > 0 AND ≥14 trades during evaluation
- **Integration**: Must use `ai-prophet-core` SDK (`BenchmarkSession`, `ServerAPIClient`)
- **Tick interval**: 15-minute ticks, 9-minute submission deadline per tick

## Prizes

| Track | Place | Prize |
|---|---|---|
| Forecasting | 1st | Sponsored trip to South Korea (up to $2,000) — ICML workshop presentation |
| Forecasting | 2nd | $500 cash |
| Trading | 1st | Sponsored trip to South Korea (up to $2,000) — ICML workshop presentation |
| Trading | 2nd | $500 cash |

**Total effective value**: ~$5,000+ across both tracks

## Judging

- **Forecasting**: Pure Brier score — `sum((p_i - outcome_i)^2)` averaged per event — lower is better
- **Trading**: Sum of rankings across metrics (PnL, Sharpe) — lowest combined rank wins
- **Judges**: Simon Mahns, Haifeng Xu (SIGMA Lab, UChicago professor)

## Eligibility & Rules

- 18+ (under-18 with parental consent)
- All countries, open to all
- AI tools explicitly allowed and encouraged
- Must NOT: submit previously built projects, manipulate leaderboard, access non-public benchmark data, train on evaluation questions
- Public GitHub repo required (MIT or Apache 2.0 recommended)

---

## SDK & Technical Resources (Verified from Source Code)

### ai-prophet Monorepo
- **Main repo**: https://github.com/ai-prophet/ai-prophet (accessible)
- **Core SDK**: `packages/core` → `ai-prophet-core` (PyPI)
- **CLI**: `packages/cli` → `ai-prophet` (PyPI, command: `prophet`)
- **Example API**: https://github.com/ai-prophet/example-api
- **Datasets**: https://github.com/ai-prophet/ai-prophet-datasets

### Install (from source — recommended for hackathon)
```bash
git clone https://github.com/ai-prophet/ai-prophet.git
cd ai-prophet
pip install -e packages/core    # typed SDK (ai-prophet-core)
pip install -e "packages/cli[dev]"  # CLI (installs as `prophet`)
```
Or from PyPI:
```bash
pip install ai-prophet-core  # typed SDK
pip install ai-prophet       # CLI (installs as `prophet`)
```

### CLI Commands (Forecasting Track)
| Command | Description |
|---|---|
| `prophet forecast retrieve` | Fetch sample dataset events (offline, from `ai-prophet-datasets`) |
| `prophet forecast events` | List open/closed events from **live server** (requires `PA_SERVER_API_KEY`) |
| `prophet forecast register --team-name <name>` | **Register your team** (one-time, permanent, saves `PA_TEAM_NAME` to `.env`) |
| `prophet forecast predict` | Run agent against events (`--local <module>` or `--agent-url <url>`) |
| `prophet forecast submit` | **Submit predictions** to Prophet Arena server |
| `prophet forecast evaluate` | Score predictions locally (Brier score) |
| `prophet forecast leaderboard` | View current leaderboard scores |

### CLI Commands (Trading Track)
| Command | Description |
|---|---|
| `prophet trade eval run --models openai:gpt-4o` | Full 4-stage LLM pipeline |
| `prophet trade dashboard --slug <slug>` | Local dashboard (port 8501) |

---

## ⚠️ CRITICAL: Agent Endpoint Contracts

There are **TWO** ways to connect your agent. The CLI supports both:

### Option A: HTTP Endpoint (`--agent-url`)

The CLI calls your agent via **`POST /predict`** (NOT `/chat/completions`).

#### Request (from CLI)
```json
POST /predict
Content-Type: application/json

{
  "event_ticker": "KXNBAGAME-26MAY15DETCLE",
  "market_ticker": "KXNBAGAME-26MAY15DETCLE",
  "title": "Will Cleveland beat Detroit...?",
  "category": "Sports",
  "outcomes": ["Cleveland", "Detroit"],
  "close_time": "2026-05-15T20:00:00Z",
  ...
}
```

#### Response (either format accepted)
```json
// Option 1: Binary (p_yes)
{"p_yes": 0.68, "rationale": "Based on..."}

// Option 2: Multi-outcome (probabilities list)
{"probabilities": [{"market": "Cleveland", "probability": 0.68}, {"market": "Detroit", "probability": 0.32}]}

// Option 3: Multi-outcome (probabilities dict — also accepted)
{"probabilities": {"Cleveland": 0.68, "Detroit": 0.32}}
```

### Option B: Local Python Module (`--local`)

A Python module with a `predict(event: dict) -> dict` function:
```python
# my_agent.py
def predict(event: dict) -> dict:
    return {"p_yes": 0.65, "rationale": "..."}
    # OR
    return {"probabilities": [{"market": "A", "probability": 0.65}, {"market": "B", "probability": 0.35}]}
```

Run with: `prophet forecast predict --events events.json --local my_agent`

### Option C: OpenAI-Compatible Endpoint (for Prophet Arena auto-eval)

For the continuous 2-week evaluation, Prophet Arena calls a registered **OpenAI-compatible `/chat/completions`** endpoint.

#### Request (from evaluation harness)
```
POST /chat/completions
Authorization: Bearer <your-token>

{"model": "your-model-name", "messages": [{"role": "user", "content": "<prompt>"}]}
```

#### Response
```json
{"choices": [{"message": {"content": "{\"probabilities\": [...], \"rationale\": \"...\"}"}}}]
```

### Prediction Schema (from `ai_prophet_core.forecast.schemas`)

```python
class Prediction(BaseModel):
    market_ticker: str
    p_yes: float | None = Field(default=None, ge=0.01, le=0.99)
    probabilities: list[MarketProbability] | None = None
    rationale: str | None = None

    # Validation: requires EITHER p_yes OR probabilities
```

**Key**: `p_yes` must be in `[0.01, 0.99]`. `rationale` is optional but strongly recommended.

#### Onboarding
1. Deploy your endpoint (e.g., Render, Railway, Fly.io)
2. Test on `prophetarena.co/onboarding`
3. Submit the endpoint URL + model name + bearer token

### Trading Track: SDK-Based Bot

Uses `ai_prophet_core.arena.BenchmarkSession` with tick-based lifecycle:
```python
from ai_prophet_core import ServerAPIClient, TradeIntentRequest
from ai_prophet_core.arena import BenchmarkSession

API = ServerAPIClient(
    base_url=os.environ["PA_SERVER_URL"],
    api_key=os.environ["PA_SERVER_API_KEY"],
    timeout=30,
)

with BenchmarkSession(API) as session:
    session.create_experiment(slug="my-bot", config_hash=hash, config_json=config, n_ticks=96)
    part = session.upsert_participant(model="custom:my-bot", starting_cash=10_000)
    while True:
        lease = session.claim_tick()
        # ... strategy logic ...
        session.submit_intents(lease, part.participant_idx, intents)
        session.finalize(lease, part.participant_idx)
        session.complete_tick(lease)
```

---

## Event Data Format (Verified from `ai-prophet-datasets`)

### 4 Sample Datasets Available

| Dataset | Tasks | Resolved? | Use For |
|---|---|---|---|
| `sample-sports` | 16 | No | NBA/MLB playoffs, tennis matches |
| `sample-entertainment` | 13 | No | Eurovision, anime awards, Emmys |
| `sample-economics` | 13 | No | CPI, GDP, central bank rates |
| `sample-resolved` | 26 | **Yes** | Benchmarking with ground truth |

### Retrieve Events
```bash
prophet forecast retrieve -o events.json                          # default: sample-sports
prophet forecast retrieve --dataset sample-economics -o events.json
prophet forecast retrieve --dataset sample-resolved --include-resolved -o resolved.json
```

### Event Schema (Exact, from SDK)
```json
{
  "event_ticker": "KXNBAGAME-26MAY15DETCLE",
  "market_ticker": "KXNBAGAME-26MAY15DETCLE",
  "title": "Will Cleveland beat Detroit in NBA Eastern Conference Game 6 on May 15, 2026?",
  "subtitle": null,
  "description": "If Cleveland wins the Game 6...",
  "category": "Sports",
  "rules": "If Cleveland wins the Game 6...",
  "close_time": "2026-05-15T20:00:00Z",
  "outcomes": ["Cleveland", "Detroit"],
  "resolved_outcome": null
}
```

### Field Definitions
| Field | Type | Description |
|---|---|---|
| `event_ticker` | string | Stable event ID (Kalshi-style ticker) |
| `market_ticker` | string | Unique market/question ID (join key for all commands) |
| `title` | string | Human-readable question — safe for LLM prompts |
| `subtitle` | string \| null | Optional qualifier |
| `description` | string | Resolution criterion (same as `rules` in current samples) |
| `category` | string | Top-level topic: `"Sports"`, `"Entertainment"`, `"Economics"`, `"Elections"`, `"Politics"`, etc. |
| `rules` | string | Literal market-resolution criterion — **feed to prompt verbatim** |
| `close_time` | ISO-8601 | UTC deadline for accepting forecasts |
| `outcomes` | string[] | Choice list (2 for binary, 20+ for multi-outcome) |
| `resolved_outcome` | object \| null | `null` for open; `{value: [str], resolved_at: str, source: str}` for resolved |

### Resolved Outcome Format
```json
{
  "resolved_outcome": {
    "value": ["Anna Lena Ebster"],
    "resolved_at": "2026-05-13T17:02:27.064637+00:00",
    "source": "KXITFWMATCH-26MAY12NAJEBS"
  }
}
```
- `value` is **always a list of strings** (even for single outcomes)

### Environment Variables for CLI
| Variable | Default | What it sets |
|---|---|---|
| `PA_SERVER_API_KEY` | **required** | API key for Prophet Arena server (request at prophetarena.co) |
| `PA_SERVER_URL` | `https://api.aiprophet.dev` | Prophet Arena server URL |
| `PA_TEAM_NAME` | set by `register` | Team name (saved to `.env` by CLI) |
| `PA_FORECAST_DATASET` | `sample-sports` | Dataset when `--dataset` omitted |
| `PA_FORECAST_RELEASE` | latest open | Release ID |
| `PA_FORECAST_DATASET_BRANCH` | `main` | Branch for remote fetches |
| `PA_FORECAST_DATASETS_REPO_PATH` | remote | Local clone path for offline |
| `PA_FORECAST_DATASETS_REPO_URL` | GitHub ai-prophet-datasets | Override for forks |

---

## 🆕 SDK Built-in SearchClient

The `ai-prophet` CLI includes a **built-in web search module** (`packages/cli/ai_prophet/search/`):

```python
from ai_prophet.search import SearchClient

search = SearchClient(provider="exa", api_key=os.environ["EXA_API_KEY"])
results = search.search("NBA playoff picture 2026", limit=3)
```

### Search Providers
| Provider | Env Var | Notes |
|---|---|---|
| `exa` | `EXA_API_KEY` | Best for news/events |
| `brave` | `BRAVE_API_KEY` | Good general search |
| `tavily` | `TAVILY_API_KEY` | Optimized for AI agents |
| `perplexity` | `PERPLEXITY_API_KEY` | AI-native search |

### Key Features
- **`as_of` parameter**: Date cutoff for fairness (prevents using future info)
- **Sandbox mode**: Results have `sandbox_status` ("accepted" or rejected)
- **Rejection tracking**: `search.last_rejected`, `search.last_warnings`
- **Source files**: `client.py` (18.9KB), `providers.py` (8.4KB), `sandbox.py` (6.9KB)

⚠️ **This replaces the need for custom retrieval routers** — use the SDK's search client instead of building ESPN/NewsAPI/FRED integrations from scratch.

---

## Trading Track SDK Details (Verified)

### Tick Lifecycle (in order)
| Call | Purpose | Required? |
|---|---|---|
| `session.claim_tick()` | Reserve next tick. Returns `TickLease` | **Yes** |
| `session.load_candidates(lease)` | Fetch market universe + quotes | **Yes** |
| `session.get_portfolio(idx)` | Current cash, equity, positions | Optional |
| `session.put_plan(lease, idx, json)` | Persist audit JSON | Optional |
| `session.submit_intents(lease, idx, intents)` | Submit trades | **Yes** (if trading) |
| `session.finalize(lease, idx)` | Mark tick COMPLETED | **Yes** |
| `session.complete_tick(lease)` | Advance experiment | **Yes** |

### Trading Rules (from `ai_prophet_core.ruleset`)
| Constant | Value |
|---|---|
| `TICK_INTERVAL_SECONDS` | 900 (15 min) |
| `TICK_SUBMISSION_DEADLINE_SECS` | 540 (9 min) |
| `INITIAL_CASH` | $10,000 |
| `MAX_TRADES_PER_TICK` | 20 |
| `MAX_TRADES_PER_DAY` | 100 |
| `MAX_OPEN_POSITIONS` | 30 |
| `MAX_NOTIONAL_PER_MARKET` | $1,000 |
| `MAX_GROSS_EXPOSURE` | $10,000 |
| `FEE_RATE` | 0.0 |

### Execution Semantics
- **BUY YES** fills at `best_ask`. **BUY NO** fills at `1 - best_bid`
- Prices on two sides sum to 1 (prediction-market convention)
- Cannot hold both YES and NO on same market
- SELL down to flat before flipping sides

---

## Prophet Arena Leaderboard (Current)

Top performers (13 models, 7 agents, 4,030 resolved events):

| Rank | Provider | Brier Score | Edge over Market |
|---|---|---|---|
| 1 | Google (Fixed Context) | 0.9131 | +0.0389 |
| 2 | Google (Default Harness) | 0.9291 | +0.0379 |
| 3 | xAI (Fixed Context) | 0.9018 | +0.0294 |
| 4 | Anthropic (Default Harness) | 0.9438 | +0.0274 |
| 5 | OpenAI (Fixed Context) | 0.9134 | +0.0254 |
| 20 | Kalshi Markets (Baseline) | 0.8506 | 0.0000 |

**Key insight**: Even top LLMs only beat market by 1-4%. The edge is razor-thin. Winning requires calibration, not just accuracy.

## Categories of Questions

From sample datasets and Prophet Arena:
- Sports (NBA, MLB, tennis, championships)
- Entertainment (Eurovision, anime awards, Emmys, music charts)
- Economics (CPI, GDP, central bank rates, UST yields)
- Technology
- Geopolitics / Elections / Politics
- Science
- Pop Culture

## Competitor Patterns

- 89 participants registered — likely 20-40 submissions
- First edition of Prophet Hacks (no prior winners)
- Most teams likely using the `example-api` mock endpoint pattern
- Smart teams will use retrieval-augmented approaches with domain-specific evidence
