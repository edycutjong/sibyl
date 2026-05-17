# Prophet Hacks — Project Ideas

> **Hackathon**: Prophet Hacks (AI Forecasting Hackathon)
> **Track**: Forecasting (primary) — pure Brier score performance
> **Format**: No subjective judging — agent performance only

## Recommended: Idea #1 — OracleChain

### Overview
| Field | Value |
|---|---|
| **Name** | OracleChain |
| **One-Line Pitch** | Multi-source retrieval-augmented forecasting agent that anchors on market prices and adjusts with real-time evidence from news, statistics, and polling data — routing each question category to a specialized reasoning pipeline |
| **Target Track** | Forecasting Track |
| **Difficulty** | Medium |
| **Estimated Cost** | $15–40 for 2-week eval (tiered model routing) |

### Why It Wins
1. **Market anchoring** — Uses Kalshi/Polymarket prices as Bayesian prior instead of predicting from scratch (most teams will ignore available market data)
2. **Category-specific retrieval** — Sports → stats APIs (ESPN, odds), Geopolitics → news APIs (NewsAPI, Google News), Economics → FRED/BLS data, Science → arXiv/Google Scholar
3. **Ensemble calibration** — Averages 2-3 model outputs per question, then applies Platt scaling calibration learned from historical Prophet Arena data
4. **Cost-tiered execution** — Uses GPT-4o-mini for high-confidence questions (market > 85% or < 15%), Gemini 2.5 Flash for medium confidence, Claude Opus only for close calls
5. **100% completion** — Answers every question (completion_rate = 1.0), falling back to market price ± small adjustment when retrieval fails

### Architecture
```
Event Received
  → Category Classifier (GPT-4o-mini, 1-shot)
  → Market Price Lookup (if available)
  → Category Router:
      ├── Sports → ESPN API + historical stats + odds aggregator
      ├── Geopolitics → News API + Wikipedia + polling data
      ├── Economics → FRED API + BLS + recent earnings
      ├── Science/Tech → Google Scholar + arXiv + tech news
      └── Pop Culture → Google Trends + social media signals
  → Context Assembly (relevant snippets, max 4000 tokens)
  → LLM Reasoning (model selected by confidence tier)
  → Probability Extraction + Normalization
  → Ensemble (if budget allows: 2 models, averaged)
  → Platt Scaling Calibration
  → Output Probabilities
```

### Emotional Hook
"A trader stares at a Kalshi contract for 'Will the Fed raise rates in June?' priced at 42 cents. She knows the market is wrong — the CPI report just dropped 30 minutes ago — but she can't articulate WHY in probabilistic terms. OracleChain can."

### Gate Checks
- ✅ Emotional Hook: Specific person, specific crisis
- ✅ Docs Distance: 🟢 Novel — the example agent is a bare Claude call with no retrieval
- ✅ Winner Archetype: Capability-unlock ("markets can now be systematically beaten by retrieval-augmented AI")
- ✅ Scope: Narrow+Deep (ONE pipeline: retrieve → reason → calibrate)
- ✅ Rubric Alignment: 100% (only criterion is Brier score performance)

### Risk
- External API rate limits during 2-week eval
- Market prices not available for all questions
- Calibration overfitting on historical data
- **Mitigation**: Graceful fallback to uncalibrated LLM prediction; cache API responses; use conservative calibration

---

## Alternative: Idea #2 — Consilience

### Overview
| Field | Value |
|---|---|
| **Name** | Consilience |
| **One-Line Pitch** | Ensemble-of-experts agent that queries 3 different LLMs with 3 different prompting strategies and aggregates via learned calibration weights |
| **Target Track** | Forecasting Track |
| **Difficulty** | Easy-Medium |
| **Estimated Cost** | $25–60 for 2-week eval |

### Why It Wins
- **Diversity reduces variance** — averaging Claude + Gemini + GPT produces more calibrated outputs than any single model
- **Multiple reasoning modes** — each model gets a different prompt: one analytical, one contrarian, one base-rate-focused
- **Simple but effective** — easier to build than full retrieval pipeline, still beats single-model approaches
- **Calibration overlay** — learns weights from Prophet Arena historical data

### Risk
- Higher cost (3× API calls per question)
- May not outperform a single well-tuned retrieval-augmented model
- Less differentiated in README/writeup

---

## Alternative: Idea #3 — Bayesian Anchor

### Overview
| Field | Value |
|---|---|
| **Name** | Bayesian Anchor |
| **One-Line Pitch** | Minimalist agent that treats Kalshi market prices as a strong prior and only adjusts when it finds compelling new evidence — optimizing for cost-efficiency over 2 weeks |
| **Target Track** | Forecasting Track |
| **Difficulty** | Easy |
| **Estimated Cost** | $5–15 for 2-week eval |

### Why It Wins
- **Markets are already good** — Kalshi aggregates thousands of traders. Starting from their price is smarter than predicting from scratch
- **Ultra-low cost** — only calls expensive LLMs when evidence suggests the market is wrong
- **High completion rate** — can answer 100% of questions instantly (default: market price)
- **Honest strategy** — acknowledges that beating the market is hard; focuses on the few questions where edge exists

### Risk
- May produce too-small edge over market to win
- Requires access to Kalshi prices for each question (may not be available in dataset)
- Feels "too simple" for hackathon writeup

---

## Recommendation

**Idea #1 (OracleChain)** is the clear winner because:
1. It combines the best elements of all three approaches (market anchoring + retrieval + ensemble + calibration)
2. It has the richest architecture story for the README/writeup
3. It directly addresses what the leaderboard shows: information retrieval strategy matters most
4. Cost-tiered execution keeps 2-week costs manageable
5. 100% completion rate strategy maximizes the scoring formula

**Proceed with OracleChain for the Forecasting Track.**
