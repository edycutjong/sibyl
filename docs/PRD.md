# OracleChain — Product Requirements Document

> **Emotional Hook**: A trader stares at a Kalshi contract for "Will the Fed raise rates in June?" priced at 42 cents. She knows the market is wrong — the CPI report just dropped 30 minutes ago — but she can't articulate WHY in probabilistic terms. OracleChain can.

## Problem Statement

Current AI forecasting agents treat every question the same — they receive text, call an LLM, and return a probability. This ignores two critical realities:
1. **Prediction markets already encode massive information** — Kalshi prices aggregate thousands of informed traders. Starting from scratch throws away this intelligence.
2. **Different question categories need different evidence** — Sports outcomes need historical stats, geopolitical events need breaking news, economic questions need indicator data. A one-size-fits-all prompt wastes tokens and misses domain-specific signals.

The result: most agents perform AT or BELOW market baseline, despite using frontier LLMs that cost $0.01+ per question.

## Solution Overview

OracleChain is a **retrieval-augmented forecasting agent** that:
1. **Exposes** an OpenAI-compatible `/chat/completions` endpoint (Prophet Arena evaluation contract)
2. **Anchors** on available market prices as Bayesian priors
3. **Routes** each question to a category-specific retrieval pipeline
4. **Reasons** with context-rich LLM calls using domain evidence
5. **Calibrates** output probabilities using post-hoc calibration (Platt scaling)
6. **Tiers** model selection by question difficulty to control 2-week API costs

## Target Users

- Prophet Arena evaluation harness (primary consumer — calls `/chat/completions`)
- `prophet forecast predict --local` CLI (local benchmarking via `predict(event)`)
- Hackathon judges reviewing architecture and approach

## Core Features (MVP — 32h Build)

### 1. OpenAI-Compatible Server
- **POST /chat/completions** — receives chat request with event in prompt, returns prediction as chat response
- Follows exact OpenAI schema: `id`, `object`, `created`, `model`, `choices[].message.content`, `usage`
- Bearer token authentication (configurable)
- Onboard at `prophetarena.co/onboarding`

### 2. Category Classifier
- Classifies each incoming event into: Sports, Geopolitics, Economics, Science/Tech, Pop Culture, Other
- Uses GPT-4o-mini with few-shot examples (fast, cheap)
- Fallback: keyword-based heuristic if API fails

### 3. Market Price Anchor
- Attempts to look up current market price for the event (Kalshi, Polymarket, Metaculus)
- If found: uses as prior probability
- If not found: starts with base rate (uniform distribution)

### 4. Category-Specific Retrieval
| Category | Sources | Key Data |
|---|---|---|
| Sports | ESPN API, odds aggregators | Historical matchup data, current odds, injuries |
| Geopolitics | NewsAPI, Google News RSS | Recent headlines, expert analysis |
| Economics | FRED API, BLS | Economic indicators, recent data releases |
| Science/Tech | Google Scholar, arXiv, tech blogs | Research trends, company announcements |
| Pop Culture | Google Trends, social media | Trending topics, sentiment |

### 5. Context-Rich LLM Reasoning
- Assembles retrieved context (max 4,000 tokens per question)
- Structured prompt: "Given this evidence and market price, estimate probability for each outcome"
- Extracts probability via structured output (JSON mode)
- Returns probabilities as dict `{"Outcome A": 0.68, "Outcome B": 0.32}` plus rationale

### 6. Cost-Tiered Model Selection
| Confidence Level | Model | Cost |
|---|---|---|
| High (market > 85% or < 15%) | GPT-4o-mini | ~$0.0001/question |
| Medium (market 15-85%) | Gemini 2.5 Flash | ~$0.001/question |
| Low (market 40-60%, complex) | Claude Sonnet 4 | ~$0.005/question |

### 7. Calibration Layer
- Post-hoc Platt scaling trained on `sample-resolved` dataset (26 resolved events)
- Corrects systematic LLM over/under-confidence
- Falls back to raw probabilities if calibration worsens performance

## User Stories

1. As the Prophet Arena harness, I call `/chat/completions` with an event prompt and receive a valid OpenAI chat response with calibrated probabilities within 30 seconds
2. As the eval system, I can query the agent endpoint continuously for 2 weeks without downtime
3. As the agent operator, I can monitor API costs and adjust model tier thresholds via `/stats`
4. As the developer, I can run `prophet forecast predict --local oraclechain.agent` for local benchmarking

## Success Metrics

| Metric | Target |
|---|---|
| Brier score edge over market | > +0.01 (even small edge counts) |
| Completion rate | 100% (answer every question) |
| Total API cost (2-week eval) | < $40 |
| Response latency (p95) | < 30 seconds |
| Uptime during eval window | > 99% |

## Out of Scope

- Trading Track integration (focus on Forecasting only)
- Custom model fine-tuning (time-prohibitive for 32h build)
- Frontend dashboard (no UI needed for this competition)
- Real-money trading or mainnet deployment
- Mobile or browser interface

## Scope Constraint

**ONE core flow**: `Chat Request → Parse Event → Classify → Retrieve → Reason → Calibrate → Chat Response`

This single pipeline with extreme depth (category-specific retrieval, model tiering, calibration) rather than multiple features.
