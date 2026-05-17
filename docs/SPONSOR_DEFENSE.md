# Sibyl — Sponsor Defense Brief

## Why ONLY Prophet Arena?

Sibyl is built **exclusively** for the Prophet Arena evaluation ecosystem. Every component integrates with Prophet Arena's toolchain. Remove Prophet Arena and you'd need to build 5 separate systems from scratch.

## Prophet Arena Touchpoints Used

| # | Feature/Method | What It Does | Code Location |
|---|---|---|---|
| 1 | `prophet forecast retrieve` | Fetches sample datasets (4 event slates: sports, entertainment, economics, resolved) | `scripts/fetch_events.sh` |
| 2 | `prophet forecast register` | **Registers team** permanently with Prophet Arena server (one-time) | CLI setup |
| 3 | `prophet forecast events` | Lists open/closed events from **live server** (requires `PA_SERVER_API_KEY`) | `sibyl/agent.py` |
| 4 | `prophet forecast predict --local` | Runs our agent against events using the standard `predict(event)` contract | `sibyl/agent.py` |
| 5 | `prophet forecast predict --agent-url` | Tests our HTTP `/predict` endpoint via CLI | `sibyl/server.py` |
| 6 | `prophet forecast evaluate` | Scores predictions locally using Brier score formula | `scripts/bench.py` |
| 7 | `prophet forecast submit` | **Submits predictions** to Prophet Arena server for leaderboard | `scripts/submit.sh` |
| 8 | `prophet forecast leaderboard` | Compares our performance against 13 LLM providers + Kalshi baseline | `README.md` benchmarks |
| 9 | `ai-prophet-datasets` | 4 sample datasets (68 total events, 26 resolved) for calibration training | `scripts/calibrate.py` |
| 10 | `ai_prophet_core.forecast.schemas.Prediction` | Dual format: `p_yes` (binary) OR `probabilities` list (multi-outcome) | `sibyl/agent.py` |
| 11 | `ai_prophet.search.SearchClient` | **SDK built-in retrieval** — Exa, Brave, Tavily, Perplexity with sandbox mode | `sibyl/retrieval.py` |
| 12 | OpenAI-compatible `POST /chat/completions` | HTTP endpoint contract — Prophet Arena calls this for auto-evaluation | `sibyl/server.py` |
| 13 | `POST /predict` endpoint | CLI-compatible endpoint — `prophet forecast predict --agent-url` | `sibyl/server.py` |
| 14 | `prophetarena.co/onboarding` | Agent registration — submit endpoint URL, model name, bearer token | Deployment config |
| 15 | `PA_SERVER_API_KEY` + `PA_SERVER_URL` env vars | CLI configuration for server authentication and URL | `.env.example` |

## What We'd Need Without Prophet Arena

Without Prophet Arena's toolchain, we would need:

1. **A custom event ingestion system** — to parse and route forecasting questions (Prophet Arena's `retrieve` + `events` CLI handles this with 4 curated datasets + live server)
2. **A custom evaluation harness** — to score Brier scores against resolved outcomes (Prophet Arena's `evaluate` does this in one command)
3. **A custom leaderboard system** — to compare against baselines (Prophet Arena's `leaderboard` provides rankings across 13 models)
4. **A separate dataset registry** — to host and version forecasting tasks (Prophet Arena's `ai-prophet-datasets` handles versioning with releases)
5. **A custom agent contract standard** — to define how agents receive questions and return probabilities (Prophet Arena's dual endpoint spec standardizes this)
6. **A web search infrastructure** — to gather real-time context (Prophet Arena's `SearchClient` provides sandboxed, date-aware search across 4 providers)
7. **A submission pipeline** — to submit predictions to a scoring server (Prophet Arena's `submit` + `register` CLI handles this)

**Take Prophet Arena out and you'd need 7 separate systems + custom data pipelines + a proprietary evaluation framework.**

## SDK Integration Depth

```
ai-prophet-core (PyPI)
├── ai_prophet_core.forecast.schemas  → Event model, Prediction model (p_yes + probabilities dual format)
├── ai_prophet_core.ServerAPIClient   → Typed HTTP client (Trading track)
├── ai_prophet_core.arena             → BenchmarkSession lifecycle
└── ai_prophet_core.ruleset           → Trading constants

ai-prophet (PyPI, CLI: prophet)
├── prophet forecast register         → Team registration (one-time)
├── prophet forecast retrieve         → Dataset fetching
├── prophet forecast events           → Live server event listing
├── prophet forecast predict          → Agent invocation (--local or --agent-url)
├── prophet forecast submit           → Prediction submission
├── prophet forecast evaluate         → Brier scoring
└── prophet forecast leaderboard      → Performance comparison

ai_prophet.search (SDK built-in)
├── SearchClient                      → Unified search (Exa, Brave, Tavily, Perplexity)
├── sandbox_status                    → Result filtering for fairness
└── as_of parameter                   → Date-aware search cutoff
```

## Honest Limitations

1. **26 resolved events for calibration** — Small training set for Platt scaling. May need to supplement with synthetic data or use simpler calibration.
2. **10-minute response window per batch** — For complex questions requiring extensive web research, this may be tight if the batch is large.
3. **SearchClient sandbox** — SDK's sandboxed search may reject some results; fallback to LLM-only if too aggressive.

## Conclusion

Sibyl doesn't just USE Prophet Arena — it's BUILT FOR Prophet Arena. The entire pipeline, from team registration (`register`) to event ingestion (`retrieve` + `events`) to retrieval (`SearchClient`) to local benchmarking (`evaluate`) to submission (`submit`) to production deployment (dual endpoints → `prophetarena.co/onboarding`), runs on Prophet Arena's CLI, SDK, and data infrastructure. We leverage **15 integration points** across 3 SDK packages. The agent exists because this evaluation framework exists.
