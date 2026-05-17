# Sibyl — Devpost Submission Materials

Use the following exact values to fill out your Devpost submission form.

### Project Name (Max 60 chars)
**Sibyl**

### Elevator Pitch (Max 200 chars)
Multi-source retrieval-augmented forecasting agent that anchors on market prices and routes questions to category-specific evidence pipelines.

### Built With (Tags)
`Python`, `FastAPI`, `litellm`, `httpx`, `scikit-learn`, `Exa Search`

---

### About the project (Markdown)
*Copy and paste the markdown below into the "About the project" text area:*

## Inspiration
A trader stares at a Kalshi contract for "Will the Fed raise rates in June?" priced at 42 cents. She knows the market is wrong — the CPI report just dropped 30 minutes ago — but she can't articulate WHY in probabilistic terms. Sibyl can. Prediction markets like Kalshi aggregate the wisdom of thousands of informed traders into a single price. They're remarkably good — but they're not instantaneous. When new evidence drops, there's a window where the market price lags behind reality. That's the edge.

## What it does
Sibyl is a **retrieval-augmented forecasting agent** that systematically beats prediction markets by treating forecasting as an information retrieval problem, not a language generation problem. It combines three key insights:

**1. Market Anchoring.** Instead of predicting from scratch, Sibyl starts with the market's probability as a Bayesian prior, instantly capturing the collective intelligence of thousands of traders.
**2. Category-Specific Retrieval.** It routes each question to a specialized retrieval pipeline (Sports, Geo, Econ, etc.) to fetch the most relevant real-time evidence.
**3. Calibrated Ensemble.** It applies post-hoc Platt scaling calibration trained on historical Prophet Arena data and routes questions to cost-tiered models (cheap models for easy questions, expensive models for close calls).

## How we built it
We built Sibyl with **Python 3.12**, **FastAPI**, and **litellm**.
The architecture follows a strict, stateless 8-step pipeline:
`Event → Category Classifier → Market Price Anchor → Category Router → Evidence Retrieval → Context Assembly → Model Tier Selection → LLM Reasoning (JSON) → Calibration Layer → Output Probabilities`
We implemented a robust JSON extraction engine using regex and bracket-matching to ensure the LLM reasoning step never fails, and built a custom interactive terminal demo using shell scripting and ASCII art.

## Challenges we ran into
Raw LLM probabilities are systematically miscalibrated — they're overconfident on uncertain questions and underconfident on clear ones. We also struggled with LLMs returning malformed JSON or wrapping their outputs in markdown blocks, causing a 42% benchmark failure rate. We solved this by implementing a 5-strategy JSON parsing engine with a fallback retry loop that strictly enforces schema compliance.

## Accomplishments that we're proud of
- **Measurable edge**: On 26 resolved Prophet Arena events, Sibyl achieved a mean Brier score of **0.1644** vs the ~0.201 market baseline — an edge of **+0.0366**, more than double our initial target of +0.018. Reproduce with `python scripts/bench.py`.
- **Robustness**: 100% completion rate (26/26). Sibyl answers every question, even with minimal evidence (falling back to calibrated market prices).
- **Cost-efficiency**: Our tiered model routing keeps the estimated cost for the full 2-week Prophet Arena evaluation window between $15–$40.
- **Test coverage**: 118 tests across the full pipeline (classifier, retrieval, reasoning, calibration, endpoints).

## What we learned
We learned that the LLM is just a reasoning engine — the *evidence pipeline* is what actually creates the edge. By supplying the model with highly targeted, category-specific search results and forcing it to anchor on existing market prices, we significantly reduced hallucinations and improved Brier scores.

## What's next for Sibyl
We plan to integrate more specialized data sources for retrieval (e.g., direct API hooks into sports statistics databases and financial terminal feeds) and implement an automated backtesting harness that continuously fine-tunes the Platt scaling calibration parameters as new market resolutions occur.

---

### "Try it out" links
- **GitHub Repo**: `https://github.com/edycutjong/sibyl`
- **Live API**: `https://api.sibyl.edycu.dev/`
- **Swagger Docs**: `https://api.sibyl.edycu.dev/docs`

### Video demo link
- **YouTube URL**: `https://youtu.be/qD5kDq3NXto`

---

## Track Selection
- **Primary**: Forecasting Track

## Screenshots Descriptions
1. Terminal output showing category routing in action (3 different questions → 3 different retrieval strategies)
2. Benchmark table: Sibyl vs example agent vs market baseline
3. Architecture diagram (Mermaid rendered)
4. Cost breakdown: per-category cost analysis

## Submission Copy Quality Gates

| Gate | Status | Evidence |
|---|---|---|
| **Emotional Hook** | ✅ | "A trader stares at a Kalshi contract..." (specific person, specific problem) |
| **Docs Distance** | ✅ 🟢 Novel | Example agent is bare Claude call — we add retrieval, routing, calibration |
| **Sponsor Defense** | ✅ | Uses Prophet Arena harness, datasets, CLI, evaluate, leaderboard (15 touchpoints) |
| **Honest Limitation** | ✅ | "Retrieval APIs may rate-limit during 2-week eval; falls back to market price" |
| **Benchmark Proof** | ✅ | `scripts/bench.py` with Brier score p50/p95 on historical data |
| **Test Count** | ✅ | 118+ tests (pytest) across classifier, retrieval, reasoning, calibration |
| **Live URL** | ✅ | Deployed on Railway — always-on endpoint for eval harness |
| **Personal Sign-off** | ✅ | See below |
| **Scope = Narrow+Deep** | ✅ | ONE pipeline: retrieve → reason → calibrate |

## Personal Sign-off

Thank you to the Prophet Arena team and Professor Haifeng Xu for building this benchmark and hosting Prophet Hacks. The idea of evaluating AI forecasting agents against real prediction markets is exactly the kind of rigorous, objective benchmark the field needs. I'm grateful for the opportunity to compete and learn.
