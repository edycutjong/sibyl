# 🧠 Prophet Hacks — Ideation Prompt

> Paste this into Gemini Deep Think, o3, or any deep reasoning model.

---

You are a hackathon strategist with a 90%+ win rate. Your job is to analyze Prophet Hacks and generate 5 non-obvious, high-winability agent architectures for the **Forecasting Track**.

## Hackathon Context

- **Name**: Prophet Hacks (AI Forecasting Hackathon)
- **Platform**: Devpost
- **Organizer**: Prophet Arena Team (SIGMA Lab, University of Chicago, powered by Kalshi)
- **Theme**: Build AI agents that predict the future — probabilistic forecasting on real-world events
- **Duration**: 32 hours build window + 2-week evaluation

### Tracks
1. **Forecasting Track** — Agent receives questions about real-world events (sports, geopolitics, economics, science, tech), returns calibrated probability predictions. Scored by Brier score edge over Kalshi market prices. Formula: `(team_avg_Brier − market_avg_Brier) × completion_rate`. Must be > 0 to win.
2. **Trading Track** — Agent takes positions on prediction markets via SDK harness. Scored by PnL + Sharpe ratio. Must be positive PnL with ≥14 trades.

### Key Differences from Normal Hackathons
- **No subjective judging** — pure algorithmic performance over 2-week eval window
- **No UI/demo needed** — your code IS the product
- **API costs on you** — agent runs for 2 weeks on your keys
- **Must beat the market** — Kalshi prices are the baseline (aggregated human intelligence)

### Judging: Performance Metrics Only
- Forecasting: Brier score edge over market × completion rate
- Trading: Combined rank across PnL + Sharpe ratio
- No innovation, design, or presentation criteria

### SDK
- `prophet forecast retrieve` — fetch event slates from `ai-prophet-datasets`
- `prophet forecast predict --local my_agent` — run agent locally
- `prophet forecast evaluate` — score locally with Brier
- Agent contract: `predict(event) -> {"probabilities": [{"market": "X", "probability": 0.68}]}`
- 10-minute response window per batch; 30s default timeout per event

### Event Format
```json
{"event_ticker": "task-001", "title": "Who will win: Pittsburgh or Atlanta?",
 "category": "Sports", "outcomes": ["Pittsburgh", "Atlanta"],
 "close_time": "2026-03-21T23:59:59Z"}
```

Categories: Sports, Technology, Economics, Geopolitics, Science, Pop Culture

### Submission Requirements
- Devpost project page with architecture description
- Public GitHub repo with README + run script
- Agent package exposing OpenAI-compatible HTTP endpoint (Forecasting Track)

### Current Leaderboard (top 5 of 20)
1. Google (Fixed Context): Brier 0.9131, Edge +0.0389
2. Google (Default Harness): Brier 0.9291, Edge +0.0379
3. xAI (Fixed Context): Brier 0.9018, Edge +0.0294
4. Anthropic (Default Harness): Brier 0.9438, Edge +0.0274
5. OpenAI (Fixed Context): Brier 0.9134, Edge +0.0254
- Kalshi Markets (Baseline): Brier 0.8506, Edge 0.0000

- **Submission Count**: ~89 participants, ~4 prize slots (2 per track)
- **Prizes**: 1st = trip to South Korea ($2,000) for ICML workshop; 2nd = $500

## My Profile

- Solo developer
- Strong in: Python, Next.js, React, Node.js, Supabase, AI/ML APIs
- Can ship a polished agent within 32 hours
- Deep experience with LLM APIs (OpenAI, Anthropic, Google)

## Your Task

Generate **5 forecasting agent architectures** ranked by winnability. For each:

1. **Name** — catchy codename
2. **One-Line Pitch** — what makes this agent different
3. **Target Track** — Forecasting (primary focus)
4. **Why It Wins** — what edge does this have over "just call GPT"
5. **Secret Angle** — non-obvious insight most teams will miss
6. **Architecture** — specific pipeline steps (retrieval → reasoning → calibration)
7. **30-Second Demo** — what the README shows to prove it works
8. **Risk** — what could go wrong
9. **Difficulty** — Easy / Medium / Hard
10. **Cost Estimate** — estimated API cost for 2-week eval window
11. **Calibration Strategy** — how probabilities are calibrated post-hoc
12. **Information Sources** — what external data the agent retrieves per question
13. **Category Routing** — does the agent handle Sports differently from Geopolitics?
14. **Market Anchoring** — does the agent use Kalshi prices as a prior?
15. **Completion Strategy** — how does it maximize completion_rate without sacrificing quality?

## Thinking Framework

### What Beats the Market?
- The market (Kalshi) aggregates thousands of informed human traders
- Even frontier LLMs only beat it by 1-4% (see leaderboard)
- Edge comes from: better information retrieval, better calibration, more consistent coverage
- The formula rewards BOTH edge AND completion — answer everything, even with small edge

### What Will 80% of Teams Build?
- Wrap Claude/GPT with "You are a superforecaster" system prompt
- No external data retrieval
- Single model for all categories
- No calibration layer
- This approach will likely perform AT or BELOW market baseline

### Anti-Patterns
- **One-Model-Fits-All**: Sports questions need stats, geopolitics needs news — different tools
- **Ignoring the Market**: Kalshi prices encode massive information — use them as prior, not ignore them
- **Over-spending on Tokens**: 2 weeks × hundreds of questions × GPT-4o = $$$. Use cheap models where edge is low
- **Perfect Accuracy Trap**: Completion rate matters. Answering 100% of questions with +0.01 edge beats answering 50% with +0.03 edge
- **No Calibration**: Raw LLM probabilities are systematically miscalibrated. Post-hoc calibration is free accuracy

### Winning Architecture Principles
1. **Retrieve → Reason → Calibrate** pipeline (not just prompt-and-pray)
2. **Category-specific strategies** (sports stats API, news API, economic indicators)
3. **Market price anchoring** (Kalshi price as Bayesian prior, then adjust)
4. **Ensemble** (average 2-3 models, reduces variance)
5. **Cost tiering** (cheap model for easy Qs, expensive model for close calls)
6. **Post-hoc calibration** (Platt scaling on historical predictions)
7. **High completion rate** (answer everything — even 50.1% edge counts)

## Output Format

Rank ideas from highest to lowest winnability. Be specific about the pipeline architecture. Every idea must have a clear path to beating the Kalshi market baseline. Focus on the Forecasting Track (more accessible for solo dev without trading infrastructure).
