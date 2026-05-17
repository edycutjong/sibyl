# Prophet Hacks — Winner Analysis

## First Edition — No Prior Winners

Prophet Hacks 2026 is the **first edition** of this hackathon. There are no prior winners to analyze from this specific event.

## Proxy Analysis: Prophet Arena Leaderboard

Since this hackathon is scored by the Prophet Arena benchmark, the existing leaderboard IS the winner analysis. The top-performing systems reveal what works.

### Leaderboard Patterns (13 models, 7 agents, 4,030 resolved events)

| Dimension | What the Leaderboard Shows |
|---|---|
| **Top performers** | Google models dominate (#1, #2), followed by xAI (#3) and Anthropic (#4) |
| **Edge over market** | Best edge is only +0.0389 (Google). Most models cluster around +0.01 to +0.03 |
| **Harness type matters** | "Fixed Context" and "Default Harness" produce different results for the same provider |
| **Calibration (ECE)** | Best calibrated: OpenAI (0.0199–0.0233 ECE). Worst: Meta (0.0967) |
| **Completion rate** | More events evaluated = more data. xAI leads with 7,252 events resolved |
| **Baseline** | Kalshi Markets (rank 20): Brier 0.8506, Edge 0.0000 — this is the floor to beat |
| **Below baseline** | Qwen actually performs BELOW market (-0.0055 edge) — it's possible to lose |

### Key Insights for Winning

1. **Beating the market is HARD.** Even frontier LLMs only edge out prediction market prices by 1-4%. The market (Kalshi) aggregates thousands of informed traders — it's a strong baseline.

2. **Calibration > Accuracy.** Having a high Brier score (close to 1) matters, but the actual scoring formula weights edge over market × completion rate. A well-calibrated model that answers MORE questions beats a slightly better model that answers fewer.

3. **Model selection is table stakes.** Everyone has access to GPT-4o, Claude, Gemini. The differentiator is the **agent architecture**: how you gather context, what sources you consult, how you calibrate probabilities.

4. **"Fixed Context" vs "Default Harness"** suggests that information retrieval strategy matters enormously. Models with richer, more relevant context outperform.

5. **Cost-awareness is critical.** Your agent runs for 2 weeks on YOUR API keys. A naive approach querying GPT-4o with max tokens for every question will cost hundreds of dollars.

## Proxy Analysis: Forecasting Competition Winners (General)

From the broader superforecasting community (Good Judgment Project, Metaculus, etc.):

| Dimension | Winning Pattern |
|---|---|
| **Emotional framing** | N/A — pure performance, no narrative needed |
| **Winner archetype** | Capability-unlock (better predictions than markets) |
| **Deployment level** | Live endpoint, production-grade reliability |
| **SDK integration depth** | Deep integration with `ai-prophet` CLI and evaluation harness |
| **Model selection** | NOT one-model-fits-all; ensemble or category-specific routing |
| **Scope pattern** | Narrow+Deep: ONE excellent forecasting pipeline > many mediocre features |
| **Benchmark artifacts** | Reproducible Brier scores with `prophet forecast evaluate` |
| **Honesty signals** | Calibration curves, acknowledging uncertainty ranges |

## What Will 80% of Teams Build?

1. **Wrap the example agent** — Call Claude/GPT with the question text, parse probability, submit. This is the `ai_prophet.forecast.example_agent` pattern.
2. **Simple prompt engineering** — Add system prompts like "You are a superforecaster" with no additional context.
3. **Single-model approach** — One LLM for all question categories.

## What Would Beat Them?

1. **Multi-source context retrieval** — Scrape relevant news, polls, betting odds, statistics before each prediction
2. **Category-aware routing** — Use different strategies for Sports (historical stats) vs Geopolitics (news analysis) vs Economics (indicator data)
3. **Ensemble/calibration layer** — Average multiple model outputs and apply post-hoc calibration (Platt scaling, isotonic regression)
4. **Cost-efficient architecture** — Use cheap models for easy questions (high-confidence markets), expensive models only for edge cases
5. **Market price anchoring** — Start with the Kalshi market price and adjust rather than predicting from scratch
